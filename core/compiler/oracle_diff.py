"""
Harmos Oracle Diff Runner: Motor de verificación de equivalencia semántica (diff).
Inspirado en el estándar de verificación diferencial de rust-anything (diff).
Ejecuta casos de prueba (cases.jsonl) contra implementaciones destino,
comparando resultados con tolerancia de punto flotante y verificando rutas de error.
"""
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from core.compiler.oracle_harvest import TestCase


@dataclass
class DiffFailure:
    case: TestCase
    actual: Any
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fn": self.case.fn,
            "args": self.case.args,
            "expected": self.case.expected,
            "actual": self.actual,
            "tolerance": self.case.tolerance,
            "reason": self.reason
        }


@dataclass
class DiffReport:
    total_cases: int
    passed_cases: int
    failed_cases: int
    verdict: str  # "PASS" o "FAIL"
    failures: List[DiffFailure] = field(default_factory=list)
    details: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "failures": [f.to_dict() for f in self.failures],
            "details": self.details
        }


def compare_numeric_or_structure(expected: Any, actual: Any, tolerance: float = 1e-7) -> Tuple[bool, Optional[str]]:
    """
    Compara dos valores con soporte para tolerancias de coma flotante escalares
    y estructuras anidadas (listas, tuplas, diccionarios).
    """
    # 1. Ambos numéricos (int, float)
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        diff = abs(expected - actual)
        # Tolerancia combinada absoluta y relativa
        max_allowed = max(tolerance, abs(expected) * tolerance)
        if diff <= max_allowed:
            return True, None
        return False, f"Discrepancia numerica: esperado {expected}, obtenido {actual} (delta: {diff:.3e} > tol: {max_allowed:.3e})"

    # 2. Listas y Tuplas
    if isinstance(expected, (list, tuple)) and isinstance(actual, (list, tuple)):
        if len(expected) != len(actual):
            return False, f"Discrepancia en longitud: esperado {len(expected)} elementos, obtenido {len(actual)}"
        for idx, (exp_item, act_item) in enumerate(zip(expected, actual)):
            ok, reason = compare_numeric_or_structure(exp_item, act_item, tolerance)
            if not ok:
                return False, f"En indice [{idx}]: {reason}"
        return True, None

    # 3. Diccionarios
    if isinstance(expected, dict) and isinstance(actual, dict):
        if set(expected.keys()) != set(actual.keys()):
            return False, f"Discrepancia en claves: esperado {set(expected.keys())}, obtenido {set(actual.keys())}"
        for k in expected:
            ok, reason = compare_numeric_or_structure(expected[k], actual[k], tolerance)
            if not ok:
                return False, f"En clave '{k}': {reason}"
        return True, None

    # 4. Igualdad exacta por omisión (strings, booleans, etc.)
    if expected == actual:
        return True, None

    return False, f"Discrepancia de valores: esperado {expected} ({type(expected).__name__}), obtenido {actual} ({type(actual).__name__})"


def evaluate_diff(
    cases: List[TestCase],
    target_registry: Dict[str, Callable[..., Any]]
) -> DiffReport:
    """
    Ejecuta una lista de TestCase contra las funciones registradas en target_registry.
    Devuelve un DiffReport con veredicto PASS o FAIL y diagnóstico de fallos.
    """
    total = len(cases)
    passed = 0
    failures: List[DiffFailure] = []

    for case in cases:
        fn_name = case.fn
        target_fn = target_registry.get(fn_name)

        if target_fn is None:
            failures.append(DiffFailure(
                case=case,
                actual=None,
                reason=f"Funcion objetivo '{fn_name}' no encontrada en el registro de evaluacion."
            ))
            continue

        try:
            actual_result = target_fn(*case.args)
            
            # Si el caso esperaba un error pero devolvió un resultado exitoso
            if case.error is not None:
                failures.append(DiffFailure(
                    case=case,
                    actual=actual_result,
                    reason=f"Ruta de error omitida: se esperaba error '{case.error}' pero la funcion retorno {actual_result}"
                ))
                continue

            # Comparar resultado
            ok, reason = compare_numeric_or_structure(case.expected, actual_result, case.tolerance)
            if ok:
                passed += 1
            else:
                failures.append(DiffFailure(
                    case=case,
                    actual=actual_result,
                    reason=reason or "Discrepancia desconocida"
                ))

        except Exception as e:
            err_str = f"{type(e).__name__}: {str(e)}"
            # Si el caso esperaba un error, verificar coincidencia
            if case.error is not None:
                if case.error.lower() in err_str.lower() or type(e).__name__.lower() in case.error.lower():
                    passed += 1
                else:
                    failures.append(DiffFailure(
                        case=case,
                        actual=err_str,
                        reason=f"Error inesperado: esperado '{case.error}', capturado '{err_str}'"
                    ))
            else:
                failures.append(DiffFailure(
                    case=case,
                    actual=err_str,
                    reason=f"Excepcion no controlada: {err_str}"
                ))

    verdict = "PASS" if passed == total and total > 0 else "FAIL"
    details = [
        f"Evaluacion semantica: {passed}/{total} casos aprobados.",
        f"Veredicto: {verdict}"
    ]
    if failures:
        details.append(f"Se registraron {len(failures)} discrepancias o errores no esperados.")

    return DiffReport(
        total_cases=total,
        passed_cases=passed,
        failed_cases=len(failures),
        verdict=verdict,
        failures=failures,
        details=details
    )
