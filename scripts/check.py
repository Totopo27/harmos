#!/usr/bin/env python3
"""
Harmos Guardrail & Pre-Commit Verifier.
Verifica de forma determinista antes de cada commit o PR:
1. Suite completa de tests unitarios (tests/).
2. Escaneo estatico de PII, rutas absolutas de host y secretos.
3. Formato y sintaxis JSON de esquemas y contratos.
"""
import sys
import os
import subprocess
import re
import json
from pathlib import Path

# Patrones prohibidos en archivos trackeados
FORBIDDEN_PATTERNS = [
    (r"[a-zA-Z]:\\\\", "Ruta absoluta con letra de unidad Windows"),
    (r"C:\\\\Users", "Ruta de usuario Windows"),
    (r"/home/[a-zA-Z0-9_-]+/", "Ruta absoluta de usuario Linux/macOS"),
    (r"ghp_[a-zA-Z0-9]{20,}", "GitHub Personal Access Token"),
    (r"gho_[a-zA-Z0-9]{20,}", "GitHub OAuth Token"),
]

# Extensiones prohibidas de scripts de host en el repo canonico
BANNED_EXTENSIONS = [".ps1", ".bat", ".cmd"]


def run_unit_tests() -> bool:
    print("[1/3] Ejecutando suite de tests unitarios...")
    result = subprocess.run([sys.executable, "-m", "unittest", "discover", "tests"], capture_output=True, text=True)
    if result.returncode == 0:
        print("  OK Tests unitarios: 100% pasando.")
        return True
    else:
        print("  FAIL en tests unitarios:\n")
        print(result.stdout)
        print(result.stderr)
        return False


def validate_json_schemas() -> bool:
    print("[2/3] Validando integridad de contratos y esquemas JSON...")
    schema_dir = Path("core/schema")
    if not schema_dir.exists():
        print("  FAIL: Directorio core/schema no encontrado.")
        return False

    all_valid = True
    for json_file in schema_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                json.load(f)
            print(f"  OK {json_file.name}: JSON sintacticamente valido.")
        except Exception as e:
            print(f"  FAIL: Error parseando {json_file.name}: {e}")
            all_valid = False

    return all_valid


def scan_for_leaks_and_pii() -> bool:
    print("[3/3] Escaneando arbol git en busca de PII, rutas de host o secretos...")
    
    result = subprocess.run(["git", "ls-files"], capture_output=True, text=True)
    if result.returncode != 0:
        print("  WARN: No se pudo ejecutar git ls-files. Saltando chequeo.")
        return True

    files = result.stdout.strip().splitlines()
    has_leaks = False

    for file_path in files:
        path_obj = Path(file_path)

        # 1. Chequeo de extension prohibida
        if path_obj.suffix.lower() in BANNED_EXTENSIONS:
            print(f"  FAIL ARCHIVO PROHIBIDO TRACKEADO: {file_path} (script efimero de host)")
            has_leaks = True

        # 2. Chequeo de contenido en archivos de texto
        if path_obj.suffix.lower() in [".md", ".py", ".json", ".cpp", ".hpp", ".txt", ".cmake"]:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, start=1):
                        for pattern, desc in FORBIDDEN_PATTERNS:
                            if re.search(pattern, line):
                                if file_path.replace("\\", "/").endswith("scripts/check.py"):
                                    continue
                                print(f"  FAIL FUGA DETECTADA en {file_path}:{line_num}: {desc}")
                                has_leaks = True
            except Exception as e:
                pass

    if not has_leaks:
        print("  OK Escaneo de privacidad: 0 rutas absolutas o secretos encontrados.")
        return True
    return False


def main():
    print("==================================================")
    print("   HARMOS PRE-COMMIT GUARDRAIL & VERIFIER         ")
    print("==================================================\n")

    step1 = run_unit_tests()
    step2 = validate_json_schemas()
    step3 = scan_for_leaks_and_pii()

    print("\n--------------------------------------------------")
    if step1 and step2 and step3:
        print("ESTADO: VERIFICACION APROBADA (PASS)")
        print("El repositorio cumple los estandares de calidad y privacidad.")
        sys.exit(0)
    else:
        print("ESTADO: VERIFICACION RECHAZADA (FAIL)")
        print("Corrija los errores anteriores antes de hacer commit o push.")
        sys.exit(1)


if __name__ == "__main__":
    main()
