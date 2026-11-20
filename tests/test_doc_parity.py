"""
Tests de paridad documental entre las especificaciones (docs/ORACULO_LIMITES.md)
y el codigo ejecutable que emite los veredictos (scripts/audit.py, core/compiler/provenance.py).

Garantiza honestidad epistemica: ningun veredicto o garantia documentada puede existir
en la taxonomia sin corresponder a un literal exacto en el codigo que lo emite.
"""
import ast
import re
import unittest
from pathlib import Path

from scripts import audit

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = REPO_ROOT / "docs" / "ORACULO_LIMITES.md"
AUDIT_SCRIPT_PATH = REPO_ROOT / "scripts" / "audit.py"


def extract_verdict_tokens_from_doc(doc_path: Path) -> list:
    """
    Extrae los tokens de veredicto definidos en la tabla de taxonomia de ORACULO_LIMITES.md (§4).
    """
    content = doc_path.read_text(encoding="utf-8")
    # Aislar la seccion 4 (Taxonomia de Veredictos del Sistema)
    match = re.search(r"## 4\.\s+Taxonom[ií]a de Veredictos del Sistema.*?(?=\n## |\Z)", content, re.DOTALL)
    if not match:
        raise ValueError(f"No se encontro la seccion de taxonomia en {doc_path}")

    section_text = match.group(0)
    lines = [
        line.strip()
        for line in section_text.splitlines()
        if line.strip().startswith("|")
        and not line.strip().startswith("| :---")
        and not line.strip().startswith("| Veredicto")
    ]

    tokens = []
    for line in lines:
        parts = line.split("|")
        if len(parts) < 2:
            continue
        first_cell = parts[1].strip()
        found = re.findall(r"`([^`]+)`", first_cell)
        tokens.extend(found)

    return tokens


def get_string_literals_from_python_file(file_path: Path) -> set:
    """
    Parsea un archivo Python con AST y extrae todos los literales de cadena constantes.
    """
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))
    literals = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            literals.add(node.value)
    return literals


class TestDocParity(unittest.TestCase):
    def test_doc_file_exists(self):
        self.assertTrue(DOC_PATH.is_file(), f"Documento no encontrado: {DOC_PATH}")

    def test_taxonomy_verdict_tokens_match_emitting_code_literals(self):
        """
        Cada token de veredicto documentado en ORACULO_LIMITES.md (§4)
        debe aparecer como un literal exacto en scripts/audit.py.
        """
        doc_tokens = extract_verdict_tokens_from_doc(DOC_PATH)
        self.assertGreater(len(doc_tokens), 0, "No se extrajeron tokens de la taxonomia documental.")

        code_literals = get_string_literals_from_python_file(AUDIT_SCRIPT_PATH)

        missing_tokens = []
        for token in doc_tokens:
            if token not in code_literals:
                missing_tokens.append(token)

        self.assertEqual(
            missing_tokens,
            [],
            f"Tokens de veredicto documentados en ORACULO_LIMITES.md que no existen "
            f"como literales en scripts/audit.py: {missing_tokens}",
        )

    def test_coverage_limitation_clause_references_actual_fail_patterns(self):
        """
        El limite de cobertura documentado en §3 debe referenciar estructuras
        reales existentes en scripts/audit.py.
        """
        doc_content = DOC_PATH.read_text(encoding="utf-8")
        self.assertIn("FAIL_PATTERNS", doc_content)
        self.assertTrue(hasattr(audit, "FAIL_PATTERNS"))
        self.assertIsInstance(audit.FAIL_PATTERNS, list)
        self.assertGreater(len(audit.FAIL_PATTERNS), 0)
        for pattern in audit.FAIL_PATTERNS:
            self.assertIsInstance(pattern, str)
            self.assertTrue(len(pattern) > 0)


if __name__ == "__main__":
    unittest.main()
