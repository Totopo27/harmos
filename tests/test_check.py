"""
Tests del guardrail de privacidad scripts/check.py.

Verifican que los patrones prohibidos detectan rutas absolutas reales de
Windows sin generar falsos positivos sobre URLs ni URIs de esquema JSON.
Las muestras se construyen en tiempo de ejecucion para que este propio archivo
no contenga rutas literales que el guardrail deba rechazar.
"""
import re
import unittest

from scripts.check import FORBIDDEN_PATTERNS

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


if __name__ == "__main__":
    unittest.main()
