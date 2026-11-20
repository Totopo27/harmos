"""
Tests unitarios para el motor de cosecha de casos del oráculo (core/compiler/oracle_harvest.py).
Inspirado en el estándar de oráculo ejecutable de rust-anything.
"""
import unittest
import tempfile
from pathlib import Path
from core.compiler.oracle_harvest import (
    TestCase,
    write_cases_jsonl,
    read_cases_jsonl,
    harvest_from_callable,
    generate_numeric_edge_cases
)


class TestOracleHarvest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_test_case_dict_roundtrip(self):
        case = TestCase(
            fn="add",
            args=[2.5, 3.5],
            expected=6.0,
            tolerance=1e-5,
            metadata={"source": "math_test"}
        )
        d = case.to_dict()
        self.assertEqual(d["fn"], "add")
        self.assertEqual(d["args"], [2.5, 3.5])
        self.assertEqual(d["expected"], 6.0)
        self.assertEqual(d["tolerance"], 1e-5)
        self.assertEqual(d["metadata"]["source"], "math_test")

        restored = TestCase.from_dict(d)
        self.assertEqual(restored.fn, case.fn)
        self.assertEqual(restored.args, case.args)
        self.assertEqual(restored.expected, case.expected)
        self.assertEqual(restored.tolerance, case.tolerance)

    def test_write_and_read_cases_jsonl(self):
        cases = [
            TestCase(fn="calc_freq", args=[440.0, 2], expected=880.0),
            TestCase(fn="calc_ratio", args=[3, 2], expected=[1.0, 2.0]),
            TestCase(fn="divide", args=[1.0, 0.0], error="ZeroDivisionError: division by zero")
        ]
        out_file = self.dir_path / "cases.jsonl"
        count = write_cases_jsonl(cases, out_file)
        self.assertEqual(count, 3)
        self.assertTrue(out_file.is_file())

        read_back = read_cases_jsonl(out_file)
        self.assertEqual(len(read_back), 3)
        self.assertEqual(read_back[0].fn, "calc_freq")
        self.assertEqual(read_back[1].expected, [1.0, 2.0])
        self.assertIn("ZeroDivisionError", read_back[2].error)

    def test_harvest_from_callable_success_and_error(self):
        def sample_kernel(a, b):
            if b == 0:
                raise ValueError("Denominador no puede ser cero")
            return a / b

        inputs = [
            [10.0, 2.0],
            [9.0, 3.0],
            [5.0, 0.0]  # Provocará error
        ]

        cases = harvest_from_callable(sample_kernel, "sample_kernel", inputs)
        self.assertEqual(len(cases), 3)
        self.assertEqual(cases[0].expected, 5.0)
        self.assertEqual(cases[1].expected, 3.0)
        self.assertIsNone(cases[2].expected)
        self.assertIn("ValueError", cases[2].error)

    def test_generate_numeric_edge_cases(self):
        def safe_multiply(x, factor):
            return x * factor

        cases = generate_numeric_edge_cases(safe_multiply, "safe_multiply", base_args=[10.0, 2.0])
        # Con 2 argumentos y 6 valores de fuzz cada uno = 12 variaciones
        self.assertEqual(len(cases), 12)
        self.assertTrue(all(c.fn == "safe_multiply" for c in cases))
        self.assertTrue(any(c.args[0] == 0.0 for c in cases))
        self.assertTrue(any(c.args[1] == -1.0 for c in cases))

    def test_read_malformed_json_raises_error(self):
        bad_file = self.dir_path / "bad.jsonl"
        bad_file.write_text("{\"fn\": \"incomplete\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            read_cases_jsonl(bad_file)


if __name__ == "__main__":
    unittest.main()
