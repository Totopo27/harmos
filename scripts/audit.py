#!/usr/bin/env python3
"""
Harmos Live Runtime Verifier & Auditor.
Automatiza la verificacion en vivo de parches y packages en Cycling '74 Max.

Contrato Operativo (Hard Rules):
1. Deteccion de runtime Max (Registro de Windows / rutas estandar / MAX_PATH).
2. Si Max no esta disponible, el veredicto es estrictamente BLOCKED (no PASS).
3. Si Max esta disponible:
   - Aislamiento por sesion de log: Max trunca Max.log en cada arranque, por lo que
     la lectura se ancla al header de sesion y no a offsets de bytes.
   - Ejecucion de Max.exe con el patcher objetivo.
   - Espera event-driven hasta fin de carga (startup_load), con timeout acotado.
   - Parsing estricto de la sesion de Max.log: nivel `error` o patrones criticos.
   - Fail-closed: sin sesion propia o sin carga completada el veredicto es BLOCKED.
   - Generacion de evidencia / receipt verificable.
   - Procedencia: si el paquete incluye `emitted-from.json` junto al patcher, se
     verifica antes de arrancar Max; un veredicto distinto de VALID impide PASS.
"""
import sys
import os
import re
import time
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict

# El script se ejecuta como `python scripts/audit.py`: la raiz del repo debe estar
# en sys.path para importar el motor de procedencia.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.compiler.provenance import verify_provenance

# Formato canonico de linea de Max.log:  [YYYY-MM-DD HH:MM:SS.ffffff level] [pid] mensaje
LOG_LINE_RE = re.compile(
    r"^\[(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)\s+"
    r"(?P<level>[A-Za-z]+)\] \[(?P<pid>\d+)\] (?P<message>.*)$"
)

# Marcadores de sesion emitidos por Max 9.
SESSION_HEADER_MARKER = "max logging initialized"
STARTUP_COMPLETE_MARKER = "<- startup_load(max-startup)"
CRASH_RECOVERY_MARKER = "looks like prior Max run crashed"

# Niveles de log que constituyen fallo (cero tolerancia).
FAIL_LEVELS = ("error", "fatal", "critical")

# Patrones de mensaje que representan contratos rotos. No incluye "error:"/"fatal:"
# porque el nivel ya se evalua estructuralmente y "crash" porque la recuperacion de
# sesion previa de Max usa esa palabra en lineas informativas.
FAIL_PATTERNS = [
    "doesn't match type",
    "no such object",
    "no patcher ",
    "can't connect",
    "connecting to comment",
    "access violation",
    "0xc0000005",
]

# Tolerancia de reloj y margen para capturar lineas posteriores al fin de carga.
SESSION_CLOCK_TOLERANCE_SECONDS = 2.0
SETTLE_SECONDS = 1.0
POLL_INTERVAL_SECONDS = 0.25
DEFAULT_TIMEOUT_SECONDS = 60

# Huella de procedencia emitida por el compilador junto al paquete.
PROVENANCE_RECORD_NAME = "emitted-from.json"

# Veredictos de procedencia que impiden emitir PASS: el paquete no corresponde a
# los insumos con los que fue emitido, o la evidencia no es verificable.
PROVENANCE_BLOCKING_VERDICTS = (
    "STALE_CONTRACTS",
    "STALE_IR",
    "STALE_SOURCE",
    "STALE_ARTIFACTS",
    "UNVERIFIABLE",
    "INVALID",
)


def audit_provenance(patcher_path: Path) -> Tuple[Optional[str], List[str]]:
    """
    Certifica la procedencia del paquete que contiene el patcher.

    Devuelve (veredicto, detalles), o (None, []) cuando no existe
    `emitted-from.json` junto al patcher: un paquete sin huella no es un fallo,
    simplemente no hay procedencia que certificar.
    """
    record = patcher_path.parent / PROVENANCE_RECORD_NAME
    if not record.is_file():
        return None, []

    try:
        return verify_provenance(record)
    except Exception as e:
        return "UNVERIFIABLE", [
            f"Error al verificar la procedencia: {e}",
            "Sin evidencia legible no se certifica el paquete.",
        ]


def resolve_max_executable() -> Optional[Path]:
    """Resuelve la ruta a Max.exe via variable de entorno, Registro o rutas conocidas."""
    env_path = os.environ.get("MAX_PATH")
    if env_path and Path(env_path).is_file():
        return Path(env_path)

    # Busqueda en registro de Windows
    if sys.platform == "win32":
        try:
            import winreg
            for root_key in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                for sub in [r"SOFTWARE\Cycling '74\Max 9", r"SOFTWARE\Cycling '74\Max 8"]:
                    try:
                        with winreg.OpenKey(root_key, sub) as key:
                            loc, _ = winreg.QueryValueEx(key, "Installed Location")
                            exe = Path(loc) / "Max.exe"
                            if exe.is_file():
                                return exe
                    except OSError:
                        continue
        except Exception:
            pass

    # Rutas por defecto en Windows: se recorren los directorios de programa
    # declarados por el entorno y las unidades fijas del host. El codigo nunca
    # codifica rutas absolutas de host.
    roots = []
    for env_name in ("ProgramW6432", "ProgramFiles", "ProgramFiles(x86)"):
        root = os.environ.get(env_name)
        if root and root not in roots:
            roots.append(root)
    if sys.platform == "win32":
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            candidate_root = f"{letter}:\\Program Files"
            if candidate_root not in roots and Path(candidate_root).is_dir():
                roots.append(candidate_root)

    candidates = []
    for root in roots:
        for version in ("Max 9", "Max 8"):
            candidate = Path(root) / "Cycling '74" / version / "Max.exe"
            if candidate not in candidates:
                candidates.append(candidate)
    for c in candidates:
        if c.is_file():
            return c

    return None


def resolve_max_log_path(max_exe: Optional[Path] = None) -> Optional[Path]:
    """
    Localiza el archivo Max.log dentro de la carpeta de usuario de Max.

    En Max 9 la ruta canonica es <APPDATA>/Cycling '74/Max 9/Logs/Max.log.
    Si se suministra max_exe se prioriza la carpeta de la version detectada y,
    cuando hay varias instalaciones, se elige de forma deterministica (ordenada).
    """
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None

    base = Path(appdata) / "Cycling '74"
    if not base.exists():
        return None

    wants = None
    if max_exe:
        exe_str = str(max_exe).lower()
        if "max 9" in exe_str:
            wants = "max 9"
        elif "max 8" in exe_str:
            wants = "max 8"

    candidates = sorted(
        (p for p in base.glob("*/Logs/Max.log") if p.is_file()),
        key=lambda p: str(p).lower(),
    )
    if not candidates:
        return None

    if wants:
        for candidate in candidates:
            if wants in str(candidate.parent.parent).lower():
                return candidate

    return candidates[0]


def parse_log_line(line: str) -> Optional[Dict[str, str]]:
    """Parsea una linea canonica de Max.log en sus campos; None si no la cumple."""
    match = LOG_LINE_RE.match(line.strip())
    if not match:
        return None
    return match.groupdict()


def _parse_log_timestamp(raw_timestamp: str) -> Optional[float]:
    """Convierte el timestamp local de Max.log a epoch segundos."""
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw_timestamp, fmt).timestamp()
        except ValueError:
            continue
    return None


def load_session_lines(max_log: Optional[Path], launched_after: float) -> Optional[List[str]]:
    """
    Devuelve las lineas de la sesion de log iniciada por este arranque de Max.

    Max trunca Max.log en cada arranque, asi que un offset de bytes previo queda
    invalido y un marcador escrito antes del launch se pierde. El aislamiento se
    realiza con el header de sesion mas el mtime del archivo:
    - se toma el ultimo header de sesion del archivo;
    - se exige que el archivo se haya escrito despues del launch;
    - se lee desde ese header hasta el final.
    Devuelve None cuando no hay sesion atribuible a esta corrida (fail-closed).
    """
    if not max_log or not max_log.is_file():
        return None

    try:
        stat = max_log.stat()
        raw = max_log.read_bytes()
    except OSError:
        return None

    if stat.st_mtime < (launched_after - SESSION_CLOCK_TOLERANCE_SECONDS):
        return None

    lines = raw.decode("utf-8", errors="replace").splitlines()

    header_index = None
    for index in range(len(lines) - 1, -1, -1):
        if SESSION_HEADER_MARKER in lines[index].lower():
            header_index = index
            break
    if header_index is None:
        return None

    header = parse_log_line(lines[header_index])
    if header is None:
        return None
    started_at = _parse_log_timestamp(header["timestamp"])
    if started_at is None:
        return None
    if started_at < (launched_after - SESSION_CLOCK_TOLERANCE_SECONDS):
        return None

    session = [line.strip() for line in lines[header_index:] if line.strip()]
    return session or None


def evaluate_session(lines: List[str]) -> Tuple[str, List[str]]:
    """
    Evalua la sesion de log y devuelve (veredicto, detalle).

    Fail-closed: una sesion vacia o sin fin de carga nunca produce PASS, porque
    no constituye evidencia de que el patcher se haya cargado sin errores.
    """
    if not lines:
        return "BLOCKED", ["Sesion de log vacia: no hay evidencia de ejecucion."]

    detected_errors = []
    for line in lines:
        parsed = parse_log_line(line)
        level = parsed["level"].lower() if parsed else ""
        lowered = line.lower()
        if level in FAIL_LEVELS or any(pattern in lowered for pattern in FAIL_PATTERNS):
            detected_errors.append(line)

    if detected_errors:
        return "FAIL", detected_errors

    if not any(STARTUP_COMPLETE_MARKER in line for line in lines):
        return "BLOCKED", [
            "Max no completo la fase de carga (startup_load) dentro del timeout.",
            "La evidencia es insuficiente para certificar el patcher: suba --timeout o revise Max.",
        ]

    details = [
        f"Sesion verificada: {len(lines)} lineas, 0 errores de consola.",
        "Alcance: errores de consola y contratos de objetos durante la carga del patcher.",
        "No certifica equivalencia DSP, comportamiento en tiempo real ni fallos silenciosos (ver I11).",
    ]

    if any(CRASH_RECOVERY_MARKER.lower() in line.lower() for line in lines):
        details.append(
            "Aviso: Max restauro el workspace de una sesion previa interrumpida; "
            "las condiciones de arranque no fueron limpias."
        )

    return "PASS", details


def audit_patcher_live(patcher_path: Path, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> Tuple[str, List[str]]:
    """
    Ejecuta el patcher en Max.exe y audita la sesion de log resultante.
    Devuelve (veredicto, detalle_lineas).
    Veredictos posibles: PASS, FAIL, BLOCKED, y los de procedencia
    (STALE_CONTRACTS, STALE_IR, STALE_SOURCE, STALE_ARTIFACTS,
    UNVERIFIABLE, INVALID) cuando el paquete trae emitted-from.json.
    """
    # Max no abre rutas relativas: se resuelve a absoluta antes de lanzarlo.
    patcher_path = patcher_path.expanduser().resolve()

    if not patcher_path.is_file():
        return "FAIL", [f"El archivo objetivo no existe: {patcher_path}"]

    if patcher_path.suffix.lower() != ".maxpat":
        return "FAIL", [
            f"El objetivo no es un patcher Max (.maxpat): {patcher_path.name}",
        ]

    max_exe = resolve_max_executable()
    if not max_exe:
        return "BLOCKED", [
            "Max.exe no fue detectado en el sistema.",
            "Contrato Harmos: Prohibido emitir PASS sin ejecucion en vivo.",
            "Instale Cycling '74 Max o configure la variable MAX_PATH.",
        ]

    # Procedencia: se decide antes de arrancar Max. Un paquete obsoleto o alterado
    # no gasta un arranque del runtime para recibir un PASS que no le corresponde.
    prov_verdict, prov_details = audit_provenance(patcher_path)
    if prov_verdict is not None and prov_verdict != "VALID":
        return prov_verdict, [
            f"Procedencia rechazada: {PROVENANCE_RECORD_NAME} no certifica este paquete.",
            *prov_details,
            "Recompilar el paquete desde el IR antes de auditar: no se emite PASS.",
        ]

    # Puede no existir todavia: se re-resuelve durante el sondeo.
    max_log = resolve_max_log_path(max_exe)

    print(f"[*] Binario Max detectado: {max_exe}")
    print(f"[*] Lanzando patcher: {patcher_path.name}")
    print(f"[*] Esperando sesion de log y fin de carga (timeout max: {timeout_seconds}s)...")

    launched_after = time.time()
    try:
        proc = subprocess.Popen([str(max_exe), str(patcher_path)])
    except Exception as e:
        return "FAIL", [f"Error al iniciar Max.exe: {e}"]

    session_lines: Optional[List[str]] = None
    deadline = launched_after + max(timeout_seconds, 1)

    try:
        while time.time() < deadline:
            time.sleep(POLL_INTERVAL_SECONDS)

            if max_log is None or not max_log.is_file():
                max_log = resolve_max_log_path(max_exe)

            session_lines = load_session_lines(max_log, launched_after)

            if session_lines and any(STARTUP_COMPLETE_MARKER in line for line in session_lines):
                time.sleep(min(SETTLE_SECONDS, max(0.0, deadline - time.time())))
                session_lines = load_session_lines(max_log, launched_after) or session_lines
                break

            if proc.poll() is not None:
                session_lines = load_session_lines(max_log, launched_after) or session_lines
                break
    finally:
        # Cerrar el proceso para no dejar procesos huerfanos en CI/testing.
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    if not session_lines:
        return "BLOCKED", [
            "No se detecto una sesion de Max.log atribuible a esta corrida.",
            f"Log consultado: {max_log if max_log else 'no encontrado'}",
            "Sin sesion propia no hay telemetria verificable: prohibido emitir PASS.",
        ]

    return evaluate_session(session_lines)


def main():
    parser = argparse.ArgumentParser(description="Harmos Live Runtime Verifier")
    parser.add_argument("--patcher", type=str, required=True, help="Ruta al archivo .maxpat objetivo")
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Segundos maximos de espera para la sesion de Max.log (default: {DEFAULT_TIMEOUT_SECONDS}). "
             "La auditoria termina antes si Max completa la carga.",
    )
    args = parser.parse_args()

    patcher = Path(args.patcher)
    verdict, details = audit_patcher_live(patcher, timeout_seconds=args.timeout)

    print("\n" + "=" * 50)
    print(f" HARMOS LIVE AUDIT: {verdict}")
    print("=" * 50)
    for d in details:
        print(f"  {d}")
    print("-" * 50)

    if verdict == "PASS":
        sys.exit(0)
    elif verdict == "BLOCKED":
        sys.exit(2)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
