"""
Tests unitarios para el sistema de huella criptográfica de procedencia (core/compiler/provenance.py).
Inspirado en el estándar de procedencia de rust-anything.
"""
import unittest
import tempfile
import json
from pathlib import Path
from core.compiler.provenance import (
    compute_file_sha256,
    build_provenance_record,
    write_provenance_file,
    verify_provenance,
    resolve_canonical_contracts_path
)
from core.compiler.cli import compile_ir


class TestProvenanceEngine(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.test_dir.name)

        # Crear IR dummy
        self.dummy_ir = self.dir_path / "dummy.ir.json"
        self.ir_data = {
            "object_name": "test_object",
            "category": "control",
            "inlets": [{"id": 0, "type": "float", "description": "In"}],
            "outlets": [{"id": 0, "type": "float", "description": "Out"}]
        }
        with open(self.dummy_ir, "w", encoding="utf-8") as f:
            json.dump(self.ir_data, f, indent=4)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_compute_sha256_deterministic(self):
        h1 = compute_file_sha256(self.dummy_ir)
        h2 = compute_file_sha256(self.dummy_ir)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_build_and_write_provenance(self):
        record = build_provenance_record(self.dummy_ir)
        self.assertIn("contracts", record)
        self.assertIn("ir", record)
        self.assertEqual(record["ir"]["file"], "dummy.ir.json")

        out_file = write_provenance_file(self.dir_path, record)
        self.assertTrue(out_file.is_file())
        self.assertEqual(out_file.name, "emitted-from.json")

    def test_verify_valid_provenance(self):
        record = build_provenance_record(self.dummy_ir)
        prov_file = write_provenance_file(self.dir_path, record)

        verdict, details = verify_provenance(prov_file, current_ir_path=self.dummy_ir)
        self.assertEqual(verdict, "VALID")
        self.assertTrue(any("Contratos OK" in d for d in details))

    def test_detect_stale_contracts(self):
        record = build_provenance_record(self.dummy_ir)
        # Simular que el contrato registrado era de una version previa
        record["contracts"]["sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"
        prov_file = write_provenance_file(self.dir_path, record)

        verdict, details = verify_provenance(prov_file)
        self.assertEqual(verdict, "STALE_CONTRACTS")
        self.assertTrue(any("han cambiado" in d for d in details))

    def test_detect_stale_ir(self):
        record = build_provenance_record(self.dummy_ir)
        prov_file = write_provenance_file(self.dir_path, record)

        # Modificar el IR despues de emitido
        with open(self.dummy_ir, "a", encoding="utf-8") as f:
            f.write("\n// cambio arbitrario")

        verdict, details = verify_provenance(prov_file, current_ir_path=self.dummy_ir)
        self.assertEqual(verdict, "STALE_IR")
        self.assertTrue(any("ha sido modificada" in d for d in details))

    def test_compile_ir_generates_provenance(self):
        out_sub = self.dir_path / "compiled_pkg"
        res = compile_ir(str(self.dummy_ir), str(out_sub))

        self.assertTrue(res["success"])
        self.assertIn("provenance_path", res)
        prov_path = Path(res["provenance_path"])
        self.assertTrue(prov_path.is_file())

        # Verificar que el archivo generado sea valido
        verdict, _ = verify_provenance(prov_path)
        self.assertEqual(verdict, "VALID")


if __name__ == "__main__":
    unittest.main()
