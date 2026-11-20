"""
Tests unitarios para el arnés de prueba headless C++ (core/compiler/cpp_headless_runner.py).
Verifica compilación nativa, ejecución aislada y evaluación semántica contra kernels desacoplados.
"""
import os
import shutil
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
    run_headless_cases
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
        # En el entorno host detectamos g++ o clang++
        self.assertIsNotNone(compiler)
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


if __name__ == "__main__":
    unittest.main()
