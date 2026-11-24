"""
Harmos Benchmark Engine: Medición de rendimiento y evaluación de presupuestos de tiempo real.
Inspirado en la regla epistémica de rust-anything (DECISIONS.md S4):
Reportar métricas brutas traslada la decisión al usuario; el benchmark debe emitir un veredicto
categórico basado en presupuestos de tiempo real y ganancia de velocidad.

NOTA: Este módulo evalúa latencias en Python host (time.perf_counter_ns). No sustituye
ni constituye un veredicto de auditoría en vivo en Cycling '74 Max (scripts/audit.py).
"""
import gc
import time
import statistics
from dataclasses import dataclass, field
from typing import Callable, Any, Dict, List, Optional, Tuple


@dataclass
class PerformanceBudget:
    """
    Presupuesto de ejecución para tiempo real en Max MSP.
    A 48 kHz y tamaño de vector de 64 muestras:
    - 1 bloque = 64 / 48000 s = 1.333 ms = 1333.3 us.
    - 10% de carga de CPU = 133.3 us de presupuesto máximo por bloque DSP.
    - 5% de carga de CPU = 66.7 us de presupuesto.
    """
    max_latency_us: float = 133.3       # Límite superior aceptable en microsegundos
    min_speedup: Optional[float] = None # Factor mínimo de aceleración respecto a la referencia
    max_p95_latency_us: float = 200.0   # Percentil 95 máximo admisible para evitar glitches de audio
    tolerance_margin: float = 0.05      # Margen de tolerancia frente a ruido de medición (5%)


@dataclass
class BenchmarkVerdict:
    name: str
    verdict: str                        # "SHIP" o "NO_SHIP"
    mean_latency_us: float
    min_latency_us: float
    max_latency_us: float
    p95_latency_us: float
    median_latency_us: float = 0.0
    speedup: Optional[float] = None
    reference_mean_us: Optional[float] = None
    reference_median_us: Optional[float] = None
    speedup_dispersion: Optional[float] = None
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "verdict": self.verdict,
            "mean_latency_us": round(self.mean_latency_us, 3),
            "median_latency_us": round(self.median_latency_us or self.mean_latency_us, 3),
            "min_latency_us": round(self.min_latency_us, 3),
            "max_latency_us": round(self.max_latency_us, 3),
            "p95_latency_us": round(self.p95_latency_us, 3),
            "speedup": round(self.speedup, 2) if self.speedup is not None else None,
            "speedup_dispersion": round(self.speedup_dispersion, 2) if self.speedup_dispersion is not None else None,
            "reference_mean_us": round(self.reference_mean_us, 3) if self.reference_mean_us is not None else None,
            "reasons": self.reasons
        }


def _calculate_p95(latencies: List[float]) -> float:
    """Calcula el percentil 95 con interpolación lineal (evita sesgo al alza de nearest-rank)."""
    if not latencies:
        return 0.0
    sorted_vals = sorted(latencies)
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    idx = (n - 1) * 0.95
    low = int(idx)
    high = min(low + 1, n - 1)
    weight = idx - low
    return sorted_vals[low] * (1.0 - weight) + sorted_vals[high] * weight


def run_workload(
    fn: Callable[[], Any],
    iterations: int = 1000,
    warmup: int = 100
) -> List[float]:
    """Ejecuta una función en bucle y devuelve latencias individuales en microsegundos."""
    for _ in range(warmup):
        fn()

    latencies_us = []
    for _ in range(iterations):
        t0 = time.perf_counter_ns()
        fn()
        t1 = time.perf_counter_ns()
        latencies_us.append((t1 - t0) / 1000.0)

    return latencies_us


def _collect_round_latencies(
    target_fn: Callable[[], Any],
    reference_fn: Optional[Callable[[], Any]],
    iterations: int,
    rounds: int,
    warmup: int
) -> Tuple[List[float], List[float], List[float], List[float], List[float]]:
    """Recolecta latencias individuales y medianas por ronda para target y referencia opcional."""
    all_target_times: List[float] = []
    all_ref_times: List[float] = []
    round_target_medians: List[float] = []
    round_ref_medians: List[float] = []
    round_speedups: List[float] = []

    for _ in range(rounds):
        # Warmup por ronda
        for _ in range(warmup):
            target_fn()
            if reference_fn:
                reference_fn()

        round_target: List[float] = []
        round_ref: List[float] = []

        if reference_fn:
            # Medición intercalada para neutralizar throttling térmico y bias de scheduler
            for _ in range(iterations):
                t0 = time.perf_counter_ns()
                target_fn()
                t1 = time.perf_counter_ns()
                reference_fn()
                t2 = time.perf_counter_ns()
                round_target.append((t1 - t0) / 1000.0)
                round_ref.append((t2 - t1) / 1000.0)

            med_target = statistics.median(round_target)
            med_ref = statistics.median(round_ref)
            round_target_medians.append(med_target)
            round_ref_medians.append(med_ref)
            round_speedups.append(med_ref / med_target if med_target > 0 else 1.0)
            all_target_times.extend(round_target)
            all_ref_times.extend(round_ref)
        else:
            for _ in range(iterations):
                t0 = time.perf_counter_ns()
                target_fn()
                t1 = time.perf_counter_ns()
                round_target.append((t1 - t0) / 1000.0)

            med_target = statistics.median(round_target)
            round_target_medians.append(med_target)
            all_target_times.extend(round_target)

    return all_target_times, all_ref_times, round_target_medians, round_ref_medians, round_speedups


def _compute_statistical_verdict(
    name: str,
    budget: PerformanceBudget,
    all_target_times: List[float],
    all_ref_times: List[float],
    round_target_medians: List[float],
    round_ref_medians: List[float],
    round_speedups: List[float],
    has_reference: bool
) -> BenchmarkVerdict:
    """Calcula las estadísticas de latencia y emite el veredicto categórico SHIP/NO_SHIP."""
    if not all_target_times or not round_target_medians:
        return BenchmarkVerdict(
            name=name, verdict="NO_SHIP",
            mean_latency_us=0.0, min_latency_us=0.0, max_latency_us=0.0, p95_latency_us=0.0,
            reasons=["Sin muestras de latencia: no hay evidencia para emitir SHIP."],
        )
    mean_target = statistics.mean(all_target_times)
    median_target = statistics.median(round_target_medians)
    min_target = min(all_target_times)
    max_target = max(all_target_times)
    p95_target = _calculate_p95(all_target_times)

    reasons: List[str] = []
    verdict = "SHIP"

    # Verificación de presupuesto absoluto
    if mean_target > budget.max_latency_us:
        verdict = "NO_SHIP"
        reasons.append(
            f"Latencia media ({mean_target:.2f} us) excede el presupuesto maximo ({budget.max_latency_us:.2f} us)."
        )

    if p95_target > budget.max_p95_latency_us:
        verdict = "NO_SHIP"
        reasons.append(
            f"Percentil 95 ({p95_target:.2f} us) excede el limite ({budget.max_p95_latency_us:.2f} us) - riesgo de jitter."
        )

    # Verificación de aceleración respecto a referencia
    speedup = None
    mean_ref = None
    median_ref = None
    speedup_dispersion = None

    if has_reference and not (all_ref_times and round_ref_medians and round_speedups):
        verdict = "NO_SHIP"
        reasons.append("Referencia declarada sin muestras: aceleracion no evaluable.")
    elif has_reference:
        mean_ref = statistics.mean(all_ref_times)
        median_ref = statistics.median(round_ref_medians)
        speedup = statistics.median(round_speedups)
        speedup_dispersion = statistics.stdev(round_speedups) if len(round_speedups) > 1 else 0.0

        if budget.min_speedup is not None:
            threshold = budget.min_speedup - budget.tolerance_margin
            if speedup < threshold:
                verdict = "NO_SHIP"
                reasons.append(
                    f"Aceleracion insuficiente ({speedup:.2f}x). Requerido minimo {budget.min_speedup:.2f}x (dispersion: +/-{speedup_dispersion:.2f}x)."
                )
            elif speedup < budget.min_speedup:
                reasons.append(
                    f"Aceleracion marginal dentro de banda de ruido ({speedup:.2f}x vs requerido {budget.min_speedup:.2f}x, +/-{speedup_dispersion:.2f}x)."
                )
            else:
                reasons.append(f"Aceleracion exitosa ({speedup:.2f}x vs referencia).")
    elif budget.min_speedup is not None:
        reasons.append("Aceleracion no evaluable: min_speedup especificado sin funcion de referencia.")

    if verdict == "SHIP":
        reasons.insert(0, f"Dentro de presupuesto de tiempo real ({mean_target:.2f} us <= {budget.max_latency_us:.2f} us).")

    return BenchmarkVerdict(
        name=name,
        verdict=verdict,
        mean_latency_us=mean_target,
        min_latency_us=min_target,
        max_latency_us=max_target,
        p95_latency_us=p95_target,
        median_latency_us=median_target,
        speedup=speedup,
        reference_mean_us=mean_ref,
        reference_median_us=median_ref,
        speedup_dispersion=speedup_dispersion,
        reasons=reasons
    )


def evaluate_benchmark(
    name: str,
    target_fn: Callable[[], Any],
    reference_fn: Optional[Callable[[], Any]] = None,
    budget: Optional[PerformanceBudget] = None,
    iterations: int = 1000,
    rounds: int = 5,
    warmup: int = 50
) -> BenchmarkVerdict:
    """
    Evalúa una función contra un presupuesto de rendimiento mediante muestreo multi-ronda
    intercalado y estadísticas robustas (medianas):
    - SHIP: Cumple presupuesto de latencia en tiempo real y aceleración requerida.
    - NO_SHIP: Supera el presupuesto o presenta regresión inaceptable.
    """
    b = budget or PerformanceBudget()

    gc.collect()
    gc_enabled = gc.isenabled()
    gc.disable()
    try:
        all_target_times, all_ref_times, round_target_medians, round_ref_medians, round_speedups = _collect_round_latencies(
            target_fn=target_fn,
            reference_fn=reference_fn,
            iterations=iterations,
            rounds=rounds,
            warmup=warmup
        )
    finally:
        if gc_enabled:
            gc.enable()

    return _compute_statistical_verdict(
        name=name,
        budget=b,
        all_target_times=all_target_times,
        all_ref_times=all_ref_times,
        round_target_medians=round_target_medians,
        round_ref_medians=round_ref_medians,
        round_speedups=round_speedups,
        has_reference=(reference_fn is not None)
    )


def format_benchmark_report(verdicts: List[BenchmarkVerdict]) -> str:
    """Genera un reporte textual consistente y desacoplado para CLI y scripts."""
    lines = [
        "=" * 65,
        "      HARMOS PERFORMANCE BENCHMARK & TIMING EVALUATION",
        "=" * 65,
        "",
        "[i] AVISO EPISTEMICO (docs/ORACULO_LIMITES.md):",
        "    Esta evaluacion mide latencias en el interprete Python host (time.perf_counter_ns).",
        "    No constituye una auditoria de ejecucion en vivo en Cycling '74 Max ni certifica",
        "    rendimiento en el motor de audio DSP (reservado exclusivamente a scripts/audit.py).",
        ""
    ]
    all_ship = True
    for v in verdicts:
        lines.append(f"[*] Benchmark: {v.name}")
        lines.append(f"    Evaluacion:   [{v.verdict}]")
        lines.append(
            f"    Media:        {v.mean_latency_us:.3f} us (mediana: {v.median_latency_us:.3f} us, p95: {v.p95_latency_us:.3f} us)"
        )
        if v.speedup is not None:
            disp_str = f" +/- {v.speedup_dispersion:.2f}x" if v.speedup_dispersion else ""
            lines.append(f"    Aceleracion:  {v.speedup:.2f}x{disp_str} (ref media: {v.reference_mean_us:.3f} us)")
        for r in v.reasons:
            lines.append(f"    - {r}")
        lines.append("")
        if v.verdict != "SHIP":
            all_ship = False

    lines.append("-" * 65)
    final_status = "SHIP (DENTRO DE PRESUPUESTO)" if all_ship else "NO_SHIP (FUERA DE PRESUPUESTO)"
    lines.append(f"EVALUACION FINAL DE RENDIMIENTO: {final_status}")
    lines.append("-" * 65)
    return "\n".join(lines)


def benchmark_truax_normal_form() -> BenchmarkVerdict:
    """Benchmark estandar: reduccion a forma normal de Truax (MicrotonalEngine)."""
    from benchmarks.truax_fm.microtonal_engine import MicrotonalEngine

    engine = MicrotonalEngine()

    ratios = [
        (5.0, 3.0), (7.0, 4.0), (9.0, 8.0), (11.0, 6.0),
        (13.0, 8.0), (15.0, 8.0), (17.0, 16.0), (19.0, 16.0)
    ]
    str_ratios = [f"{c}:{m}" for c, m in ratios]

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

    return evaluate_benchmark(
        name="Truax Normal Form Reduction (Microtonal Engine)",
        target_fn=engine_truax_batch,
        reference_fn=unoptimized_truax_batch,
        budget=PerformanceBudget(max_latency_us=100.0, min_speedup=0.6, max_p95_latency_us=250.0, tolerance_margin=0.15),
        iterations=500,
        rounds=5
    )


def benchmark_scale_generation_384() -> BenchmarkVerdict:
    """Benchmark estandar: generacion de tablas de afinacion de 384 posiciones."""
    from benchmarks.truax_fm.microtonal_engine import MicrotonalEngine

    engine = MicrotonalEngine()
    return evaluate_benchmark(
        name="Generacion de Tablas de Afinacion (384 posiciones)",
        target_fn=lambda: engine.generate_all_scales(),
        budget=PerformanceBudget(max_latency_us=4000.0, max_p95_latency_us=8000.0),
        iterations=50,
        rounds=3
    )


def get_standard_benchmarks(suite: str = "all") -> List[BenchmarkVerdict]:
    """Ejecuta y compila la suite de benchmarks solicitada ('truax', 'tables', 'all')."""
    suites = []
    if suite in ["truax", "all"]:
        suites.append(benchmark_truax_normal_form())
    if suite in ["tables", "all"]:
        suites.append(benchmark_scale_generation_384())
    return suites
