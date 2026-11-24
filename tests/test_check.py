"""
Tests del guardrail de privacidad scripts/check.py.

Verifican que los patrones prohibidos detectan rutas absolutas reales de
Windows sin generar falsos positivos sobre URLs ni URIs de esquema JSON.
Las muestras se construyen en tiempo de ejecucion para que este propio archivo
no contenga rutas literales que el guardrail deba rechazar.
"""
import re
import shutil
import subprocess
import unittest
import contextlib
import io
import json
import tempfile
from pathlib import Path

from scripts.check import FORBIDDEN_PATTERNS, SCANNED_EXTENSIONS, scan_for_leaks_and_pii, validate_json_schemas

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

    def test_detects_fine_grained_token_aws_key_and_private_key(self):
        # Built at runtime so this file never contains a literal secret.
        for sample in [
            "token = " + "github" + "_pat_" + "A1" * 15,
            "key = " + "AK" + "IA" + "ABCDEFGHIJKLMNOP",
            "-----BEGIN " + "RSA PRIVATE" + " KEY-----",
            "-----BEGIN " + "PRIVATE" + " KEY-----",
        ]:
            with self.subTest(sample=sample[:16]):
                self.assertTrue(_matches(sample))

    def test_scanned_extensions_include_config_and_script_files(self):
        for ext in (".toml", ".env", ".sh", ".xml"):
            self.assertIn(ext, SCANNED_EXTENSIONS)


class TestUntrackedScan(unittest.TestCase):
    def _git(self, root, *args):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)

    def test_untracked_files_are_scanned_and_ignored_files_are_not(self):
        if shutil.which("git") is None:
            self.skipTest("git no disponible")
        secret = "ghp" + "_" + "x" * 24
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._git(root, "init", "-q")
            (root / ".gitignore").write_text("ignored/\n", encoding="utf-8")
            (root / "ignored").mkdir()
            (root / "ignored" / "notes.md").write_text(secret, encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(scan_for_leaks_and_pii(root))

            (root / ".env").write_text("TOKEN=" + secret, encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertFalse(scan_for_leaks_and_pii(root))
            self.assertIn(".env", output.getvalue())

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
