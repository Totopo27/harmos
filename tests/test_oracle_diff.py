"""
Tests unitarios para el runner de diff del oráculo semántico (core/compiler/oracle_diff.py).
Inspirado en el estándar de verificación diferencial de rust-anything.
"""
import unittest
from core.compiler.oracle_harvest import TestCase
from core.compiler.oracle_diff import (
    compare_numeric_or_structure,
    evaluate_diff,
    DiffReport
)


class TestOracleDiff(unittest.TestCase):
    def test_compare_numeric_within_tolerance(self):
        ok, reason = compare_numeric_or_structure(100.0, 100.00000005, tolerance=1e-6)
        self.assertTrue(ok)
        self.assertIsNone(reason)

    def test_compare_numeric_exceeding_tolerance(self):
        ok, reason = compare_numeric_or_structure(100.0, 100.05, tolerance=1e-4)
        self.assertFalse(ok)
        self.assertIn("Discrepancia numerica", reason)
        self.assertIn("delta", reason)

    def test_compare_nested_lists_and_dicts(self):
        expected = {"freqs": [440.0, 660.0], "scale": "hexany"}
        actual = {"freqs": [440.00000001, 660.0], "scale": "hexany"}
        ok, _ = compare_numeric_or_structure(expected, actual, tolerance=1e-6)
        self.assertTrue(ok)

        mismatched = {"freqs": [440.0, 700.0], "scale": "hexany"}
        ok_bad, reason = compare_numeric_or_structure(expected, mismatched, tolerance=1e-6)
        self.assertFalse(ok_bad)
        self.assertIn("clave 'freqs'", reason)

    def test_evaluate_diff_all_pass(self):
        cases = [
            TestCase(fn="double_it", args=[5.0], expected=10.0),
            TestCase(fn="double_it", args=[2.5], expected=5.0),
            TestCase(fn="square_it", args=[4.0], expected=16.0)
        ]

        registry = {
            "double_it": lambda x: x * 2.0,
            "square_it": lambda x: x ** 2
        }

        report = evaluate_diff(cases, registry)
        self.assertEqual(report.verdict, "PASS")
        self.assertEqual(report.passed_cases, 3)
        self.assertEqual(report.failed_cases, 0)
        self.assertEqual(len(report.failures), 0)

    def test_evaluate_diff_detects_mismatch(self):
        cases = [
            TestCase(fn="calc", args=[10.0], expected=20.0),
            TestCase(fn="calc", args=[5.0], expected=10.0)
        ]

        # Implementación con bug
        registry = {
            "calc": lambda x: x * 3.0
        }

        report = evaluate_diff(cases, registry)
        self.assertEqual(report.verdict, "FAIL")
        self.assertEqual(report.passed_cases, 0)
        self.assertEqual(report.failed_cases, 2)
        self.assertEqual(len(report.failures), 2)
        self.assertIn("Discrepancia numerica", report.failures[0].reason)

    def test_evaluate_diff_handles_expected_errors(self):
        def fragile_divide(a, b):
            if b == 0:
                raise ZeroDivisionError("denominador cero")
            return a / b

        cases = [
            TestCase(fn="div", args=[10.0, 2.0], expected=5.0),
            TestCase(fn="div", args=[10.0, 0.0], error="ZeroDivisionError")
        ]

        report = evaluate_diff(cases, {"div": fragile_divide})
        self.assertEqual(report.verdict, "PASS")
        self.assertEqual(report.passed_cases, 2)

    def test_evaluate_diff_fails_when_expected_error_is_missing(self):
        # Función que silencia el error retornando 0 en vez de lanzar
        def silent_div(a, b):
            return a / b if b != 0 else 0.0

        cases = [
            TestCase(fn="div", args=[10.0, 0.0], error="ZeroDivisionError")
        ]

        report = evaluate_diff(cases, {"div": silent_div})
        self.assertEqual(report.verdict, "FAIL")
        self.assertIn("Ruta de error omitida", report.failures[0].reason)

    def test_evaluate_diff_missing_target_function(self):
        cases = [
            TestCase(fn="unknown_fn", args=[1])
        ]
        report = evaluate_diff(cases, {})
        self.assertEqual(report.verdict, "FAIL")
        self.assertIn("no encontrada", report.failures[0].reason)


if __name__ == "__main__":
    unittest.main()
