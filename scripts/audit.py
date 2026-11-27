#!/usr/bin/env python3
"""
Harmos Live Runtime Verifier & Auditor.
Automatiza la verificacion en vivo de parches y packages en Cycling '74 Max.

Contrato Operativo (Hard Rules):
1. Deteccion de runtime Max (Registro de Windows / rutas estandar / MAX_PATH).
2. Puertas estaticas: la procedencia y los patchcords se evaluan antes de resolver
   el runtime, porque solo leen archivos. Un rechazo estatico es FAIL aunque Max no
   este instalado.
3. Si las puertas estaticas aprueban y Max no esta disponible, el veredicto es
   estrictamente BLOCKED (no PASS): BLOCKED significa "falta el runtime", no "no se
   pudo comprobar nada".
4. Si Max esta disponible:
   - Aislamiento por sesion de log: Max trunca Max.log en cada arranque, por lo que
     la lectura se ancla al header de sesion y no a offsets de bytes.
   - Ejecucion de Max.exe con el patcher objetivo.
   - Espera event-driven hasta fin de carga (startup_load), con timeout acotado.
   - Parsing estricto de la sesion de Max.log: nivel `error` o patrones criticos.
   - Fail-closed: sin sesion propia o sin carga completada el veredicto es BLOCKED.
   - Generacion de evidencia / receipt verificable.
   - Procedencia: si el paquete incluye `emitted-from.json` junto al patcher, se
     verifica antes de los contratos; un veredicto distinto de VALID impide PASS.
   - Contratos: los patchcords del patcher se validan contra
     `core/schema/max_contracts.json`; una conexion que el contrato declara ilegal
     produce FAIL. Se reutiliza la misma puerta que usa el emisor (`ContractEngine`),
     sin indices de inlet/outlet codificados aqui.
"""
import sys
import os
import re
import json
import signal
import time
import argparse
import contextlib
import io
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, NamedTuple, Sequence

# El script se ejecuta como `python scripts/audit.py`: la raiz del repo debe estar
# en sys.path para importar el motor de procedencia.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.compiler.provenance import verify_provenance
from core.compiler.contract_engine import ContractEngine
from core.compiler.cli_output import emit_json_envelope
from core.compiler.live_bridge import LiveAuditReceipt, LiveBridgeError, MaxLiveBridge

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


def audit_provenance(patcher_path: Path, ir_path: Optional[Path] = None) -> Tuple[Optional[str], List[str]]:
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
        return verify_provenance(record, current_ir_path=ir_path)
    except Exception as e:
        return "UNVERIFIABLE", [
            f"Error al verificar la procedencia: {e}",
            "Sin evidencia legible no se certifica el paquete.",
        ]


# Archivo de contratos que valida la puerta estatica de patchcords.
CONTRACTS_SCHEMA_PATH = "core/schema/max_contracts.json"


class PatcherDocumentError(ValueError):
    """El objetivo no es un documento JSON nativo de Max; no puede cargarse."""


def _maxpat_containers(document: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Devuelve todos los contenedores `patcher` del documento, subpatchers incluidos.

    En el formato nativo de Max un objeto `p`/`bpatcher` guarda su parche hijo en
    `box["patcher"]`, por lo que los cables internos solo se validan recorriendo
    esos contenedores.
    """
    containers: List[Dict[str, Any]] = []
    pending = [document.get("patcher")]
    while pending:
        current = pending.pop()
        if not isinstance(current, dict):
            continue
        containers.append(current)
        for entry in current.get("boxes") or []:
            box = entry.get("box") if isinstance(entry, dict) else None
            if isinstance(box, dict) and isinstance(box.get("patcher"), dict):
                pending.append(box["patcher"])
    return containers


def _index_boxes(container: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """Mapea el id de cada caja a su texto y maxclass declarados."""
    index: Dict[str, Dict[str, str]] = {}
    for entry in container.get("boxes") or []:
        box = entry.get("box") if isinstance(entry, dict) else None
        if not isinstance(box, dict):
            continue
        box_id = box.get("id")
        if not isinstance(box_id, str) or not box_id:
            continue
        text = box.get("text")
        maxclass = box.get("maxclass")
        index[box_id] = {
            "text": text if isinstance(text, str) else "",
            "maxclass": maxclass if isinstance(maxclass, str) else "",
        }
    return index


def _as_port_index(value: Any) -> Optional[int]:
    """Normaliza el indice de inlet/outlet de un patchline; None si no es entero."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and not value.is_integer():
        return None
    return int(value)


class ContractAudit(NamedTuple):
    violations: Optional[List[str]]
    checked: int
    unverifiable: List[str]


def assess_patcher_contracts(
    patcher_path: Path, contract_engine: Optional[ContractEngine] = None,
) -> ContractAudit:
    """
    Valida los patchcords del patcher contra `core/schema/max_contracts.json`.

    Recorre el documento nativo de Max y evalua cada cable con
    `ContractEngine.assess_connection`, la misma puerta que usa el emisor
    (`TypedPatch.connect`). No hay numeros de inlet/outlet codificados aqui: el
    motor distingue conexiones ilegales y evidencia de contratos ausente.

    Devuelve violaciones, cables evaluados y conexiones no verificables.
    `violations` es `None` cuando
    el archivo no expone un contenedor `patcher` nativo: en ese caso no hay
    contratos que validar y el veredicto lo declara explicitamente.
    Lanza `PatcherDocumentError` si el archivo no es JSON legible.
    """
    try:
        document = json.loads(patcher_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError) as e:
        raise PatcherDocumentError(
            f"No se pudo leer el patcher {patcher_path.name}: {e}"
        ) from e
    except json.JSONDecodeError as e:
        raise PatcherDocumentError(
            f"El patcher {patcher_path.name} no es un documento JSON nativo de Max: {e}"
        ) from e

    containers = _maxpat_containers(document) if isinstance(document, dict) else []
    if not containers:
        return ContractAudit(None, 0, [])

    engine = contract_engine or ContractEngine()
    violations: List[str] = []
    unverifiable: List[str] = []
    checked = 0

    for container in containers:
        boxes = _index_boxes(container)
        for entry in container.get("lines") or []:
            patchline = entry.get("patchline") if isinstance(entry, dict) else None
            if not isinstance(patchline, dict):
                continue
            source = patchline.get("source")
            destination = patchline.get("destination")
            if not isinstance(source, list) or not isinstance(destination, list):
                continue
            if len(source) < 2 or len(destination) < 2:
                continue

            src_id, src_outlet = source[0], _as_port_index(source[1])
            dest_id, dest_inlet = destination[0], _as_port_index(destination[1])
            if src_outlet is None or dest_inlet is None:
                continue

            src_box = boxes.get(src_id) if isinstance(src_id, str) else None
            dest_box = boxes.get(dest_id) if isinstance(dest_id, str) else None
            if src_box is None or dest_box is None:
                # Extremo no resoluble: la carga en vivo lo reporta como fallo.
                continue

            checked += 1
            src_label = src_box["text"] or src_id
            dest_label = dest_box["text"] or dest_id

            if dest_box["maxclass"] == "comment":
                violations.append(
                    f"{src_label} outlet {src_outlet} -> {dest_label}: "
                    "las cajas 'comment' carecen de inlets funcionales."
                )
                continue

            src_spec = "message" if src_box["maxclass"] == "message" else src_box["text"]
            dest_spec = "message" if dest_box["maxclass"] == "message" else dest_box["text"]
            result = engine.assess_connection(
                src_spec, src_outlet, dest_spec, dest_inlet
            )
            if result.status != "VALID":
                issues = violations if result.status == "INVALID" else unverifiable
                issues.append(
                    f"{src_label} outlet {src_outlet} -> {dest_label} "
                    f"inlet {dest_inlet}: {result.reason}"
                )

    return ContractAudit(violations, checked, unverifiable)


def audit_contracts(patcher_path: Path) -> Tuple[Optional[List[str]], int]:
    """Legacy tuple interface; missing evidence is reported, never silently valid."""
    result = assess_patcher_contracts(patcher_path)
    issues = None if result.violations is None else result.violations + result.unverifiable
    return issues, result.checked


def _iter_windows_fixed_drives() -> List[Path]:
    """Enumera unidades fijas locales montadas en Windows sin hardcodear letras."""
    if sys.platform != "win32":
        return []
    try:
        import ctypes
        import string

        kernel32 = ctypes.windll.kernel32
        mask = int(kernel32.GetLogicalDrives())
        drive_fixed = 3
        drives: List[Path] = []
        for idx, letter in enumerate(string.ascii_uppercase):
            if mask & (1 << idx):
                root = f"{letter}:{os.sep}"
                if kernel32.GetDriveTypeW(root) == drive_fixed:
                    drives.append(Path(root))
        return drives
    except Exception:
        return []


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

    if sys.platform == "darwin":
        for version in ("Max 9", "Max 8", "Max"):
            for candidate in (
                Path(f"/Applications/{version}.app/Contents/MacOS/Max"),
                Path.home() / f"Applications/{version}.app/Contents/MacOS/Max",
            ):
                if candidate.is_file():
                    return candidate

    # Rutas por defecto en Windows: se recorren los directorios de programa
    # declarados por el entorno y las unidades fijas montadas. El codigo nunca
    # codifica rutas absolutas de host.
    roots: List[Path] = []
    seen_roots: set[str] = set()

    def _add_root(raw_root: Optional[Any]) -> None:
        if not raw_root:
            return
        root_path = Path(raw_root)
        key = os.path.normcase(os.path.abspath(str(root_path)))
        if key not in seen_roots:
            seen_roots.add(key)
            roots.append(root_path)

    for env_name in ("ProgramW6432", "ProgramFiles", "ProgramFiles(x86)"):
        _add_root(os.environ.get(env_name))
    if sys.platform == "win32":
        sys_drive = os.environ.get("SystemDrive", "C:")
        candidate_root = Path(f"{sys_drive}\\Program Files")
        if candidate_root.is_dir():
            _add_root(candidate_root)
        for drive in _iter_windows_fixed_drives():
            for subdir in ("Program Files", "Program Files (x86)"):
                drive_root = drive / subdir
                if drive_root.is_dir():
                    _add_root(drive_root)

    candidates = []
    for version in ("Max 9", "Max 8"):
        for root in roots:
            candidate = root / "Cycling '74" / version / "Max.exe"
            if candidate not in candidates:
                candidates.append(candidate)
    for c in candidates:
        if c.is_file():
            return c

    return None


def resolve_max_log_path(max_exe: Optional[Path] = None) -> Optional[Path]:
    """
    Localiza el archivo Max.log dentro de la carpeta de usuario de Max.

    En Max 9 la ruta canonica es <APPDATA>/Cycling '74/Max 9/Logs/Max.log (Windows)
    o ~/Library/Logs/Cycling '74/Max 9/Max.log (macOS). Si max_exe revela la version
    ("Max 9"), se prefiere el log de esa version en ambas plataformas.
    """
    wants = None
    if max_exe:
        version = re.search(r"\bmax (\d+)\b", str(max_exe).lower())
        if version:
            wants = f"max {version.group(1)}"

    candidates: List[Path] = []
    if sys.platform == "darwin":
        mac_bases = [
            Path.home() / "Library" / "Logs" / "Cycling '74",
            Path.home() / "Library" / "Application Support" / "Cycling '74",
        ]
        for base in mac_bases:
            if base.exists():
                candidates.extend(p for p in base.glob("*/Logs/Max.log") if p.is_file())
                candidates.extend(p for p in base.glob("*/Max.log") if p.is_file())

    if not candidates:
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) / "Cycling '74" if appdata else None
        if base is not None and base.exists():
            candidates.extend(p for p in base.glob("*/Logs/Max.log") if p.is_file())

    candidates = sorted(set(candidates), key=lambda p: str(p).lower())
    if not candidates:
        return None

    if wants:
        for candidate in candidates:
            if wants in (part.lower() for part in candidate.parts):
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


def _detect_console_errors(lines: Sequence[str]) -> List[str]:
    detected_errors: List[str] = []
    for line in lines:
        parsed = parse_log_line(line)
        level = parsed["level"].lower() if parsed else ""
        lowered = line.lower()
        if level in FAIL_LEVELS or any(pattern in lowered for pattern in FAIL_PATTERNS):
            detected_errors.append(line)
    return detected_errors


def evaluate_session(lines: List[str]) -> Tuple[str, List[str]]:
    """
    Evalua la sesion de log y devuelve (veredicto, detalle).

    Fail-closed: una sesion vacia o sin fin de carga nunca produce PASS, porque
    no constituye evidencia de que el patcher se haya cargado sin errores.
    """
    if not lines:
        return "BLOCKED", ["Sesion de log vacia: no hay evidencia de ejecucion."]

    detected_errors = _detect_console_errors(lines)
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


def evaluate_live_receipt(receipt: LiveAuditReceipt) -> Tuple[str, List[str]]:
    """Evalua de forma fail-closed la telemetria devuelta por un puente vivo en Max."""
    if not receipt.loaded or not receipt.runtime.strip():
        return "BLOCKED", [
            f"BLOCKED (RUNTIME_UNAVAILABLE): Puente vivo en {receipt.endpoint} no reporto carga verificable del patcher.",
            "Sin confirmacion de carga en runtime real: prohibido emitir PASS.",
        ]

    if receipt.failed_objects:
        return "FAIL", [f"Objeto fallido en runtime: {obj}" for obj in receipt.failed_objects]

    detected_errors = _detect_console_errors(receipt.console_lines)
    if detected_errors:
        return "FAIL", detected_errors

    return "PASS", [
        f"Puente vivo verificado ({receipt.runtime} via {receipt.endpoint}): "
        f"{len(receipt.console_lines)} lineas de consola, 0 errores.",
        "Alcance: errores de consola y contratos de objetos durante la carga del patcher.",
        "No certifica equivalencia DSP, comportamiento en tiempo real ni fallos silenciosos (ver I11).",
    ]


def _terminate_process_tree(proc: Any) -> None:
    """Termina el proceso lanzado y su grupo/arbol completo en Windows y POSIX."""
    pid = getattr(proc, "pid", None)
    if sys.platform == "win32":
        if isinstance(pid, int) and pid > 0:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True,
                    check=False,
                )
            except Exception:
                pass
    elif hasattr(os, "killpg") and isinstance(pid, int) and pid > 0:
        try:
            os.killpg(pid, signal.SIGTERM)
            proc.wait(timeout=3)
            return
        except subprocess.TimeoutExpired:
            try:
                os.killpg(pid, getattr(signal, "SIGKILL", signal.SIGTERM))
                proc.wait(timeout=1)
                return
            except (OSError, subprocess.SubprocessError):
                pass
        except (ProcessLookupError, OSError):
            pass

    try:
        proc.terminate()
        proc.wait(timeout=3)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def _append_static_gate_details(
    details: List[str],
    prov_verdict: Optional[str],
    contract_violations: Optional[List[str]],
    contract_checked: int,
) -> None:
    if prov_verdict == "VALID":
        details.append(
            "Procedencia verificada: emitted-from.json certifica los contratos y la "
            "integridad de los artefactos emitidos."
        )
    elif prov_verdict is None:
        details.append(
            f"Sin {PROVENANCE_RECORD_NAME} junto al patcher: la procedencia no fue certificada."
        )

    if contract_violations is None:
        details.append(
            "Contratos no evaluados: el archivo no expone un contenedor 'patcher' nativo de Max."
        )
    elif contract_checked:
        details.append(
            f"Contratos verificados: {contract_checked} conexiones evaluadas contra "
            f"{CONTRACTS_SCHEMA_PATH}, 0 ilegales."
        )
    else:
        details.append(
            f"Contratos verificados: 0 patchcords que evaluar en {CONTRACTS_SCHEMA_PATH}."
        )


def audit_patcher_live(
    patcher_path: Path, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    *, ir_path: Optional[Path] = None,
    live_endpoint: Optional[str] = None,
) -> Tuple[str, List[str]]:
    """
    Ejecuta el patcher en Max.exe y audita la sesion de log resultante.
    Devuelve (veredicto, detalle_lineas).
    Veredictos posibles: PASS, FAIL, BLOCKED, UNVERIFIABLE, y los de procedencia
    (STALE_CONTRACTS, STALE_IR, STALE_SOURCE, STALE_ARTIFACTS,
    UNVERIFIABLE, INVALID) cuando el paquete trae emitted-from.json.
    Orden: primero las puertas estaticas (procedencia, luego contratos), despues la
    resolucion del runtime. Una conexion ilegal produce FAIL sin gastar arranque y
    sin necesitar Max instalado; BLOCKED queda para cuando lo estatico paso.
    """
    # Max no abre rutas relativas: se resuelve a absoluta antes de lanzarlo.
    patcher_path = patcher_path.expanduser().resolve()

    if not patcher_path.is_file():
        return "FAIL", [f"El archivo objetivo no existe: {patcher_path}"]

    if patcher_path.suffix.lower() != ".maxpat":
        return "FAIL", [
            f"El objetivo no es un patcher Max (.maxpat): {patcher_path.name}",
        ]

    # Puertas estaticas: procedencia y contratos solo leen archivos, asi que se
    # deciden antes de resolver el runtime. En un host sin Max un patcher ilegal es
    # FAIL, no BLOCKED: BLOCKED significa "todo lo estatico paso, falta el runtime".
    #
    # Procedencia primero: un paquete emitido contra un esquema anterior conserva su
    # propio veredicto y no se juzga contra un esquema para el que no fue emitido.
    prov_verdict, prov_details = audit_provenance(patcher_path, ir_path=ir_path)
    if prov_verdict is not None and prov_verdict != "VALID":
        return prov_verdict, [
            f"Procedencia rechazada: {PROVENANCE_RECORD_NAME} no certifica este paquete.",
            *prov_details,
            "Recompilar el paquete desde el IR antes de auditar: no se emite PASS.",
        ]

    # Contratos: los patchcords se validan contra max_contracts.json antes de
    # arrancar Max. Un cable ilegal no gasta un arranque del runtime ni recibe un
    # PASS que el contrato no respalda.
    try:
        if ir_path is not None:
            if prov_verdict != "VALID":
                return "UNVERIFIABLE", ["An IR contract requires matching emitted-from.json provenance."]
            ir = json.loads(Path(ir_path).read_text(encoding="utf-8"))
            engine = ContractEngine.from_ir(ir)
        else:
            engine = ContractEngine()
        contract_result = assess_patcher_contracts(patcher_path, engine)
        contract_violations, contract_checked, unverifiable = contract_result
    except PatcherDocumentError as e:
        return "FAIL", [
            str(e),
            "Un patcher ilegible no puede cargarse en Max: no se emite PASS.",
        ]
    except (OSError, ValueError, KeyError, TypeError) as e:
        return "UNVERIFIABLE", [f"Contract evidence could not be validated: {e}"]

    if contract_violations:
        return "FAIL", [
            "Contratos rechazados: el patcher contiene conexiones ilegales segun "
            f"{CONTRACTS_SCHEMA_PATH}.",
            *contract_violations[:20],
            "Corregir el emisor o el IR antes de auditar: no se emite PASS.",
        ]
    if unverifiable:
        return "UNVERIFIABLE", [
            "Missing contracts: static validation is incomplete; no PASS is issued.",
            *unverifiable[:20],
            "Supply catalog contracts, or --ir with matching package provenance for a generated object.",
        ]

    # Recien aqui se requiere el runtime: las puertas estaticas ya aprobaron.
    if live_endpoint is not None:
        try:
            with MaxLiveBridge(
                live_endpoint,
                contract_engine=engine,
                timeout=max(float(timeout_seconds), 1.0),
            ) as bridge:
                receipt = bridge.audit_patcher(patcher_path, timeout_seconds=timeout_seconds)
        except (LiveBridgeError, OSError) as exc:
            return "BLOCKED", [
                f"BLOCKED (RUNTIME_UNAVAILABLE): Puente vivo no disponible en {live_endpoint} ({exc}).",
                "Contrato Harmos: Prohibido emitir PASS sin ejecucion en vivo.",
            ]

        verdict, details = evaluate_live_receipt(receipt)
        _append_static_gate_details(details, prov_verdict, contract_violations, contract_checked)
        return verdict, details

    max_exe = resolve_max_executable()
    if not max_exe:
        return "BLOCKED", [
            "BLOCKED (RUNTIME_UNAVAILABLE): Max.exe no fue detectado en el sistema.",
            "Contrato Harmos: Prohibido emitir PASS sin ejecucion en vivo.",
            "Instale Cycling '74 Max o configure la variable MAX_PATH.",
        ]

    # Puede no existir todavia: se re-resuelve durante el sondeo.
    max_log = resolve_max_log_path(max_exe)

    print(f"[*] Binario Max detectado: {max_exe}")
    print(f"[*] Lanzando patcher: {patcher_path.name}")
    print(f"[*] Esperando sesion de log y fin de carga (timeout max: {timeout_seconds}s)...")

    launched_after = time.time()
    try:
        proc = subprocess.Popen(
            [str(max_exe), str(patcher_path)],
            start_new_session=(sys.platform != "win32"),
        )
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
        # Cerrar el proceso y su arbol/grupo para no dejar procesos huerfanos.
        _terminate_process_tree(proc)

    if not session_lines:
        return "BLOCKED", [
            "No se detecto una sesion de Max.log atribuible a esta corrida.",
            f"Log consultado: {max_log if max_log else 'no encontrado'}",
            "Sin sesion propia no hay telemetria verificable: prohibido emitir PASS.",
        ]

    verdict, details = evaluate_session(session_lines)
    _append_static_gate_details(details, prov_verdict, contract_violations, contract_checked)
    return verdict, details


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser CLI de auditoria en vivo de Harmos."""
    parser = argparse.ArgumentParser(description="Harmos Live Runtime Verifier")
    parser.add_argument("--patcher", type=str, required=True, help="Ruta al archivo .maxpat objetivo")
    parser.add_argument(
        "--ir", type=Path, default=None,
        help="IR contract for a generated object; must match emitted-from.json provenance.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Segundos maximos de espera para la sesion de Max.log (default: {DEFAULT_TIMEOUT_SECONDS}). "
             "La auditoria termina antes si Max completa la carga.",
    )
    parser.add_argument(
        "--live-endpoint",
        type=str,
        default=None,
        help="Endpoint WebSocket loopback de un puente vivo en Max (ej. ws://127.0.0.1:7400)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        dest="json_output",
        help="Emitir salida estructurada en formato JSON uniforme",
    )
    return parser


def main(argv: Optional[List[str]] = None):
    parser = build_parser()
    args = parser.parse_args(argv)

    patcher = Path(args.patcher)
    if args.json_output:
        with contextlib.redirect_stdout(io.StringIO()):
            verdict, details = audit_patcher_live(
                patcher,
                timeout_seconds=args.timeout,
                ir_path=args.ir,
                live_endpoint=args.live_endpoint,
            )
        exit_code = 0 if verdict == "PASS" else (2 if verdict == "BLOCKED" else 1)
        emit_json_envelope(
            status=verdict,
            command="audit",
            artifacts={
                "patcher": str(patcher),
                "ir": str(args.ir) if args.ir else None,
                "live_endpoint": args.live_endpoint,
            },
            diagnostics=list(details),
            exit_code=exit_code,
        )
        sys.exit(exit_code)

    verdict, details = audit_patcher_live(
        patcher,
        timeout_seconds=args.timeout,
        ir_path=args.ir,
        live_endpoint=args.live_endpoint,
    )

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
