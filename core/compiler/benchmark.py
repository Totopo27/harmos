"""
Harmos Benchmark Engine: Medición de rendimiento y emisión de veredictos explícitos (SHIP / NO_SHIP).
Inspirado en la regla epistémica de rust-anything (DECISIONS.md S4):
Reportar métricas brutas traslada la decisión al usuario; el benchmark debe emitir un veredicto
categórico basado en presupuestos de tiempo real y ganancia de velocidad.
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
    min_speedup: float = 1.0            # Factor mínimo de aceleración respecto a la referencia
    max_p95_latency_us: float = 200.0   # Percentil 95 máximo admisible para evitar glitches de audio


@dataclass
class BenchmarkVerdict:
    name: str
    verdict: str                        # "SHIP" o "NO_SHIP"
    mean_latency_us: float
    min_latency_us: float
    max_latency_us: float
    p95_latency_us: float
    speedup: Optional[float] = None
    reference_mean_us: Optional[float] = None
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "verdict": self.verdict,
            "mean_latency_us": round(self.mean_latency_us, 3),
            "p95_latency_us": round(self.p95_latency_us, 3),
            "speedup": round(self.speedup, 2) if self.speedup is not None else None,
            "reference_mean_us": round(self.reference_mean_us, 3) if self.reference_mean_us is not None else None,
            "reasons": self.reasons
        }


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
    iterations: int = 1000
) -> BenchmarkVerdict:
    """
    Evalúa una función contra un presupuesto de rendimiento y emite un veredicto explícito:
    - SHIP: Cumple presupuesto de latencia en tiempo real y no presenta regresión respecto a referencia.
    - NO_SHIP: Supera el presupuesto o es más lenta que la referencia.
    """
    b = budget or PerformanceBudget()
    target_times = run_workload(target_fn, iterations=iterations)

    mean_target = statistics.mean(target_times)
    min_target = min(target_times)
    max_target = max(target_times)
    sorted_times = sorted(target_times)
    p95_target = sorted_times[int(len(sorted_times) * 0.95)]

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
    if reference_fn:
        ref_times = run_workload(reference_fn, iterations=iterations)
        mean_ref = statistics.mean(ref_times)
        speedup = mean_ref / mean_target if mean_target > 0 else 1.0

        if speedup < b.min_speedup:
            verdict = "NO_SHIP"
            reasons.append(
                f"Aceleracion insuficiente ({speedup:.2f}x). Requerido minimo {b.min_speedup:.2f}x."
            )
        else:
            reasons.append(f"Aceleracion exitosa ({speedup:.2f}x vs referencia).")

    if verdict == "SHIP":
        reasons.insert(0, f"Dentro de presupuesto de tiempo real ({mean_target:.2f} us <= {b.max_latency_us:.2f} us).")

    return BenchmarkVerdict(
        name=name,
        verdict=verdict,
        mean_latency_us=mean_target,
        min_latency_us=min_target,
        max_latency_us=max_target,
        p95_latency_us=p95_target,
        speedup=speedup,
        reference_mean_us=mean_ref,
        reasons=reasons
    )
