"""
Harmos Oracle Harvester: Captura y serialización de vectores de prueba semánticos (cases.jsonl).
Inspirado en el estándar de oráculo ejecutable de rust-anything (cases.jsonl).
Permite capturar entradas y salidas esperadas a partir de suites de tests existentes,
código de referencia o generadores de casos de borde sintéticos.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


@dataclass
class TestCase:
    """Representa un caso de prueba individual del oráculo semántico."""
    fn: str
    args: List[Any]
    expected: Optional[Any] = None
    tolerance: float = 1e-7
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "fn": self.fn,
            "args": self.args,
        }
        if self.expected is not None:
            d["expected"] = self.expected
        if self.error is not None:
            d["error"] = self.error
        if self.tolerance != 1e-7:
            d["tolerance"] = self.tolerance
        if self.metadata:
            d["metadata"] = self.metadata
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestCase":
        return cls(
            fn=data["fn"],
            args=data.get("args", []),
            expected=data.get("expected"),
            tolerance=data.get("tolerance", 1e-7),
            error=data.get("error"),
            metadata=data.get("metadata", {})
        )


def write_cases_jsonl(cases: List[TestCase], output_path: Union[Path, str]) -> int:
    """Escribe una lista de TestCase en formato JSON Lines (cases.jsonl)."""
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case.to_dict(), ensure_ascii=False) + "\n")
    return len(cases)


def read_cases_jsonl(input_path: Union[Path, str]) -> List[TestCase]:
    """Lee y valida un archivo cases.jsonl."""
    p = Path(input_path)
    if not p.is_file():
        raise FileNotFoundError(f"Archivo de casos no encontrado: {p}")

    cases = []
    with open(p, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                data = json.loads(line_str)
                cases.append(TestCase.from_dict(data))
            except Exception as e:
                raise ValueError(f"Error en linea {idx} de {p.name}: {e}")
    return cases


def harvest_from_callable(
    fn: Callable[..., Any],
    fn_name: str,
    inputs_list: List[List[Any]],
    tolerance: float = 1e-7,
    metadata: Optional[Dict[str, Any]] = None
) -> List[TestCase]:
    """
    Ejecuta una función de referencia sobre una lista de argumentos y
    cosecha los valores de retorno (o excepciones) como oráculo determinista.
    """
    cases = []
    meta = metadata or {}
    for args in inputs_list:
        try:
            result = fn(*args)
            cases.append(TestCase(
                fn=fn_name,
                args=args,
                expected=result,
                tolerance=tolerance,
                metadata=meta
            ))
        except Exception as err:
            cases.append(TestCase(
                fn=fn_name,
                args=args,
                error=f"{type(err).__name__}: {str(err)}",
                tolerance=tolerance,
                metadata=meta
            ))
    return cases


def generate_numeric_edge_cases(
    fn: Callable[..., Any],
    fn_name: str,
    base_args: List[Any],
    arg_indices_to_fuzz: Optional[List[int]] = None
) -> List[TestCase]:
    """
    Genera casos de borde sintéticos para funciones numéricas:
    - 0.0, -0.0
    - 1.0, -1.0
    - Valores fraccionarios extremos (1e-6, 1e6)
    """
    indices = arg_indices_to_fuzz if arg_indices_to_fuzz is not None else list(range(len(base_args)))
    fuzz_values = [0.0, 1.0, -1.0, 0.5, 2.0, 1e-4]

    variations = []
    for idx in indices:
        for val in fuzz_values:
            args_copy = list(base_args)
            args_copy[idx] = val
            variations.append(args_copy)

    return harvest_from_callable(
        fn=fn,
        fn_name=fn_name,
        inputs_list=variations,
        metadata={"generated_type": "numeric_edge_case"}
    )
