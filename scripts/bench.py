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
import json
from dataclasses import asdict
from core.compiler.benchmark import (
    get_standard_benchmarks,
    format_benchmark_report,
    benchmark_truax_normal_form,
    benchmark_scale_generation_384,
)


def main():
    parser = argparse.ArgumentParser(description="Harmos Explicit Benchmark Runner")
    parser.add_argument("--suite", choices=["truax", "tables", "all"], default="all", help="Suite a ejecutar")
    parser.add_argument("--json", action="store_true", help="Emitir reporte en formato JSON legible por maquina")
    args = parser.parse_args()

    try:
        suites = get_standard_benchmarks(args.suite)
    except Exception as e:
        print(f"ERROR: Fallo al ejecutar suite de benchmark {args.suite}: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        data = [asdict(v) for v in suites]
        print(json.dumps(data, indent=2))
    else:
        print("\n" + format_benchmark_report(suites))

    all_ship = all(v.verdict == "SHIP" for v in suites)
    sys.exit(0 if all_ship else 1)


if __name__ == "__main__":
    main()
