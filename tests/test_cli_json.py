"""Tests for uniform --json output envelopes across Harmos CLI entrypoints."""
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.compiler.cli_output import ENVELOPE_KEYS
from scripts import audit, check

REPO_ROOT = Path(__file__).resolve().parent.parent
MICRO_MPE_IR = REPO_ROOT / "benchmarks" / "midiControl" / "micro_mpe_ir.json"


class TestCLIJsonEnvelope(unittest.TestCase):
    def _assert_valid_envelope(
        self,
        raw_stdout: str,
        *,
        expected_command: str,
        expected_exit_code: int,
        expected_status: str | None = None,
    ) -> dict:
        data = json.loads(raw_stdout)
        self.assertEqual(set(data.keys()), set(ENVELOPE_KEYS))
        self.assertIsInstance(data["status"], str)
        self.assertIsInstance(data["command"], str)
        self.assertIsInstance(data["artifacts"], dict)
        self.assertIsInstance(data["diagnostics"], list)
        self.assertTrue(all(isinstance(item, str) for item in data["diagnostics"]))
        self.assertIsInstance(data["exit_code"], int)
        self.assertEqual(data["command"], expected_command)
        self.assertEqual(data["exit_code"], expected_exit_code)
        if expected_status is not None:
            self.assertEqual(data["status"], expected_status)
        return data

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "core.compiler.cli", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )

    def test_compiler_cli_compile_json_and_legacy_modes(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_a = Path(tmp) / "a"
            res_a = self._run_cli("--json", "compile", str(MICRO_MPE_IR), "--out", str(out_a), "--no-build")
            self.assertEqual(res_a.returncode, 0, res_a.stderr)
            env_a = self._assert_valid_envelope(
                res_a.stdout,
                expected_command="compile",
                expected_exit_code=0,
                expected_status="PASS",
            )
            self.assertTrue(Path(env_a["artifacts"]["maxpat_path"]).is_file())

            out_b = Path(tmp) / "b"
            res_b = self._run_cli("compile", str(MICRO_MPE_IR), "--out", str(out_b), "--no-build", "--json")
            self.assertEqual(res_b.returncode, 0, res_b.stderr)
            self._assert_valid_envelope(
                res_b.stdout,
                expected_command="compile",
                expected_exit_code=0,
                expected_status="PASS",
            )

            out_c = Path(tmp) / "c"
            res_c = self._run_cli(str(MICRO_MPE_IR), "--out", str(out_c), "--no-build", "--json")
            self.assertEqual(res_c.returncode, 0, res_c.stderr)
            self._assert_valid_envelope(
                res_c.stdout,
                expected_command="compile",
                expected_exit_code=0,
                expected_status="PASS",
            )

            out_d = Path(tmp) / "d"
            res_d = self._run_cli("--json", str(MICRO_MPE_IR), "--out", str(out_d), "--no-build")
            self.assertEqual(res_d.returncode, 0, res_d.stderr)
            self._assert_valid_envelope(
                res_d.stdout,
                expected_command="compile",
                expected_exit_code=0,
                expected_status="PASS",
            )

            out_plain = Path(tmp) / "plain"
            res_plain = self._run_cli(str(MICRO_MPE_IR), "--out", str(out_plain), "--no-build")
            self.assertEqual(res_plain.returncode, 0, res_plain.stderr)
            self.assertIn("Compilacion exitosa para:", res_plain.stdout)

    def test_compiler_cli_extract_doc_and_provenance_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            ts_file = Path(tmp) / "GainMeter.ts"
            ts_file.write_text(
                "export class GainMeter {\n  process(x: number): number { return x; }\n}\n",
                encoding="utf-8",
            )
            extracted_ir = Path(tmp) / "gain_meter.ir.json"
            res_extract = self._run_cli(
                "extract", str(ts_file), "--out", str(extracted_ir), "--name", "harmos.test_gain", "--json"
            )
            self.assertEqual(res_extract.returncode, 0, res_extract.stderr)
            env_extract = self._assert_valid_envelope(
                res_extract.stdout,
                expected_command="extract",
                expected_exit_code=0,
                expected_status="PASS",
            )
            self.assertEqual(env_extract["artifacts"]["object_name"], "harmos.test_gain")
            self.assertTrue(Path(env_extract["artifacts"]["ir_path"]).is_file())

            doc_out = Path(tmp) / "micro_mpe.maxref.xml"
            res_doc = self._run_cli("doc", str(MICRO_MPE_IR), "--out", str(doc_out), "--json")
            self.assertEqual(res_doc.returncode, 0, res_doc.stderr)
            env_doc = self._assert_valid_envelope(
                res_doc.stdout,
                expected_command="doc",
                expected_exit_code=0,
                expected_status="PASS",
            )
            self.assertTrue(Path(env_doc["artifacts"]["maxref_path"]).is_file())

            pkg_dir = Path(tmp) / "pkg"
            res_compile = self._run_cli("compile", str(MICRO_MPE_IR), "--out", str(pkg_dir), "--no-build", "--json")
            self.assertEqual(res_compile.returncode, 0, res_compile.stderr)

            res_prov_ok = self._run_cli("verify-provenance", str(pkg_dir), "--json")
            self.assertEqual(res_prov_ok.returncode, 0, res_prov_ok.stderr)
            self._assert_valid_envelope(
                res_prov_ok.stdout,
                expected_command="verify-provenance",
                expected_exit_code=0,
                expected_status="VALID",
            )

            empty_dir = Path(tmp) / "empty"
            empty_dir.mkdir()
            res_prov_bad = self._run_cli("verify-provenance", str(empty_dir), "--json")
            self.assertEqual(res_prov_bad.returncode, 1)
            env_bad = self._assert_valid_envelope(
                res_prov_bad.stdout,
                expected_command="verify-provenance",
                expected_exit_code=1,
            )
            self.assertTrue(len(env_bad["diagnostics"]) > 0)

    def test_compiler_cli_harvest_diff_bench_and_error_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases_file = Path(tmp) / "truax.jsonl"
            res_harvest = self._run_cli("harvest", "--suite", "truax", "--out", str(cases_file), "--json")
            self.assertEqual(res_harvest.returncode, 0, res_harvest.stderr)
            env_harvest = self._assert_valid_envelope(
                res_harvest.stdout,
                expected_command="harvest",
                expected_exit_code=0,
                expected_status="PASS",
            )
            self.assertGreater(env_harvest["artifacts"]["case_count"], 0)

            res_diff = self._run_cli("diff", str(cases_file), "--suite", "truax", "--json")
            self.assertEqual(res_diff.returncode, 0, res_diff.stderr)
            self._assert_valid_envelope(
                res_diff.stdout,
                expected_command="diff",
                expected_exit_code=0,
                expected_status="PASS",
            )

            res_bench = self._run_cli("bench", "--suite", "truax", "--json")
            self.assertIn(res_bench.returncode, (0, 1))
            expected_status = "SHIP" if res_bench.returncode == 0 else "NO_SHIP"
            env_bench = self._assert_valid_envelope(
                res_bench.stdout,
                expected_command="bench",
                expected_exit_code=res_bench.returncode,
                expected_status=expected_status,
            )
            self.assertIsInstance(env_bench["artifacts"]["results"], list)
            self.assertGreater(len(env_bench["artifacts"]["results"]), 0)

            missing_ir = Path(tmp) / "nonexistent.ir.json"
            res_err = self._run_cli("compile", str(missing_ir), "--json")
            self.assertEqual(res_err.returncode, 1)
            env_err = self._assert_valid_envelope(
                res_err.stdout,
                expected_command="compile",
                expected_exit_code=1,
                expected_status="ERROR",
            )
            self.assertGreater(len(env_err["diagnostics"]), 0)

    def test_audit_cli_json_verdicts_purity_and_legacy_banner(self):
        for verdict, expected_exit in [
            ("PASS", 0),
            ("BLOCKED", 2),
            ("FAIL", 1),
            ("INVALID", 1),
        ]:
            with self.subTest(verdict=verdict):
                def _fake_audit(*args, **kwargs):
                    print("[*] Binario Max detectado: simulated")
                    return verdict, [f"detail for {verdict}"]

                stdout = io.StringIO()
                with mock.patch.object(audit, "audit_patcher_live", side_effect=_fake_audit), \
                        contextlib.redirect_stdout(stdout):
                    with self.assertRaises(SystemExit) as ctx:
                        audit.main(["--patcher", "demo.maxpat", "--json"])

                self.assertEqual(ctx.exception.code, expected_exit)
                env = self._assert_valid_envelope(
                    stdout.getvalue(),
                    expected_command="audit",
                    expected_exit_code=expected_exit,
                    expected_status=verdict,
                )
                self.assertEqual(env["artifacts"]["patcher"], "demo.maxpat")
                self.assertEqual(env["diagnostics"], [f"detail for {verdict}"])

        plain_stdout = io.StringIO()
        with mock.patch.object(audit, "audit_patcher_live", return_value=("PASS", ["ok"])), \
                contextlib.redirect_stdout(plain_stdout):
            with self.assertRaises(SystemExit) as ctx:
                audit.main(["--patcher", "demo.maxpat"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertIn("HARMOS LIVE AUDIT: PASS", plain_stdout.getvalue())

    def test_check_cli_json_and_legacy_text_without_recursion(self):
        stdout_ok = io.StringIO()
        with mock.patch.object(check, "run_unit_tests", return_value=True), \
                mock.patch.object(check, "validate_json_schemas", return_value=True), \
                mock.patch.object(check, "scan_for_leaks_and_pii", return_value=True), \
                mock.patch.object(check, "verify_generated_skill", return_value=True), \
                contextlib.redirect_stdout(stdout_ok):
            with self.assertRaises(SystemExit) as ctx_ok:
                check.main(["--json"])

        self.assertEqual(ctx_ok.exception.code, 0)
        env_ok = self._assert_valid_envelope(
            stdout_ok.getvalue(),
            expected_command="check",
            expected_exit_code=0,
            expected_status="PASS",
        )
        self.assertEqual(
            env_ok["artifacts"]["checks"],
            {
                "unit_tests": True,
                "json_schemas": True,
                "privacy_scan": True,
                "skill_sync": True,
            },
        )

        def _failing_privacy(*args, **kwargs):
            print("  FAIL FUGA DETECTADA en x.md:1: Ruta")
            return False

        stdout_fail = io.StringIO()
        with mock.patch.object(check, "run_unit_tests", return_value=True), \
                mock.patch.object(check, "validate_json_schemas", return_value=True), \
                mock.patch.object(check, "scan_for_leaks_and_pii", side_effect=_failing_privacy), \
                mock.patch.object(check, "verify_generated_skill", return_value=True), \
                contextlib.redirect_stdout(stdout_fail):
            with self.assertRaises(SystemExit) as ctx_fail:
                check.main(["--json"])

        self.assertEqual(ctx_fail.exception.code, 1)
        env_fail = self._assert_valid_envelope(
            stdout_fail.getvalue(),
            expected_command="check",
            expected_exit_code=1,
            expected_status="FAIL",
        )
        self.assertFalse(env_fail["artifacts"]["checks"]["privacy_scan"])
        self.assertTrue(any("FAIL FUGA DETECTADA" in d for d in env_fail["diagnostics"]))

        stdout_plain = io.StringIO()
        with mock.patch.object(check, "run_unit_tests", return_value=True), \
                mock.patch.object(check, "validate_json_schemas", return_value=True), \
                mock.patch.object(check, "scan_for_leaks_and_pii", return_value=True), \
                mock.patch.object(check, "verify_generated_skill", return_value=True), \
                contextlib.redirect_stdout(stdout_plain):
            with self.assertRaises(SystemExit) as ctx_plain:
                check.main([])
        self.assertEqual(ctx_plain.exception.code, 0)
        self.assertIn("ESTADO: VERIFICACION APROBADA (PASS)", stdout_plain.getvalue())


if __name__ == "__main__":
    unittest.main()
