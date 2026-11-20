"""
Tests unitarios y de integracion para el verificador en vivo scripts/audit.py.

Cubren el contrato de aislamiento por sesion de log (Max trunca Max.log en cada
arranque), la deteccion estructural de errores y el caracter fail-closed del
veredicto: una sesion vacia o sin fin de carga nunca puede producir PASS.
"""
import unittest
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

from core.compiler.cli import compile_ir
from scripts import audit
from scripts.audit import (
    audit_patcher_live,
    audit_provenance,
    evaluate_session,
    load_session_lines,
    parse_log_line,
)


def _line(level="info", message="linea", when=None, pid=4242):
    when = when or datetime.now()
    stamp = when.strftime("%Y-%m-%d %H:%M:%S.%f")
    return f"[{stamp} {level}] [{pid}] {message}"


def _session(when=None, pid=4242, extra=None):
    lines = [
        _line("info", "max logging initialized: logging to logs", when, pid),
        _line("info", "Max is starting: Version 9.1.5", when, pid),
    ]
    lines.extend(extra or [])
    lines.append(_line("info", "<- startup_load(max-startup): 11.677", when, pid))
    return lines


class LogFixtureMixin:
    def make_log(self, lines):
        handle = tempfile.NamedTemporaryFile("w", suffix=".log", delete=False, encoding="utf-8")
        handle.write("\n".join(lines) + "\n")
        handle.close()
        path = Path(handle.name)
        self.addCleanup(lambda: path.unlink() if path.exists() else None)
        return path


class TestLogParsing(LogFixtureMixin, unittest.TestCase):
    def test_parse_log_line_extracts_level_and_message(self):
        parsed = parse_log_line(_line("error", "harmos_x~: No such object"))
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["level"], "error")
        self.assertEqual(parsed["message"], "harmos_x~: No such object")

    def test_parse_log_line_rejects_non_canonical_text(self):
        self.assertIsNone(parse_log_line("Max is starting up"))


class TestSessionIsolation(LogFixtureMixin, unittest.TestCase):
    def test_session_starts_at_last_header(self):
        """Los errores de una sesion previa no contaminan la sesion actual."""
        header_nueva = _line("info", "max logging initialized: sesion nueva")
        log = self.make_log(
            [
                _line("info", "max logging initialized: sesion vieja"),
                _line("error", "harmos_viejo~: No such object"),
                header_nueva,
                _line("info", "Max is starting"),
            ]
        )
        launched_after = datetime.now().timestamp() - 5

        lines = load_session_lines(log, launched_after)

        self.assertIsNotNone(lines)
        self.assertEqual(lines[0], header_nueva)
        self.assertFalse(any("viejo" in line for line in lines))

    def test_truncated_log_is_read_from_scratch(self):
        """Regresion: Max trunca el log; un offset previo no debe vaciar la lectura."""
        log = self.make_log([_line("error", "sesion anterior con fallos")])
        log.write_text("", encoding="utf-8")
        log.write_text("\n".join(_session(extra=[_line("error", "fallo real")])) + "\n", encoding="utf-8")
        launched_after = datetime.now().timestamp() - 5

        lines = load_session_lines(log, launched_after)

        self.assertIsNotNone(lines)
        self.assertTrue(any("fallo real" in line for line in lines))

    def test_stale_log_without_new_session_is_rejected(self):
        old = datetime.now() - timedelta(hours=2)
        log = self.make_log(_session(when=old))
        launched_after = datetime.now().timestamp()

        self.assertIsNone(load_session_lines(log, launched_after))

    def test_log_without_session_header_is_rejected(self):
        log = self.make_log([_line("info", "texto suelto sin header")])
        self.assertIsNone(load_session_lines(log, datetime.now().timestamp() - 5))

    def test_missing_log_file_returns_none(self):
        self.assertIsNone(load_session_lines(Path("no_existe_max.log"), 0.0))


class TestVerdicts(unittest.TestCase):
    def test_error_level_line_fails(self):
        """Formato real de Max 9: `error]` no matchea el viejo patron `error:`."""
        lines = _session(extra=[_line("error", "harmos_nonexistent_object_xyz~: No such object")])
        verdict, details = evaluate_session(lines)
        self.assertEqual(verdict, "FAIL")
        self.assertTrue(any("No such object" in d for d in details))

    def test_missing_abstraction_fails(self):
        lines = _session(extra=[_line("error", "no patcher harmos_missing.maxpat")])
        verdict, _ = evaluate_session(lines)
        self.assertEqual(verdict, "FAIL")

    def test_missing_abstraction_pattern_fails_even_at_info_level(self):
        lines = _session(extra=[_line("info", "no patcher harmos_missing.maxpat")])
        verdict, _ = evaluate_session(lines)
        self.assertEqual(verdict, "FAIL")

    def test_incomplete_session_is_blocked_never_pass(self):
        """Regresion nuclear: sin fin de carga no hay evidencia para PASS."""
        lines = [_line("info", "max logging initialized"), _line("info", "Max is starting")]
        verdict, details = evaluate_session(lines)
        self.assertEqual(verdict, "BLOCKED")
        self.assertTrue(any("startup_load" in d for d in details))

    def test_empty_session_is_blocked(self):
        verdict, _ = evaluate_session([])
        self.assertEqual(verdict, "BLOCKED")

    def test_completed_clean_session_passes(self):
        verdict, details = evaluate_session(_session())
        self.assertEqual(verdict, "PASS")
        self.assertTrue(any("No certifica equivalencia DSP" in d for d in details))

    def test_crash_recovery_notice_does_not_fail(self):
        lines = _session(extra=[_line("info", "maxworkspace_restore: looks like prior Max run crashed")])
        verdict, details = evaluate_session(lines)
        self.assertEqual(verdict, "PASS")
        self.assertTrue(any("workspace" in d.lower() for d in details))


class FakeProc:
    """Proceso falso que escribe una sesion sintetica de Max.log al arrancar."""

    def __init__(self, log_path, lines):
        if lines is not None:
            Path(log_path).write_text("\n".join(lines) + "\n", encoding="utf-8")

    def poll(self):
        return None

    def terminate(self):
        pass

    def wait(self, timeout=None):
        return 0

    def kill(self):
        pass


class TestAuditPatcherLive(LogFixtureMixin, unittest.TestCase):
    def _run(self, lines, timeout=3):
        patcher = Path(self.id().replace(".", "_") + ".maxpat")
        handle = tempfile.NamedTemporaryFile("w", suffix=".maxpat", delete=False, encoding="utf-8")
        handle.write("{}")
        handle.close()
        patcher = Path(handle.name)
        self.addCleanup(lambda: patcher.unlink() if patcher.exists() else None)

        log = self.make_log([])

        with mock.patch.object(audit, "resolve_max_executable", return_value=Path("Max.exe")), \
                mock.patch.object(audit, "resolve_max_log_path", return_value=log), \
                mock.patch.object(audit, "SETTLE_SECONDS", 0.01), \
                mock.patch.object(audit.subprocess, "Popen", side_effect=lambda *a, **k: FakeProc(log, lines)):
            return audit_patcher_live(patcher, timeout_seconds=timeout)

    def test_missing_patcher_returns_fail(self):
        verdict, details = audit_patcher_live(Path("non_existent_patcher_xyz.maxpat"))
        self.assertEqual(verdict, "FAIL")
        self.assertTrue(any("no existe" in d for d in details))

    def test_non_maxpat_target_is_rejected(self):
        handle = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8")
        handle.write("print('hola')")
        handle.close()
        target = Path(handle.name)
        self.addCleanup(lambda: target.unlink() if target.exists() else None)

        verdict, details = audit_patcher_live(target)

        self.assertEqual(verdict, "FAIL")
        self.assertTrue(any(".maxpat" in d for d in details))

    def test_blocked_when_max_is_unavailable(self):
        handle = tempfile.NamedTemporaryFile("w", suffix=".maxpat", delete=False, encoding="utf-8")
        handle.write("{}")
        handle.close()
        target = Path(handle.name)
        self.addCleanup(lambda: target.unlink() if target.exists() else None)

        with mock.patch.object(audit, "resolve_max_executable", return_value=None):
            verdict, details = audit_patcher_live(target)

        self.assertEqual(verdict, "BLOCKED")
        self.assertTrue(any("Max.exe no fue detectado" in d for d in details))

    def test_live_audit_passes_on_completed_synthetic_session(self):
        verdict, _ = self._run(_session())
        self.assertEqual(verdict, "PASS")

    def test_live_audit_fails_on_synthetic_error_session(self):
        verdict, _ = self._run(_session(extra=[_line("error", "no patcher harmos_missing.maxpat")]))
        self.assertEqual(verdict, "FAIL")

    def test_live_audit_never_passes_without_a_session(self):
        """Regresion: Max arranca pero no escribe log -> BLOCKED, jamas PASS."""
        verdict, details = self._run(None, timeout=1)
        self.assertEqual(verdict, "BLOCKED")
        self.assertTrue(any("sesion de Max.log" in d for d in details))

    def test_relative_patcher_path_is_resolved_before_launch(self):
        """Regresion: Max no abre rutas relativas; el verifier debe absolutizarlas."""
        captured = {}
        cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "rel.maxpat").write_text("{}", encoding="utf-8")
            log = self.make_log(_session())

            def fake_popen(argv, *args, **kwargs):
                captured["argv"] = list(argv)
                return FakeProc(log, None)

            os.chdir(tmp)
            try:
                with mock.patch.object(audit, "resolve_max_executable", return_value=Path("Max.exe")), \
                        mock.patch.object(audit, "resolve_max_log_path", return_value=log), \
                        mock.patch.object(audit, "SETTLE_SECONDS", 0.01), \
                        mock.patch.object(audit.subprocess, "Popen", side_effect=fake_popen):
                    audit_patcher_live(Path("rel.maxpat"), timeout_seconds=3)
            finally:
                os.chdir(cwd)

        self.assertTrue(Path(captured["argv"][1]).is_absolute())


class TestProvenanceGate(LogFixtureMixin, unittest.TestCase):
    """La procedencia se certifica dentro del audit: un paquete obsoleto nunca obtiene PASS."""

    def _compile_package(self, object_name="prov_obj"):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        ir = root / f"{object_name}.ir.json"
        ir.write_text(
            json.dumps(
                {
                    "object_name": object_name,
                    "category": "control",
                    "inlets": [{"id": 0, "type": "float", "description": "In"}],
                    "outlets": [{"id": 0, "type": "float", "description": "Out"}],
                },
                indent=4,
            ),
            encoding="utf-8",
        )
        return compile_ir(str(ir), str(root / "pkg"))

    def _audit_without_runtime(self, patcher):
        """El veredicto de procedencia debe decidirse antes de arrancar Max."""
        with mock.patch.object(audit, "resolve_max_executable", return_value=Path("Max.exe")), \
                mock.patch.object(
                    audit.subprocess, "Popen",
                    side_effect=AssertionError("Max.exe no debe lanzarse con procedencia rechazada"),
                ):
            return audit_patcher_live(patcher, timeout_seconds=1)

    def test_package_without_provenance_record_is_not_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            patcher = Path(tmp, "suelto.maxpat")
            patcher.write_text("{}", encoding="utf-8")

            self.assertEqual((None, []), audit_provenance(patcher))

    def test_tampered_artifact_blocks_before_launching_max(self):
        result = self._compile_package()
        maxpat = Path(result["maxpat_path"])
        maxpat.write_bytes(maxpat.read_bytes() + b"\x00")

        verdict, details = self._audit_without_runtime(maxpat)

        self.assertEqual("STALE_ARTIFACTS", verdict)
        self.assertTrue(any("procedencia" in d.lower() for d in details))

    def test_stale_contracts_keeps_its_own_verdict(self):
        result = self._compile_package()
        prov = Path(result["provenance_path"])
        record = json.loads(prov.read_text(encoding="utf-8"))
        record["contracts"]["sha256"] = "0" * 64
        prov.write_text(json.dumps(record, indent=4), encoding="utf-8")

        verdict, _ = self._audit_without_runtime(Path(result["maxpat_path"]))

        self.assertEqual("STALE_CONTRACTS", verdict)

    def test_corrupt_provenance_record_is_invalid(self):
        result = self._compile_package()
        Path(result["provenance_path"]).write_text("{oops", encoding="utf-8")

        verdict, _ = self._audit_without_runtime(Path(result["maxpat_path"]))

        self.assertEqual("INVALID", verdict)

    def test_valid_provenance_is_disclosed_on_pass(self):
        result = self._compile_package()
        patcher = Path(result["maxpat_path"])
        log = self.make_log([])

        with mock.patch.object(audit, "resolve_max_executable", return_value=Path("Max.exe")), \
                mock.patch.object(audit, "resolve_max_log_path", return_value=log), \
                mock.patch.object(audit, "SETTLE_SECONDS", 0.01), \
                mock.patch.object(
                    audit.subprocess, "Popen",
                    side_effect=lambda *a, **k: FakeProc(log, _session()),
                ):
            verdict, details = audit_patcher_live(patcher, timeout_seconds=3)

        self.assertEqual("PASS", verdict)
        self.assertTrue(any("Procedencia verificada" in d for d in details))

    def test_pass_without_record_discloses_uncertified_provenance(self):
        handle = tempfile.NamedTemporaryFile("w", suffix=".maxpat", delete=False, encoding="utf-8")
        handle.write("{}")
        handle.close()
        patcher = Path(handle.name)
        self.addCleanup(lambda: patcher.unlink() if patcher.exists() else None)
        log = self.make_log([])

        with mock.patch.object(audit, "resolve_max_executable", return_value=Path("Max.exe")), \
                mock.patch.object(audit, "resolve_max_log_path", return_value=log), \
                mock.patch.object(audit, "SETTLE_SECONDS", 0.01), \
                mock.patch.object(
                    audit.subprocess, "Popen",
                    side_effect=lambda *a, **k: FakeProc(log, _session()),
                ):
            verdict, details = audit_patcher_live(patcher, timeout_seconds=3)

        self.assertEqual("PASS", verdict)
        self.assertTrue(any("procedencia no fue certificada" in d for d in details))

    def test_provenance_verdict_maps_to_nonzero_exit(self):
        with mock.patch.object(sys, "argv", ["audit.py", "--patcher", "x.maxpat"]), \
                mock.patch.object(
                    audit, "audit_patcher_live",
                    return_value=("STALE_CONTRACTS", ["detalle"]),
                ):
            with self.assertRaises(SystemExit) as ctx:
                audit.main()

        self.assertEqual(1, ctx.exception.code)


if __name__ == "__main__":
    unittest.main()
