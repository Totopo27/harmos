"""
Tests unitarios para el arnés de prueba headless C++ (core/compiler/cpp_headless_runner.py).
Verifica compilación nativa, ejecución aislada y evaluación semántica contra kernels desacoplados.
"""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.compiler.oracle_harvest import TestCase
from core.compiler.cpp_generator import generate_cpp_kernel
from core.compiler.cpp_headless_runner import (
    find_cpp_compiler,
    compile_cpp_executable,
    generate_cpp_harness,
    run_headless_cases,
    parse_headless_output,
    evaluate_headless_cases,
    register_kernel_generator,
    _KERNEL_GENERATORS,
)


class TestCppHeadlessRunner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.compiler = find_cpp_compiler()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_find_cpp_compiler(self):
        compiler = find_cpp_compiler()
        if not compiler:
            self.skipTest("Compilador C++ no disponible en este entorno host")
        self.assertIn(compiler, ["g++", "clang++", "cl"])

    def test_compile_cpp_executable_minimal(self):
        if not self.compiler:
            self.skipTest("Compilador C++ no disponible")

        src = Path(self.temp_dir) / "main.cpp"
        exe = Path(self.temp_dir) / ("main.exe" if os.name == "nt" else "main")
        src.write_text("""
        #include <iostream>
        int main() {
            std::cout << "OK" << std::endl;
            return 0;
        }
        """, encoding="utf-8")

        ok, msg = compile_cpp_executable(src, exe, compiler_path=self.compiler)
        self.assertTrue(ok, f"Fallo al compilar C++ minimo: {msg}")
        self.assertTrue(exe.exists())

    def test_generate_cpp_harness_contains_includes_and_calls(self):
        cases = [
            TestCase(fn="reduce_to_octave", args=[0.5], expected=1.0, tolerance=1e-7),
            TestCase(fn="reduce_to_octave", args=[3.0], expected=1.5, tolerance=1e-7)
        ]
        dummy_header = Path(self.temp_dir) / "dummy_kernel.hpp"
        dummy_header.write_text("// dummy", encoding="utf-8")

        code = generate_cpp_harness(dummy_header, cases, kernel_class="wilson")
        self.assertIn("dummy_kernel.hpp", code)
        self.assertIn("harmos::kernels::wilson::WilsonKernel::reduce_to_octave", code)
        self.assertIn(r'\"id\": 0', code)
        self.assertIn(r'\"id\": 1', code)

    def test_run_headless_wilson_kernel_pass_and_fail(self):
        if not self.compiler:
            self.skipTest("Compilador C++ no disponible")

        wilson_header = Path("benchmarks/teclados-wilson/wilson_kernel.hpp").resolve()
        self.assertTrue(wilson_header.exists(), f"No se encontro {wilson_header}")

        # Casos válidos esperados de Wilson reduce_to_octave
        valid_cases = [
            TestCase(fn="reduce_to_octave", args=[0.5], expected=1.0, tolerance=1e-7),
            TestCase(fn="reduce_to_octave", args=[1.0], expected=1.0, tolerance=1e-7),
            TestCase(fn="reduce_to_octave", args=[1.5], expected=1.5, tolerance=1e-7),
            TestCase(fn="reduce_to_octave", args=[2.0], expected=1.0, tolerance=1e-7),
            TestCase(fn="reduce_to_octave", args=[3.0], expected=1.5, tolerance=1e-7),
            TestCase(fn="reduce_to_octave", args=[5.0], expected=1.25, tolerance=1e-7),
            TestCase(fn="reduce_to_octave", args=[7.0], expected=1.75, tolerance=1e-7)
        ]

        # 1. Ejecución con casos válidos -> PASS
        report_pass = run_headless_cases(wilson_header, valid_cases, kernel_class="wilson")
        self.assertEqual(report_pass.verdict, "PASS")
        self.assertEqual(report_pass.passed_cases, 7)
        self.assertEqual(report_pass.failed_cases, 0)
        self.assertEqual(len(report_pass.failures), 0)

        # 2. Ejecución con caso con expectativa errónea -> FAIL (MISMATCH)
        mismatch_cases = valid_cases + [
            TestCase(fn="reduce_to_octave", args=[3.0], expected=999.0, tolerance=1e-7)
        ]
        report_fail = run_headless_cases(wilson_header, mismatch_cases, kernel_class="wilson")
        self.assertEqual(report_fail.verdict, "FAIL")
        self.assertEqual(report_fail.passed_cases, 7)
        self.assertEqual(report_fail.failed_cases, 1)
        self.assertEqual(len(report_fail.failures), 1)
        self.assertEqual(report_fail.failures[0].case.fn, "reduce_to_octave")
        self.assertIn("Discrepancia numerica", report_fail.failures[0].reason)

    def test_run_headless_hexslider_kernel_pass(self):
        if not self.compiler:
            self.skipTest("Compilador C++ no disponible")

        hexslider_header = Path("benchmarks/teclados-wilson/wilson_hexslider_kernel.hpp").resolve()
        self.assertTrue(hexslider_header.exists(), f"No se encontro {hexslider_header}")

        cases = [
            TestCase(fn="compute_cell_frequency", args=[0, 0], expected=261.625565, tolerance=1e-5),
            TestCase(fn="hit_test", args=[12.0, 10.3923], expected=0, tolerance=1e-5),
            TestCase(fn="hit_test", args=[0.0, 0.0], expected=-1, tolerance=1e-5),
        ]

        report = run_headless_cases(hexslider_header, cases, kernel_class="hexslider")
        self.assertEqual(report.verdict, "PASS")
        self.assertEqual(report.passed_cases, 3)
        self.assertEqual(report.failed_cases, 0)

    def test_run_headless_truax_kernel_pass(self):
        if not self.compiler:
            self.skipTest("Compilador C++ no disponible")

        truax_header = Path("core/compiler/truax_kernel.hpp").resolve()
        self.assertTrue(truax_header.exists(), f"No se encontro {truax_header}")

        cases = [
            TestCase(fn="to_normal_form", args=[1.0, 1.0], expected=[1.0, 1.0], tolerance=1e-7),
            TestCase(fn="to_normal_form", args=[3.0, 2.0], expected=[1.0, 2.0], tolerance=1e-7),
            TestCase(fn="calc_carrier_freq", args=[220.0, 3.0, 2.0], expected=660.0, tolerance=1e-7)
        ]

        report = run_headless_cases(truax_header, cases, kernel_class="truax")
        self.assertEqual(report.verdict, "PASS")
        self.assertEqual(report.passed_cases, 3)
        self.assertEqual(report.failed_cases, 0)

    def test_run_headless_generated_kernel(self):
        if not self.compiler:
            self.skipTest("Compilador C++ no disponible")

        # Generar un kernel C++ desacoplado desde un IR de control
        ir = {
            "object_name": "harmos.test_gain",
            "category": "control",
            "target_runtime": "cpp_min_devkit",
            "inlets": [{"id": 0, "type": "float", "description": "Val"}],
            "outlets": [{"id": 0, "type": "float", "description": "Out"}],
            "attributes": []
        }
        kernel_src = generate_cpp_kernel(ir)
        header_path = Path(self.temp_dir) / "harmos_test_gain_kernel.hpp"
        header_path.write_text(kernel_src, encoding="utf-8")

        cases = [
            TestCase(fn="process_scalar", args=[0.0], expected=0.0, tolerance=1e-7),
            TestCase(fn="process_scalar", args=[440.0], expected=440.0, tolerance=1e-7),
            TestCase(fn="process_scalar", args=[-12.5], expected=-12.5, tolerance=1e-7)
        ]

        report = run_headless_cases(
            header_path,
            cases,
            kernel_class="control",
            kernel_type_name="harmos_test_gainKernel"
        )
        self.assertEqual(report.verdict, "PASS")
        self.assertEqual(report.passed_cases, 3)
        self.assertEqual(report.failed_cases, 0)

    def test_run_headless_blocked_when_compiler_unavailable(self):
        with patch("core.compiler.cpp_headless_runner.find_cpp_compiler", return_value=None):
            cases = [TestCase(fn="dummy", args=[1.0], expected=1.0, tolerance=1e-7)]
            report = run_headless_cases("dummy.hpp", cases)
            self.assertEqual(report.verdict, "BLOCKED (COMPILER_UNAVAILABLE)")
            self.assertEqual(report.failed_cases, 1)

    def test_run_headless_fail_when_header_missing(self):
        if not self.compiler:
            self.skipTest("Compilador C++ no disponible")

        cases = [TestCase(fn="dummy", args=[1.0], expected=1.0, tolerance=1e-7)]
        report = run_headless_cases("non_existent_kernel.hpp", cases)
        self.assertEqual(report.verdict, "FAIL")
        self.assertIn("no encontrado", report.details[0])

    def test_parse_headless_output_valid_and_malformed(self):
        stdout = (
            '{"id": 0, "status": "ok", "actual": 1.5}\n'
            'random debug line that is ignored\n'
            '{"malformed_json: missing_brace\n'
            '{"id": 1, "status": "error", "error": "std::overflow_error"}\n'
            '{"status": "ok", "actual": 2.0}\n'  # Missing id
        )
        outputs, errors = parse_headless_output(stdout)
        self.assertIn(0, outputs)
        self.assertEqual(outputs[0]["actual"], 1.5)
        self.assertIn(1, outputs)
        self.assertEqual(outputs[1]["error"], "std::overflow_error")
        self.assertEqual(len(errors), 2)  # One syntax error, one missing 'id' error

    def test_evaluate_headless_cases_outcomes(self):
        cases = [
            TestCase(fn="test_fn", args=[1], expected=1.0, tolerance=1e-5),
            TestCase(fn="test_fn", args=[2], expected=2.0, tolerance=1e-5),
            TestCase(fn="test_fn", args=[3], expected=3.0, tolerance=1e-5),
        ]
        outputs = {
            0: {"status": "ok", "actual": 1.0},
            1: {"status": "ok", "actual": 99.0},  # mismatch
            # 2 is missing
        }
        passed, failed, failures = evaluate_headless_cases(cases, outputs)
        self.assertEqual(passed, 1)
        self.assertEqual(failed, 2)
        self.assertEqual(len(failures), 2)
        self.assertIn("Discrepancia numerica", failures[0].reason)
        self.assertIn("Sin salida producida", failures[1].reason)

    def test_custom_kernel_generator_registration(self):
        def custom_gen(cases, _type_name):
            return ["    // Custom generator code"]

        # Isolate the module-level registry so the custom archetype never leaks into other tests.
        with patch.dict("core.compiler.cpp_headless_runner._KERNEL_GENERATORS"):
            register_kernel_generator("my_custom_archetype", custom_gen)
            cases = [TestCase(fn="foo", args=[], expected=0)]
            code = generate_cpp_harness("dummy.hpp", cases, kernel_class="my_custom_archetype")
            self.assertIn("// Custom generator code", code)
        self.assertNotIn("my_custom_archetype", _KERNEL_GENERATORS)

    def _dummy_header(self):
        header = Path(self.temp_dir) / "dummy_kernel.hpp"
        header.write_text("// dummy", encoding="utf-8")
        return header

    def test_compile_cpp_executable_rejects_invalid_source(self):
        if not self.compiler:
            self.skipTest("Compilador C++ no disponible")
        src = Path(self.temp_dir) / "broken.cpp"
        exe = Path(self.temp_dir) / ("broken.exe" if os.name == "nt" else "broken")
        src.write_text("int main( { return 0; }", encoding="utf-8")
        ok, msg = compile_cpp_executable(src, exe, compiler_path=self.compiler)
        self.assertFalse(ok)
        self.assertTrue(msg)
        self.assertFalse(exe.exists())

    def test_run_headless_fail_on_compilation_error(self):
        cases = [TestCase(fn="dummy", args=[1.0], expected=1.0, tolerance=1e-7)]
        with patch("core.compiler.cpp_headless_runner.find_cpp_compiler", return_value="g++"), \
                patch("core.compiler.cpp_headless_runner.compile_cpp_executable",
                      return_value=(False, "error: expected ';'")):
            report = run_headless_cases(self._dummy_header(), cases)
        self.assertEqual(report.verdict, "FAIL")
        self.assertEqual(report.passed_cases, 0)
        self.assertEqual(report.failed_cases, 1)
        self.assertIn("Fallo de compilacion", report.details[0])
        self.assertIn("expected ';'", report.details[0])

    def test_run_headless_fail_on_execution_timeout(self):
        cases = [TestCase(fn="dummy", args=[1.0], expected=1.0, tolerance=1e-7)]
        timeout = subprocess.TimeoutExpired(cmd="harness", timeout=0.5)
        with patch("core.compiler.cpp_headless_runner.find_cpp_compiler", return_value="g++"), \
                patch("core.compiler.cpp_headless_runner.compile_cpp_executable", return_value=(True, "")), \
                patch("core.compiler.cpp_headless_runner.subprocess.run", side_effect=timeout):
            report = run_headless_cases(self._dummy_header(), cases, timeout_sec=0.5)
        self.assertEqual(report.verdict, "FAIL")
        self.assertEqual(report.failed_cases, 1)
        self.assertIn("Timeout (0.5s)", report.details[0])


if __name__ == "__main__":
    unittest.main()
