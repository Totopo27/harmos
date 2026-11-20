#!/usr/bin/env python3
"""
Harmos Live Runtime Verifier & Auditor.
Automatiza la verificacion en vivo de parches y packages en Cycling '74 Max.

Contrato Operativo (Hard Rules):
1. Deteccion de runtime Max (Registro de Windows / rutas estandar / MAX_PATH).
2. Si Max no esta disponible, el veredicto es estrictamente BLOCKED (no PASS).
3. Si Max esta disponible:
   - Snapshot previo del log de Max.
   - Ejecucion de Max.exe con el patcher objetivo.
   - Espera acotada y monitoreo de terminacion / estabilidad.
   - Parsing estricto de Max.log en busca de errores (Cero Tolerancia a lineas rojas).
   - Generacion de evidencia / receipt verificable.
"""
import sys
import os
import time
import uuid
import argparse
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List

# Cadenas que representan fallos o advertencias criticas en Max.log
FAIL_PATTERNS = [
    "doesn't match type",
    "no such object",
    "can't connect",
    "connecting to comment",
    "error:",
    "fatal:",
    "access violation",
    "crash",
    "0xc0000005",
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

    # Rutas por defecto en Windows
    candidates = [
        Path(r"D:\Program Files\Cycling '74\Max 9\Max.exe"),
        Path(r"C:\Program Files\Cycling '74\Max 9\Max.exe"),
        Path(r"C:\Program Files\Cycling '74\Max 8\Max.exe"),
    ]
    for c in candidates:
        if c.is_file():
            return c

    return None


def resolve_max_log_path(max_exe: Optional[Path] = None) -> Optional[Path]:
    """
    Localiza el archivo Max.log en el directorio de usuario.
    Si se suministra max_exe, prioriza la subcarpeta correspondiente a la version.
    """
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None

    base = Path(appdata) / "Cycling '74"
    if not base.exists():
        return None

    # Priorizar por version detectada en el ejecutable
    if max_exe:
        exe_str = str(max_exe).lower()
        if "max 9" in exe_str:
            v9_candidates = list(base.glob("*Max 9*/Max.log"))
            if v9_candidates and v9_candidates[0].is_file():
                return v9_candidates[0]
        elif "max 8" in exe_str:
            v8_candidates = list(base.glob("*Max 8*/Max.log"))
            if v8_candidates and v8_candidates[0].is_file():
                return v8_candidates[0]

    for log_candidate in base.glob("**/Max.log"):
        if log_candidate.is_file():
            return log_candidate

    return None


def read_log_delta_binary(max_log: Path, log_size_before: int, sentinel_bytes: Optional[bytes] = None) -> List[str]:
    """
    Lee de forma determinista el delta de Max.log abriendo en modo binario ('rb')
    para evitar desajustes de offset por caracteres CRLF (\\r\\n) en Windows.
    Si existe un marcador centinela, extrae unicamente lo posterior a el.
    """
    if not max_log or not max_log.is_file():
        return []

    with open(max_log, "rb") as f:
        f.seek(log_size_before)
        raw_bytes = f.read()

    if sentinel_bytes and sentinel_bytes in raw_bytes:
        raw_bytes = raw_bytes.split(sentinel_bytes, 1)[1]

    decoded = raw_bytes.decode("utf-8", errors="replace")
    return [line.strip() for line in decoded.splitlines() if line.strip()]


def audit_patcher_live(patcher_path: Path, timeout_seconds: int = 10) -> Tuple[str, List[str]]:
    """
    Ejecuta el patcher en Max.exe y audita el log resultante.
    Devuelve (veredicto, detalle_lineas).
    Veredictos posibles: PASS, FAIL, BLOCKED.
    """
    if not patcher_path.is_file():
        return "FAIL", [f"El archivo objetivo no existe: {patcher_path}"]

    max_exe = resolve_max_executable()
    if not max_exe:
        return "BLOCKED", [
            "Max.exe no fue detectado en el sistema.",
            "Contrato Harmos: Prohibido emitir PASS sin ejecucion en vivo.",
            "Instale Cycling '74 Max o configure la variable MAX_PATH.",
        ]

    max_log = resolve_max_log_path(max_exe)
    log_size_before = max_log.stat().st_size if max_log and max_log.is_file() else 0

    # Inyeccion de marcador centinela en modo binario para aislar la sesion actual
    run_id = str(uuid.uuid4())[:8]
    sentinel_str = f"\n=== HARMOS_AUDIT_SENTINEL_{run_id} ===\n"
    sentinel_bytes = sentinel_str.strip().encode("utf-8")

    if max_log and max_log.exists():
        try:
            with open(max_log, "ab") as f:
                f.write(sentinel_str.encode("utf-8"))
            log_size_before = max_log.stat().st_size
        except Exception:
            # Si el log esta bloqueado, procedemos con offset por bytes
            pass

    print(f"[*] Binario Max detectado: {max_exe}")
    print(f"[*] Lanzando patcher: {patcher_path.name}")
    print(f"[*] Sondeando telemetria en vivo (timeout max: {timeout_seconds}s)...")

    # Iniciar Max con el patcher
    try:
        proc = subprocess.Popen([str(max_exe), str(patcher_path)])
    except Exception as e:
        return "FAIL", [f"Error al iniciar Max.exe: {e}"]

    # Sondeo reactivo en lugar de sleep() ciego
    start_time = time.time()
    poll_interval = 0.5
    stable_checks = 0
    last_known_size = log_size_before

    try:
        while (time.time() - start_time) < timeout_seconds:
            time.sleep(poll_interval)
            
            # Verificar si el proceso termino anticipadamente (ej. crash)
            if proc.poll() is not None:
                break

            if max_log and max_log.is_file():
                try:
                    current_size = max_log.stat().st_size
                    if current_size > last_known_size:
                        last_known_size = current_size
                        stable_checks = 0
                    else:
                        stable_checks += 1
                        # Si tras al menos 2.5s el log no registra mas escrituras, consideramos estable
                        if stable_checks >= 3 and (time.time() - start_time) >= 2.5:
                            break
                except OSError:
                    pass
    finally:
        # Cerrar el proceso para no dejar procesos huerfanos en CI/testing
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    if not max_log or not max_log.is_file():
        return "BLOCKED", ["No se encontro Max.log para auditar telemetria de ejecucion."]

    # Leer delta binario
    try:
        new_lines = read_log_delta_binary(max_log, log_size_before, sentinel_bytes)
    except Exception as e:
        return "FAIL", [f"Error leyendo Max.log en modo binario: {e}"]

    # Analizar si hay lineas rojas o advertencias
    detected_errors = []
    for line in new_lines:
        line_clean = line.strip()
        line_lower = line_clean.lower()
        for pattern in FAIL_PATTERNS:
            if pattern in line_lower:
                detected_errors.append(line_clean)
                break

    if detected_errors:
        return "FAIL", detected_errors

    return "PASS", [
        f"Sesion completada limpiamente ({len(new_lines)} lineas registradas sin errores de consola).",
        "Alcance: Certifica legalidad de parches y contratos. (No certifica equivalencia matematica ni DSP; ver I11)."
    ]


def main():
    parser = argparse.ArgumentParser(description="Harmos Live Runtime Verifier")
    parser.add_argument("--patcher", type=str, required=True, help="Ruta al archivo .maxpat objetivo")
    parser.add_argument("--timeout", type=int, default=8, help="Segundos de ejecucion en vivo (default: 8)")
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
