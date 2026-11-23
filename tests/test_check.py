"""
Tests del guardrail de privacidad scripts/check.py.

Verifican que los patrones prohibidos detectan rutas absolutas reales de
Windows sin generar falsos positivos sobre URLs ni URIs de esquema JSON.
Las muestras se construyen en tiempo de ejecucion para que este propio archivo
no contenga rutas literales que el guardrail deba rechazar.
"""
import re
import unittest
import contextlib
import io
import json
import tempfile
from pathlib import Path

from scripts.check import FORBIDDEN_PATTERNS, SCANNED_EXTENSIONS, validate_json_schemas

BACKSLASH = "\\"
FORWARD_SLASH = "/"


def _matches(sample):
    return [desc for pattern, desc in FORBIDDEN_PATTERNS if re.search(pattern, sample)]


def _windows_path(drive, *parts):
    return drive + ":" + BACKSLASH + BACKSLASH.join(parts)


def _windows_path_forward(drive, *parts):
    return drive + ":" + FORWARD_SLASH + FORWARD_SLASH.join(parts)


class TestForbiddenPatterns(unittest.TestCase):
    def test_detects_drive_path_with_backslashes(self):
        self.assertTrue(_matches("origen " + _windows_path("D", "proyecto", "core")))

    def test_detects_drive_path_with_forward_slashes(self):
        self.assertTrue(_matches("origen " + _windows_path_forward("D", "proyecto", "core")))

    def test_detects_windows_user_profile(self):
        self.assertTrue(_matches(_windows_path("C", "Users", "alguien", "Documents")))

    def test_ignores_https_urls(self):
        self.assertEqual(_matches("https://github.com/Cycling74/max-sdk"), [])

    def test_ignores_json_schema_uri(self):
        self.assertEqual(_matches('"$schema": "http://json-schema.org/draft-07/schema#"'), [])

    def test_scanned_extensions_include_yaml(self):
        self.assertIn(".yml", SCANNED_EXTENSIONS)
        self.assertIn(".yaml", SCANNED_EXTENSIONS)

    def test_detects_macos_user_profile(self):
        sample = "export PATH=" + FORWARD_SLASH + "Users" + FORWARD_SLASH + "developer" + FORWARD_SLASH + "bin"
        self.assertTrue(_matches(sample))

class TestContractStructureCheck(unittest.TestCase):
    def test_parseable_json_is_not_sufficient_contract_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = root / "max_contracts.json"
            for data, expected in [
                ({}, False),
                ({"objects": {"demo": {"inlets": [], "outlets": [{"name": "out", "type": "OUTLET_TYPE"}]}}}, False),
                ({"objects": {"demo": {"inlets": [], "outlets": [{"name": "out", "type": ["float", "list"]}]}}}, True),
            ]:
                with self.subTest(data=data):
                    catalog.write_text(json.dumps(data), encoding="utf-8")
                    before = catalog.read_bytes()
                    output = io.StringIO()
                    with contextlib.redirect_stdout(output):
                        self.assertEqual(expected, validate_json_schemas(root))
                    self.assertEqual(before, catalog.read_bytes())
                    self.assertIn("JSON", output.getvalue())
                    self.assertIn("estructura", output.getvalue().lower())
            catalog.write_text("{", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertFalse(validate_json_schemas(root))
            catalog.unlink()
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertFalse(validate_json_schemas(root))


if __name__ == "__main__":
    unittest.main()
