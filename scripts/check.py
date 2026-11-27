#!/usr/bin/env python3
"""
Harmos Guardrail & Pre-Commit Verifier.
Verifica de forma determinista antes de cada commit o PR:
1. Suite completa de tests unitarios (tests/).
2. Sintaxis JSON y estructura del catalogo de contratos (no JSON Schema general).
3. Escaneo estatico de PII, rutas absolutas de host y secretos.
"""
import argparse
import contextlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.compiler.cli_output import emit_json_envelope
from core.compiler.contract_engine import validate_contracts

# Patrones prohibidos en archivos trackeados
FORBIDDEN_PATTERNS = [
    (r"(?<![A-Za-z])C:[\\/]Users[\\/]", "Ruta de usuario Windows"),
    (r"(?<![A-Za-z])[A-Za-z]:[\\/]", "Ruta absoluta con letra de unidad Windows"),
    (r"/home/[a-zA-Z0-9_-]+/", "Ruta absoluta de usuario Linux"),
    (r"/Users/[a-zA-Z0-9_-]+/", "Ruta absoluta de usuario macOS"),
    (r"ghp_[a-zA-Z0-9]{20,}", "GitHub Personal Access Token"),
    (r"gho_[a-zA-Z0-9]{20,}", "GitHub OAuth Token"),
    (r"github_pat_[A-Za-z0-9_]{22,}", "GitHub Fine-Grained Personal Access Token"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----", "Clave privada PEM"),
]

# Extensiones prohibidas de scripts de host en el repo canonico
BANNED_EXTENSIONS = [".ps1", ".bat", ".cmd"]

# Extensiones de texto analizadas contra fugas y PII
SCANNED_EXTENSIONS = [
    ".md", ".py", ".json", ".cpp", ".hpp", ".txt", ".cmake", ".yml", ".yaml",
    ".toml", ".env", ".sh", ".xml",
]


def _is_scanned_text(path_obj: Path) -> bool:
    # Dotfiles such as ".env" or ".env.local" have an empty suffix in pathlib.
    name = path_obj.name.lower()
    return path_obj.suffix.lower() in SCANNED_EXTENSIONS or name == ".env" or name.startswith(".env.")


def run_unit_tests() -> bool:
    print("[1/3] Ejecutando suite de tests unitarios...")
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "tests"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("  OK Tests unitarios: 100% pasando.")
        return True
    else:
        print("  FAIL en tests unitarios:\n")
        print(result.stdout)
        print(result.stderr)
        return False


def validate_json_schemas(schema_dir: Path = None) -> bool:
    """Check syntax and supported catalog shape, not full Draft-07 conformance."""
    if schema_dir is None:
        schema_dir = _REPO_ROOT / "core" / "schema"
    print("[2/3] Validando sintaxis JSON y estructura del catalogo de contratos...")
    if not schema_dir.exists():
        print("  FAIL: Directorio core/schema no encontrado.")
        return False

    all_valid = True
    catalog_seen = False
    for json_file in schema_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"  OK {json_file.name}: JSON sintacticamente valido.")
            if json_file.name == "max_contracts.json":
                catalog_seen = True
                validate_contracts(data)
                print("  OK Estructura de contratos: indices, nombres, aliases y tipos declarados.")
        except Exception as e:
            print(f"  FAIL: Sintaxis JSON o estructura invalida en {json_file.name}: {e}")
            all_valid = False

    if not catalog_seen:
        print("  FAIL: Falta max_contracts.json para validar la estructura de contratos.")
    print("  Alcance: no valida JSON Schema general ni sustituye la auditoria en Max.")
    return all_valid and catalog_seen


def scan_for_leaks_and_pii(repo_root: Path = None) -> bool:
    print("[3/3] Escaneando arbol git en busca de PII, rutas de host o secretos...")
    root = repo_root or _REPO_ROOT

    # Tracked plus untracked-but-not-ignored files: a leak must be caught before `git add`.
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=root, capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("  FAIL: No se pudo ejecutar git ls-files. Escaneo de privacidad falló de forma estricta (fail-closed).")
        return False

    files = sorted(set(result.stdout.strip().splitlines()))
    has_leaks = False

    for file_path in files:
        path_obj = root / file_path

        # 1. Chequeo de extension prohibida
        if path_obj.suffix.lower() in BANNED_EXTENSIONS:
            print(f"  FAIL ARCHIVO PROHIBIDO TRACKEADO: {file_path} (script efimero de host)")
            has_leaks = True

        # 2. Chequeo de contenido en archivos de texto
        if _is_scanned_text(path_obj) and path_obj.is_file():
            try:
                with open(path_obj, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, start=1):
                        for pattern, desc in FORBIDDEN_PATTERNS:
                            if re.search(pattern, line):
                                if file_path.replace("\\", "/").endswith("scripts/check.py"):
                                    continue
                                print(f"  FAIL FUGA DETECTADA en {file_path}:{line_num}: {desc}")
                                has_leaks = True
            except Exception as e:
                print(f"  WARN: Error leyendo {file_path}: {e}")

    if not has_leaks:
        print("  OK Escaneo de privacidad: 0 rutas absolutas o secretos encontrados.")
        return True
    return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harmos Pre-Commit Guardrail & Verifier")
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        dest="json_output",
        help="Emitir salida estructurada en formato JSON uniforme",
    )
    return parser


def main(argv: Optional[List[str]] = None):
    args = build_parser().parse_args(argv)

    if args.json_output:
        checks_ordered = (
            ("unit_tests", run_unit_tests),
            ("json_schemas", validate_json_schemas),
            ("privacy_scan", scan_for_leaks_and_pii),
        )
        results: Dict[str, bool] = {}
        diagnostics: List[str] = []
        for check_key, fn in checks_ordered:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                results[check_key] = bool(fn())
            for raw_line in buf.getvalue().splitlines():
                stripped = raw_line.strip()
                if stripped:
                    diagnostics.append(stripped)

        passed = all(results.values())
        exit_code = 0 if passed else 1
        emit_json_envelope(
            status="PASS" if passed else "FAIL",
            command="check",
            artifacts={"checks": results},
            diagnostics=diagnostics,
            exit_code=exit_code,
        )
        sys.exit(exit_code)

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
