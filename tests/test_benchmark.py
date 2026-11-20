"""
Tests unitarios para el motor de benchmarks y veredictos explicitos (core/compiler/benchmark.py).
Inspirado en la regla de veredicto explicito de rust-anything (DECISIONS.md S4).
"""
import unittest
import time
from core.compiler.benchmark import (
    PerformanceBudget,
    BenchmarkVerdict,
    run_workload,
    evaluate_benchmark
)


class TestBenchmarkEngine(unittest.TestCase):
    def test_run_workload_returns_latencies(self):
        def sample_workload():
            x = 0
            for i in range(100):
                x += i
            return x

        latencies = run_workload(sample_workload, iterations=50, warmup=10)
        self.assertEqual(len(latencies), 50)
        self.assertTrue(all(l > 0 for l in latencies))

    def test_evaluate_benchmark_ship(self):
        """Verifica que una tarea rapida dentro del presupuesto emite SHIP."""
        def fast_fn():
            return sum(i for i in range(100))

        def slow_fn():
            return sum(i for i in range(10000))

        budget = PerformanceBudget(max_latency_us=2000.0, min_speedup=2.0, max_p95_latency_us=3000.0)
        verdict = evaluate_benchmark(
            name="Test Fast vs Slow",
            target_fn=fast_fn,
            reference_fn=slow_fn,
            budget=budget,
            iterations=50
        )

        self.assertEqual(verdict.verdict, "SHIP")
        self.assertIsNotNone(verdict.speedup)
        self.assertGreaterEqual(verdict.speedup, 2.0)
        self.assertTrue(any("Dentro de presupuesto" in r for r in verdict.reasons))

    def test_evaluate_benchmark_no_ship_latency_exceeded(self):
        """Verifica que una tarea lenta que supera el presupuesto emite NO_SHIP."""
        def slow_target():
            return sum(i for i in range(20000))

        # Presupuesto estricto de 1 microsegundo
        budget = PerformanceBudget(max_latency_us=1.0)
        verdict = evaluate_benchmark(
            name="Test Exceeded Latency",
            target_fn=slow_target,
            budget=budget,
            iterations=20
        )

        self.assertEqual(verdict.verdict, "NO_SHIP")
        self.assertTrue(any("excede el presupuesto" in r for r in verdict.reasons))

    def test_evaluate_benchmark_no_ship_speedup_regression(self):
        """Verifica que una tarea mas lenta que la referencia emite NO_SHIP."""
        def slow_target():
            return sum(i for i in range(10000))

        def fast_reference():
            return sum(i for i in range(100))

        budget = PerformanceBudget(max_latency_us=50000.0, min_speedup=1.0)
        verdict = evaluate_benchmark(
            name="Test Regression",
            target_fn=slow_target,
            reference_fn=fast_reference,
            budget=budget,
            iterations=30
        )

        self.assertEqual(verdict.verdict, "NO_SHIP")
        self.assertTrue(any("Aceleracion insuficiente" in r for r in verdict.reasons))

    def test_verdict_to_dict_serialization(self):
        v = BenchmarkVerdict(
            name="Sample",
            verdict="SHIP",
            mean_latency_us=12.3456,
            min_latency_us=10.0,
            max_latency_us=15.0,
            p95_latency_us=14.2,
            median_latency_us=11.5,
            speedup=2.555,
            reference_mean_us=31.54,
            reasons=["OK"]
        )
        d = v.to_dict()
        self.assertEqual(d["verdict"], "SHIP")
        self.assertEqual(d["mean_latency_us"], 12.346)
        self.assertEqual(d["median_latency_us"], 11.5)
        self.assertEqual(d["min_latency_us"], 10.0)
        self.assertEqual(d["max_latency_us"], 15.0)
        self.assertEqual(d["speedup"], 2.56)

    def test_benchmark_reproducibility(self):
        """
        Verifica que ejecuciones consecutivas del benchmark de Truax producen
        veredictos identicos y estables (F2: eliminacion del veredicto coin-toss).
        """
        from scripts.bench import benchmark_truax_normal_form

        verdicts = []
        speedups = []
        for _ in range(5):
            v = benchmark_truax_normal_form()
            verdicts.append(v.verdict)
            self.assertIsNotNone(v.speedup)
            speedups.append(v.speedup)

        # 1. Todos los veredictos deben ser exactamente iguales a SHIP
        self.assertTrue(all(verdict == "SHIP" for verdict in verdicts), f"Veredictos inestables: {verdicts}")

        # 2. La dispersion de speedup entre ejecuciones debe ser acotada (< 0.5x de rango)
        speedup_range = max(speedups) - min(speedups)
        self.assertLess(speedup_range, 0.5, f"Dispersion excesiva en speedup: {speedups}")


if __name__ == "__main__":
    unittest.main()
