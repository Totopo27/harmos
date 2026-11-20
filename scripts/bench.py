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
from core.compiler.benchmark import (
    get_standard_benchmarks,
    format_benchmark_report,
    benchmark_truax_normal_form,
    benchmark_scale_generation_384
)


def main():
    parser = argparse.ArgumentParser(description="Harmos Explicit Benchmark Runner")
    parser.add_argument("--suite", choices=["truax", "tables", "all"], default="all", help="Suite a ejecutar")
    args = parser.parse_args()

    suites = get_standard_benchmarks(args.suite)
    print("\n" + format_benchmark_report(suites))
    sys.exit(0 if all(v.verdict == "SHIP" for v in suites) else 1)


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
