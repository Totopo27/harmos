#!/usr/bin/env python3
"""
Harmos Benchmark Runner: Evaluación de Presupuestos de Rendimiento en Tiempo Real (SHIP / NO_SHIP).
Ejecuta suites de rendimiento contra presupuestos de tiempo real para Max MSP.

NOTA EPISTEMICA (docs/ORACULO_LIMITES.md):
Esta medición se ejecuta dentro del entorno Python host (time.perf_counter_ns).
No sustituye la auditoría de ejecución viva en Cycling '74 Max (scripts/audit.py).
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

    ratios = [
        (5.0, 3.0), (7.0, 4.0), (9.0, 8.0), (11.0, 6.0),
        (13.0, 8.0), (15.0, 8.0), (17.0, 16.0), (19.0, 16.0)
    ]
    str_ratios = [f"{c}:{m}" for c, m in ratios]

    # Referencia no optimizada que parsea strings de ratios
    def unoptimized_truax_batch():
        res = []
        for s in str_ratios:
            parts = s.split(":")
            c, m = float(parts[0]), float(parts[1])
            while (c != m) and (m < (2.0 * c)):
                c = abs(c - m)
            res.append((c, m))
        return res

    def engine_truax_batch():
        res = []
        for c, m in ratios:
            res.append(engine.to_normal_form(c, m))
        return res

    verdict = evaluate_benchmark(
        name="Truax Normal Form Reduction (Microtonal Engine)",
        target_fn=engine_truax_batch,
        reference_fn=unoptimized_truax_batch,
        budget=PerformanceBudget(max_latency_us=50.0, min_speedup=1.0, max_p95_latency_us=100.0),
        iterations=500,
        rounds=5
    )
    return verdict


def benchmark_scale_generation_384():
    engine = MicrotonalEngine()
    verdict = evaluate_benchmark(
        name="Generacion de Tablas de Afinacion (384 posiciones)",
        target_fn=lambda: engine.generate_all_scales(),
        budget=PerformanceBudget(max_latency_us=2000.0, max_p95_latency_us=3000.0), # Operación de carga / inicio
        iterations=50,
        rounds=3
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

    print("\n" + "=" * 65)
    print("      HARMOS PERFORMANCE BENCHMARK & TIMING EVALUATION")
    print("=" * 65)
    print(
        "\n[i] AVISO EPISTEMICO (docs/ORACULO_LIMITES.md):\n"
        "    Esta evaluacion mide latencias en el interprete Python host (time.perf_counter_ns).\n"
        "    No constituye una auditoria de ejecucion en vivo en Cycling '74 Max ni certifica\n"
        "    rendimiento en el motor de audio DSP (reservado exclusivamente a scripts/audit.py)."
    )

    overall_ship = True
    for v in suites:
        print(f"\n[*] Benchmark: {v.name}")
        print(f"    Evaluacion:   [{v.verdict}]")
        print(f"    Media:        {v.mean_latency_us:.3f} us (mediana: {v.median_latency_us:.3f} us, p95: {v.p95_latency_us:.3f} us)")
        if v.speedup is not None:
            disp_str = f" +/- {v.speedup_dispersion:.2f}x" if v.speedup_dispersion else ""
            print(f"    Aceleracion:  {v.speedup:.2f}x{disp_str} (ref media: {v.reference_mean_us:.3f} us)")
        for r in v.reasons:
            print(f"    - {r}")

        if v.verdict != "SHIP":
            overall_ship = False

    print("\n" + "-" * 65)
    print(f"EVALUACION FINAL DE RENDIMIENTO: {'SHIP (DENTRO DE PRESUPUESTO)' if overall_ship else 'NO_SHIP (FUERA DE PRESUPUESTO)'}")
    print("-" * 65)

    sys.exit(0 if overall_ship else 1)


if __name__ == "__main__":
    main()
