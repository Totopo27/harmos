"""
Tests unitarios para el sistema de huella criptográfica de procedencia (core/compiler/provenance.py).
Inspirado en el estándar de procedencia de rust-anything.
"""
import unittest
import tempfile
import json
import hashlib
import subprocess
import sys
import typing
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


class TestProvenanceFailsClosed(unittest.TestCase):
    """Unverifiable evidence must never be reported as VALID."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.test_dir.name)

        self.dummy_ir = self.dir_path / "dummy.ir.json"
        with open(self.dummy_ir, "w", encoding="utf-8") as f:
            json.dump({
                "object_name": "test_object",
                "category": "control",
                "inlets": [{"id": 0, "type": "float", "description": "In"}],
                "outlets": [{"id": 0, "type": "float", "description": "Out"}]
            }, f, indent=4)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_unverifiable_when_contracts_unreachable(self):
        record = build_provenance_record(self.dummy_ir)
        prov_file = write_provenance_file(self.dir_path, record)

        verdict, details = verify_provenance(
            prov_file, current_contracts_path=self.dir_path / "ausente.json"
        )
        self.assertEqual(verdict, "UNVERIFIABLE")
        self.assertTrue(any("contratos" in d.lower() for d in details))

    def test_unverifiable_when_contracts_in_record_without_hash(self):
        record = build_provenance_record(self.dummy_ir)
        record["contracts"] = {"file": "max_contracts.json"}
        prov_file = write_provenance_file(self.dir_path, record)

        verdict, _ = verify_provenance(prov_file)
        self.assertEqual(verdict, "UNVERIFIABLE")

    def test_unverifiable_when_current_ir_missing(self):
        record = build_provenance_record(self.dummy_ir)
        prov_file = write_provenance_file(self.dir_path, record)

        verdict, details = verify_provenance(
            prov_file, current_ir_path=self.dir_path / "fantasma.ir.json"
        )
        self.assertEqual(verdict, "UNVERIFIABLE")
        self.assertTrue(any("no encontrado" in d.lower() for d in details))

    def test_unverifiable_when_record_lacks_ir_but_ir_requested(self):
        record = build_provenance_record(self.dummy_ir)
        record.pop("ir")
        prov_file = write_provenance_file(self.dir_path, record)

        verdict, details = verify_provenance(prov_file, current_ir_path=self.dummy_ir)
        self.assertEqual(verdict, "UNVERIFIABLE")
        self.assertFalse(any(d.startswith("IR OK") for d in details))

    def test_unverifiable_when_current_source_missing(self):
        source = self.dir_path / "svc.ts"
        source.write_text("// v1\n", encoding="utf-8")
        record = build_provenance_record(self.dummy_ir, source_path=source)
        prov_file = write_provenance_file(self.dir_path, record)
        source.unlink()

        verdict, _ = verify_provenance(prov_file, current_source_path=source)
        self.assertEqual(verdict, "UNVERIFIABLE")

    def test_detect_stale_artifacts(self):
        out_dir = self.dir_path / "pkg"
        res = compile_ir(str(self.dummy_ir), str(out_dir))
        maxpat = Path(res["maxpat_path"])
        maxpat.write_bytes(maxpat.read_bytes() + b"\n")

        verdict, details = verify_provenance(res["provenance_path"])
        self.assertEqual(verdict, "STALE_ARTIFACTS")
        self.assertTrue(any("maxpat" in d for d in details))

    def test_unverifiable_when_recorded_artifact_missing(self):
        out_dir = self.dir_path / "pkg"
        res = compile_ir(str(self.dummy_ir), str(out_dir))
        Path(res["cpp_path"]).unlink()

        verdict, _ = verify_provenance(res["provenance_path"])
        self.assertEqual(verdict, "UNVERIFIABLE")

    def test_compile_records_artifact_hashes(self):
        out_dir = self.dir_path / "pkg"
        res = compile_ir(str(self.dummy_ir), str(out_dir))

        with open(res["provenance_path"], "r", encoding="utf-8") as f:
            record = json.load(f)

        self.assertIn("artifacts", record)
        for key in ("maxpat", "cpp", "cmake"):
            self.assertIn(key, record["artifacts"])
            self.assertEqual(len(record["artifacts"][key]["sha256"]), 64)

    def test_legacy_record_without_artifacts_is_disclosed(self):
        record = build_provenance_record(self.dummy_ir)
        prov_file = write_provenance_file(self.dir_path, record)

        verdict, details = verify_provenance(prov_file)
        self.assertEqual(verdict, "VALID")
        self.assertTrue(any("sin huella de artefactos" in d.lower() for d in details))

    def test_unverifiable_when_contracts_path_is_directory(self):
        record = build_provenance_record(self.dummy_ir)
        prov_file = write_provenance_file(self.dir_path, record)

        verdict, _ = verify_provenance(prov_file, current_contracts_path=self.dir_path)
        self.assertEqual(verdict, "UNVERIFIABLE")

    def test_unverifiable_when_record_lacks_contracts_section(self):
        record = build_provenance_record(self.dummy_ir)
        record.pop("contracts")
        prov_file = write_provenance_file(self.dir_path, record)

        verdict, _ = verify_provenance(prov_file)
        self.assertEqual(verdict, "UNVERIFIABLE")

    def test_detect_stale_cmake(self):
        out_dir = self.dir_path / "pkg"
        res = compile_ir(str(self.dummy_ir), str(out_dir))
        Path(res["cmake_path"]).write_text("tampered\n", encoding="utf-8")

        verdict, _ = verify_provenance(res["provenance_path"])
        self.assertEqual(verdict, "STALE_ARTIFACTS")

    def test_unverifiable_when_artifact_entry_incomplete(self):
        record = build_provenance_record(self.dummy_ir)
        record["artifacts"] = {"maxpat": {"sha256": "a" * 64}}
        prov_file = write_provenance_file(self.dir_path, record)

        verdict, _ = verify_provenance(prov_file)
        self.assertEqual(verdict, "UNVERIFIABLE")

    def test_invalid_when_record_sections_are_not_objects(self):
        for section in ("contracts", "ir", "source", "artifacts"):
            with self.subTest(section=section):
                record = build_provenance_record(self.dummy_ir)
                record[section] = ["not", "an", "object"]
                prov_file = write_provenance_file(self.dir_path / section, record)

                verdict, details = verify_provenance(prov_file)
                self.assertEqual(verdict, "INVALID")
                self.assertTrue(any(section in d for d in details))

    def test_invalid_when_record_root_is_not_object(self):
        target = self.dir_path / "root_list"
        target.mkdir()
        (target / "emitted-from.json").write_text("[]", encoding="utf-8")

        self.assertEqual(verify_provenance(target)[0], "INVALID")

    def test_invalid_when_record_corrupt_or_missing(self):
        corrupt_dir = self.dir_path / "corrupt"
        corrupt_dir.mkdir()
        (corrupt_dir / "emitted-from.json").write_text("{oops", encoding="utf-8")
        self.assertEqual(verify_provenance(corrupt_dir)[0], "INVALID")

        empty_dir = self.dir_path / "empty"
        empty_dir.mkdir()
        self.assertEqual(verify_provenance(empty_dir)[0], "INVALID")

    def test_rejected_verification_is_read_only(self):
        out_dir = self.dir_path / "pkg"
        res = compile_ir(str(self.dummy_ir), str(out_dir))
        maxpat = Path(res["maxpat_path"])
        maxpat.write_bytes(maxpat.read_bytes() + b"\x00")

        def tree_digest(root):
            digest = hashlib.sha256()
            for path in sorted(Path(root).rglob("*")):
                digest.update(str(path.relative_to(root)).encode("utf-8"))
                if path.is_file():
                    digest.update(path.read_bytes())
            return digest.hexdigest()

        before = tree_digest(out_dir)
        verdict, _ = verify_provenance(res["provenance_path"])
        self.assertEqual(verdict, "STALE_ARTIFACTS")
        self.assertEqual(before, tree_digest(out_dir))

    def test_cli_exit_codes(self):
        repo_root = Path(__file__).resolve().parent.parent
        out_dir = self.dir_path / "pkg"
        res = compile_ir(str(self.dummy_ir), str(out_dir))

        valid = subprocess.run(
            [sys.executable, "-m", "core.compiler.cli", "verify-provenance", str(out_dir)],
            cwd=repo_root, capture_output=True, text=True
        )
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
        self.assertIn("HARMOS PROVENANCE: VALID", valid.stdout)

        maxpat = Path(res["maxpat_path"])
        maxpat.write_bytes(maxpat.read_bytes() + b"\x00")
        tampered = subprocess.run(
            [sys.executable, "-m", "core.compiler.cli", "verify-provenance", str(out_dir)],
            cwd=repo_root, capture_output=True, text=True
        )
        self.assertEqual(tampered.returncode, 1, tampered.stdout + tampered.stderr)
        self.assertIn("STALE_ARTIFACTS", tampered.stdout)

    def test_cli_annotations_resolve(self):
        hints = typing.get_type_hints(compile_ir)
        self.assertIn("source_path", hints)
        self.assertIn("return", hints)


if __name__ == "__main__":
    unittest.main()
