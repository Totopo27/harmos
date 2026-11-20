"""
Harmos Benchmark Engine: Medición de rendimiento y evaluación de presupuestos de tiempo real.
Inspirado en la regla epistémica de rust-anything (DECISIONS.md S4):
Reportar métricas brutas traslada la decisión al usuario; el benchmark debe emitir un veredicto
categórico basado en presupuestos de tiempo real y ganancia de velocidad.

NOTA: Este módulo evalúa latencias en Python host (time.perf_counter_ns). No sustituye
ni constituye un veredicto de auditoría en vivo en Cycling '74 Max (scripts/audit.py).
"""
import time
import statistics
from dataclasses import dataclass, field
from typing import Callable, Any, Dict, List, Optional


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

    mean_target = statistics.mean(all_target_times)
    median_target = statistics.median(round_target_medians)
    min_target = min(all_target_times)
    max_target = max(all_target_times)
    p95_target = _calculate_p95(all_target_times)

    reasons = []
    verdict = "SHIP"

    # Verificación de presupuesto absoluto
    if mean_target > b.max_latency_us:
        verdict = "NO_SHIP"
        reasons.append(
            f"Latencia media ({mean_target:.2f} us) excede el presupuesto maximo ({b.max_latency_us:.2f} us)."
        )

    if p95_target > b.max_p95_latency_us:
        verdict = "NO_SHIP"
        reasons.append(
            f"Percentil 95 ({p95_target:.2f} us) excede el limite ({b.max_p95_latency_us:.2f} us) - riesgo de jitter."
        )

    # Verificación de aceleración respecto a referencia
    speedup = None
    mean_ref = None
    median_ref = None
    speedup_dispersion = None

    if reference_fn:
        mean_ref = statistics.mean(all_ref_times)
        median_ref = statistics.median(round_ref_medians)
        speedup = statistics.median(round_speedups)
        speedup_dispersion = statistics.stdev(round_speedups) if len(round_speedups) > 1 else 0.0

        if b.min_speedup is not None:
            threshold = b.min_speedup - b.tolerance_margin
            if speedup < threshold:
                verdict = "NO_SHIP"
                reasons.append(
                    f"Aceleracion insuficiente ({speedup:.2f}x). Requerido minimo {b.min_speedup:.2f}x (dispersion: +/-{speedup_dispersion:.2f}x)."
                )
            elif speedup < b.min_speedup:
                reasons.append(
                    f"Aceleracion marginal dentro de banda de ruido ({speedup:.2f}x vs requerido {b.min_speedup:.2f}x, +/-{speedup_dispersion:.2f}x)."
                )
            else:
                reasons.append(f"Aceleracion exitosa ({speedup:.2f}x vs referencia).")
    elif b.min_speedup is not None:
        reasons.append("Aceleracion no evaluable: min_speedup especificado sin funcion de referencia.")

    if verdict == "SHIP":
        reasons.insert(0, f"Dentro de presupuesto de tiempo real ({mean_target:.2f} us <= {b.max_latency_us:.2f} us).")

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
