"""
Downstream Pilot Benchmark Suites & C++ Kernel Harnesses (ADR-0001).

Keeps domain-specific mathematical references (Truax, Wilson, Hexslider) out of
`core/compiler/` while supplying harvest/diff registries and headless C++ harness
generators for Harmos pilot benchmarks.
"""
from typing import Any, Callable, Dict, List, Optional

from core.compiler.cpp_headless_runner import register_kernel_generator, wrap_try_catch
from core.compiler.oracle_harvest import TestCase, harvest_from_callable


def wilson_reduce_to_octave(ratio: float) -> float:
    """Reduce an interval ratio to the octave [1.0, 2.0)."""
    if ratio <= 0.0:
        return 1.0
    while ratio >= 2.0:
        ratio /= 2.0
    while ratio < 1.0:
        ratio *= 2.0
    return ratio


def ref_hex_freq(col: int, row: int) -> float:
    """Reference cell frequency for a 31-EDO Wilson hexagonal keyboard cell."""
    base_freq = 261.625565
    edo = 31.0
    step_x = 1
    step_y = 5
    step_count = col * step_x + row * step_y
    return base_freq * (2.0 ** (step_count / edo))


def ref_hex_hit(x: float, y: float) -> int:
    """Reference hit-test for the Wilson hexagonal lattice."""
    r = 12.0
    cols = 39
    rows = 25
    sqrt3 = 1.732050807568877
    h_spacing = r * 1.5
    v_spacing = r * sqrt3
    idx = 0
    for row in range(rows):
        for col in range(cols):
            cx = col * h_spacing + r
            cy = row * v_spacing + (v_spacing * 0.5 if col % 2 == 1 else 0.0) + (r * sqrt3 * 0.5)
            dx = x - cx
            dy = y - cy
            if (dx * dx + dy * dy) <= (r * r * 0.85):
                return idx
            idx += 1
    return -1


def harvest_suite_cases(suite: str, tolerance: float = 1e-7) -> List[TestCase]:
    """Harvest semantic test vectors for a pilot suite (`truax`, `wilson`, `hexslider`)."""
    cases: List[TestCase] = []
    if suite == "truax":
        from benchmarks.truax_fm.microtonal_engine import MicrotonalEngine

        eng = MicrotonalEngine()
        truax_inputs = [
            [1.0, 1.0], [1.0, 2.0], [3.0, 2.0], [5.0, 3.0], [7.0, 4.0], [9.0, 5.0]
        ]
        cases.extend(harvest_from_callable(eng.to_normal_form, "to_normal_form", truax_inputs, tolerance=tolerance))
        carrier_inputs = [
            [220.0, 1.0, 1.0], [220.0, 3.0, 2.0], [440.0, 5.0, 3.0]
        ]
        cases.extend(harvest_from_callable(eng.calc_carrier_freq, "calc_carrier_freq", carrier_inputs, tolerance=tolerance))
    elif suite == "wilson":
        w_inputs = [[0.5], [1.0], [1.5], [2.0], [3.0], [5.0], [7.0]]
        cases.extend(harvest_from_callable(wilson_reduce_to_octave, "reduce_to_octave", w_inputs, tolerance=tolerance))
    elif suite == "hexslider":
        freq_inputs = [[0, 0], [1, 0], [0, 1], [5, 2], [10, 4]]
        cases.extend(harvest_from_callable(ref_hex_freq, "compute_cell_frequency", freq_inputs, tolerance=tolerance))
        hit_inputs = [[12.0, 10.392], [0.0, 0.0], [30.0, 20.784], [500.0, 500.0]]
        cases.extend(harvest_from_callable(ref_hex_hit, "hit_test", hit_inputs, tolerance=tolerance))
    return cases


def get_diff_registry(suite: str) -> Dict[str, Callable[..., Any]]:
    """Return reference Python callables for a pilot differential suite."""
    registry: Dict[str, Callable[..., Any]] = {}
    if suite == "truax":
        from benchmarks.truax_fm.microtonal_engine import MicrotonalEngine

        eng = MicrotonalEngine()
        registry["to_normal_form"] = eng.to_normal_form
        registry["calc_carrier_freq"] = eng.calc_carrier_freq
    elif suite == "wilson":
        registry["reduce_to_octave"] = wilson_reduce_to_octave
    elif suite == "hexslider":
        registry["compute_cell_frequency"] = ref_hex_freq
        registry["hit_test"] = ref_hex_hit
    return registry


def _generate_wilson_kernel(cases: List[TestCase], _type_name: Optional[str] = None) -> List[str]:
    lines: List[str] = []
    for idx, c in enumerate(cases):
        arg0 = c.args[0] if c.args else 1.0
        expr = f"harmos::kernels::wilson::WilsonKernel::reduce_to_octave({float(arg0)})"
        lines.extend(wrap_try_catch(expr, idx, "double"))
    return lines


def _generate_hexslider_kernel(cases: List[TestCase], _type_name: Optional[str] = None) -> List[str]:
    lines = ["    harmos::kernels::wilson::HexsliderKernel kernel;"]
    for idx, c in enumerate(cases):
        if c.fn == "hit_test":
            arg0 = c.args[0] if len(c.args) > 0 else 0.0
            arg1 = c.args[1] if len(c.args) > 1 else 0.0
            expr = f"kernel.hit_test({float(arg0)}, {float(arg1)})"
            lines.extend(wrap_try_catch(expr, idx, "int"))
        else:
            arg0 = c.args[0] if len(c.args) > 0 else 0
            arg1 = c.args[1] if len(c.args) > 1 else 0
            expr = f"kernel.compute_cell_frequency({int(arg0)}, {int(arg1)})"
            lines.extend(wrap_try_catch(expr, idx, "double"))
    return lines


def _generate_truax_kernel(cases: List[TestCase], _type_name: Optional[str] = None) -> List[str]:
    lines: List[str] = []
    for idx, c in enumerate(cases):
        if c.fn == "to_normal_form":
            arg0 = c.args[0] if len(c.args) > 0 else 1.0
            arg1 = c.args[1] if len(c.args) > 1 else 1.0
            expr = f"harmos::kernels::truax::TruaxKernel::to_normal_form({float(arg0)}, {float(arg1)})"
            lines.extend(wrap_try_catch(expr, idx, "auto", is_vector=True))
        else:
            arg0 = c.args[0] if len(c.args) > 0 else 220.0
            arg1 = c.args[1] if len(c.args) > 1 else 1.0
            arg2 = c.args[2] if len(c.args) > 2 else 1.0
            expr = f"harmos::kernels::truax::TruaxKernel::calc_carrier_freq({float(arg0)}, {float(arg1)}, {float(arg2)})"
            lines.extend(wrap_try_catch(expr, idx, "double"))
    return lines


def register_pilot_kernels() -> None:
    """Register downstream pilot C++ harness generators on demand."""
    register_kernel_generator("wilson", _generate_wilson_kernel)
    register_kernel_generator("hexslider", _generate_hexslider_kernel)
    register_kernel_generator("truax", _generate_truax_kernel)
