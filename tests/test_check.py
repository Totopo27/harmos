"""
Tests del guardrail de privacidad scripts/check.py.

Verifican que los patrones prohibidos detectan rutas absolutas reales de
Windows sin generar falsos positivos sobre URLs ni URIs de esquema JSON.
"""
import re
import unittest

from scripts.check import FORBIDDEN_PATTERNS


def _matches(sample):
    return [desc for pattern, desc in FORBIDDEN_PATTERNS if re.search(pattern, sample)]


class TestForbiddenPatterns(unittest.TestCase):
    def test_detects_drive_path_with_backslashes(self):
        self.assertTrue(_matches(r"origen D:\DocumentosDiscoD\harmos\core"))

    def test_detects_drive_path_with_forward_slashes(self):
        self.assertTrue(_matches("origen D:/DocumentosDiscoD/harmos/core"))

    def test_detects_windows_user_profile(self):
        self.assertTrue(_matches(r"C:\Users\alguien\Documents\Max 9"))

    def test_ignores_https_urls(self):
        self.assertEqual(_matches("https://github.com/Cycling74/max-sdk"), [])

    def test_ignores_json_schema_uri(self):
        self.assertEqual(_matches('"$schema": "http://json-schema.org/draft-07/schema#"'), [])


if __name__ == "__main__":
    unittest.main()
