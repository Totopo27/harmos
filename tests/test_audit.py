"""
Tests unitarios para el modulo de auditoria en vivo scripts/audit.py.
Verifica lectura binaria, aislamiento por centinela y descarte de falsos positivos CRLF.
"""
import unittest
import tempfile
from pathlib import Path
from scripts.audit import read_log_delta_binary, FAIL_PATTERNS, audit_patcher_live


class TestAuditPatcherLive(unittest.TestCase):
    def test_missing_patcher_returns_fail(self):
        bogus_path = Path("non_existent_patcher_xyz.maxpat")
        verdict, details = audit_patcher_live(bogus_path)
        self.assertEqual(verdict, "FAIL")
        self.assertTrue(any("no existe" in d for d in details))

    def test_binary_crlf_read_delta_integrity(self):
        """Verifica que leer offsets en modo binario con saltos CRLF (\\r\\n) no desalinea lineas."""
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            temp_path = Path(f.name)
            initial_content = b"Linea previa 1\r\nLinea previa 2\r\n"
            f.write(initial_content)

        try:
            offset_before = temp_path.stat().st_size

            # Simular escrituras durante la ejecucion de Max
            with open(temp_path, "ab") as f:
                f.write(b"Nueva linea 1 de Max\r\nNueva linea 2 de Max\r\n")

            new_lines = read_log_delta_binary(temp_path, offset_before)
            self.assertEqual(len(new_lines), 2)
            self.assertEqual(new_lines[0], "Nueva linea 1 de Max")
            self.assertEqual(new_lines[1], "Nueva linea 2 de Max")
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_sentinel_marker_isolation(self):
        """Verifica que solo se extraen lineas posteriores al centinela inyectado."""
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            temp_path = Path(f.name)
            # Ruido previo historico
            f.write(b"Log viejo de otra sesion\r\nerror: fallo viejo ignorado\r\n")

        try:
            sentinel = b"=== HARMOS_AUDIT_SENTINEL_abc123 ==="
            with open(temp_path, "ab") as f:
                f.write(b"\r\n" + sentinel + b"\r\n")
                f.write(b"Sesion limpia actual 1\r\nSesion limpia actual 2\r\n")

            new_lines = read_log_delta_binary(temp_path, 0, sentinel_bytes=sentinel)
            self.assertEqual(len(new_lines), 2)
            self.assertEqual(new_lines[0], "Sesion limpia actual 1")
            self.assertEqual(new_lines[1], "Sesion limpia actual 2")
            # El error viejo fue ignorado porque precedia al centinela
            self.assertFalse(any("error" in line.lower() for line in new_lines))
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_fail_patterns_detection_in_delta(self):
        """Verifica que los patrones criticos de fallo sean detectados."""
        sample_errors = [
            "midiformat: doesn't match type",
            "poly~: fatal: access violation at address 0x00",
            "unable to create: no such object"
        ]
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            temp_path = Path(f.name)
            for err in sample_errors:
                f.write(f"{err}\r\n".encode("utf-8"))

        try:
            lines = read_log_delta_binary(temp_path, 0)
            detected = []
            for line in lines:
                for pattern in FAIL_PATTERNS:
                    if pattern in line.lower():
                        detected.append(line)
                        break
            self.assertEqual(len(detected), 3)
        finally:
            if temp_path.exists():
                temp_path.unlink()


if __name__ == "__main__":
    unittest.main()
