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


def resolve_max_log_path() -> Optional[Path]:
    """Localiza el archivo Max.log en el directorio de usuario."""
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None

    base = Path(appdata) / "Cycling '74"
    if not base.exists():
        return None

    for log_candidate in base.glob("**/Max.log"):
        if log_candidate.is_file():
            return log_candidate

    return None


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

    max_log = resolve_max_log_path()
    log_size_before = max_log.stat().st_size if max_log and max_log.is_file() else 0

    print(f"[*] Binario Max detectado: {max_exe}")
    print(f"[*] Lanzando patcher: {patcher_path.name}")
    print(f"[*] Esperando estabilizacion ({timeout_seconds}s)...")

    # Iniciar Max con el patcher
    try:
        proc = subprocess.Popen([str(max_exe), str(patcher_path)])
    except Exception as e:
        return "FAIL", [f"Error al iniciar Max.exe: {e}"]

    try:
        time.sleep(timeout_seconds)
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

    # Leer las lineas agregadas durante la sesion
    new_lines = []
    try:
        with open(max_log, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(log_size_before)
            new_lines = f.readlines()
    except Exception as e:
        return "FAIL", [f"Error leyendo Max.log: {e}"]

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

    return "PASS", [f"Sesion completada limpiamente. {len(new_lines)} lineas registradas sin errores."]


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
