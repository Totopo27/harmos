#!/usr/bin/env python3
"""
Harmos Benchmark Runner con Veredictos Explícitos (SHIP / NO_SHIP).
Ejecuta suites de rendimiento contra presupuestos de tiempo real para Max MSP.
"""
import sys
from pathlib import Path

# Asegurar importacion desde la raiz del repositorio
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import argparse
from core.compiler.benchmark import evaluate_benchmark, PerformanceBudget
from core.compiler.microtonal_engine import MicrotonalEngine


def benchmark_truax_normal_form():
    engine = MicrotonalEngine()
    
    # Referencia no optimizada que parsea strings de ratios
    def unoptimized_truax(ratio_str: str):
        parts = ratio_str.split(":")
        c, m = float(parts[0]), float(parts[1])
        while (c != m) and (m < (2.0 * c)):
            c = abs(c - m)
        return c, m

    verdict = evaluate_benchmark(
        name="Truax Normal Form Reduction (Microtonal Engine)",
        target_fn=lambda: engine.to_normal_form(5.0, 3.0),
        reference_fn=lambda: unoptimized_truax("5.0:3.0"),
        budget=PerformanceBudget(max_latency_us=10.0, min_speedup=1.0, max_p95_latency_us=25.0),
        iterations=5000
    )
    return verdict


def benchmark_scale_generation_384():
    engine = MicrotonalEngine()
    verdict = evaluate_benchmark(
        name="Generacion de Tablas de Afinacion (384 posiciones)",
        target_fn=lambda: engine.generate_all_scales(),
        budget=PerformanceBudget(max_latency_us=2000.0, max_p95_latency_us=3000.0), # Operación de carga / inicio
        iterations=200
    )
    return verdict


def main():
    parser = argparse.ArgumentParser(description="Harmos Explicit Benchmark Runner")
    parser.add_argument("--suite", choices=["truax", "tables", "all"], default="all", help="Suite a ejecutar")
    args = parser.parse_args()

    suites = []
    if args.suite in ["truax", "all"]:
        suites.append(benchmark_truax_normal_form())
    if args.suite in ["tables", "all"]:
        suites.append(benchmark_scale_generation_384())

    print("\n" + "=" * 60)
    print("           HARMOS BENCHMARK AUDIT & VERDICTS")
    print("=" * 60)

    overall_ship = True
    for v in suites:
        print(f"\n[*] Benchmark: {v.name}")
        print(f"    Veredicto:    [{v.verdict}]")
        print(f"    Media:        {v.mean_latency_us:.3f} us (p95: {v.p95_latency_us:.3f} us)")
        if v.speedup:
            print(f"    Aceleracion:  {v.speedup:.2f}x (ref: {v.reference_mean_us:.3f} us)")
        for r in v.reasons:
            print(f"    - {r}")

        if v.verdict != "SHIP":
            overall_ship = False

    print("\n" + "-" * 60)
    print(f"VEREDICTO FINAL CONSOLIDADO: {'SHIP (APROBADO)' if overall_ship else 'NO_SHIP (RECHAZADO)'}")
    print("-" * 60)

    sys.exit(0 if overall_ship else 1)


if __name__ == "__main__":
    main()
