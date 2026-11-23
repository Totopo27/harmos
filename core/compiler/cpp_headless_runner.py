"""
Harmos Decoupled C++ Headless Test Runner.
Permite compilar y verificar kernels C++ puros sin depender del SDK de Max ni de Max.exe.

Proporciona detección de compilador host (g++, clang++, cl), generación de arnés
de prueba C++ a partir de vectores de prueba (cases.jsonl) y evaluación con
tolerancia escalar mediante el oráculo semántico.
"""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from core.compiler.oracle_diff import DiffFailure, DiffReport, compare_numeric_or_structure
from core.compiler.oracle_harvest import TestCase

KernelGenerator = Callable[[List[TestCase], Optional[str]], List[str]]
_KERNEL_GENERATORS: Dict[str, KernelGenerator] = {}


def register_kernel_generator(archetype: str, generator: KernelGenerator) -> None:
    """Registra un generador de código de arnés para un arquetipo de kernel dado."""
    _KERNEL_GENERATORS[archetype] = generator


def find_cpp_compiler() -> Optional[str]:
    """
    Localiza un compilador C++ compatible en el entorno host.
    Prioridad: g++, clang++, cl.
    """
    for candidate in ["g++", "clang++", "cl"]:
        found = shutil.which(candidate)
        if found:
            return candidate
    return None


def compile_cpp_executable(
    source_path: Union[str, Path],
    output_exe: Union[str, Path],
    include_dirs: Optional[List[Union[str, Path]]] = None,
    compiler_path: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Compila un archivo C++ fuente en un ejecutable binario autónomo bajo estándar C++17.
    Devuelve (éxito, mensajes de salida/error).
    """
    compiler = compiler_path or find_cpp_compiler()
    if not compiler:
        return False, "No se encontro ningun compilador C++ disponible en el PATH (g++, clang++, cl)."

    src = Path(source_path).resolve()
    out = Path(output_exe).resolve()

    inc_dirs = [Path(d).resolve() for d in (include_dirs or [])]

    is_msvc = "cl" in Path(compiler).name.lower()

    if is_msvc:
        cmd = [compiler, "/std:c++17", "/EHsc", "/O2", f"/Fe:{str(out)}", str(src)]
        for inc in inc_dirs:
            cmd.append(f"/I{str(inc)}")
    else:
        cmd = [compiler, "-std=c++17", "-O2", "-o", str(out), str(src)]
        for inc in inc_dirs:
            cmd.append(f"-I{str(inc)}")

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output_msg = proc.stderr if proc.stderr else proc.stdout
        return (proc.returncode == 0), output_msg
    except Exception as e:
        return False, f"Error al invocar compilador {compiler}: {e}"


def _wrap_try_catch(expr_str: str, idx: int, out_type: str = "double", is_vector: bool = False) -> List[str]:
    """Genera un bloque try/catch en C++ que serializa el resultado o la excepción a JSON."""
    lines = [
        "    try {",
        f"        {out_type} out_val = {expr_str};"
    ]
    if is_vector:
        lines.append(f'        std::cout << "{{\\"id\\": {idx}, \\"status\\": \\"ok\\", \\"actual\\": [" << out_val.first << ", " << out_val.second << "]}}\\n";')
    else:
        lines.append(f'        std::cout << "{{\\"id\\": {idx}, \\"status\\": \\"ok\\", \\"actual\\": " << out_val << "}}\\n";')
    lines.extend([
        "    } catch (const std::exception& e) {",
        f'        std::cout << "{{\\"id\\": {idx}, \\"status\\": \\"error\\", \\"error\\": \\"" << e.what() << "\\"}}\\n";',
        "    } catch (...) {",
        f'        std::cout << "{{\\"id\\": {idx}, \\"status\\": \\"error\\", \\"error\\": \\"unknown_exception\\"}}\\n";',
        "    }"
    ])
    return lines


def _generate_wilson_kernel(cases: List[TestCase], _type_name: Optional[str] = None) -> List[str]:
    lines = []
    for idx, c in enumerate(cases):
        arg0 = c.args[0] if c.args else 1.0
        expr = f"harmos::kernels::wilson::WilsonKernel::reduce_to_octave({float(arg0)})"
        lines.extend(_wrap_try_catch(expr, idx, "double"))
    return lines


def _generate_hexslider_kernel(cases: List[TestCase], _type_name: Optional[str] = None) -> List[str]:
    lines = ["    harmos::kernels::wilson::HexsliderKernel kernel;"]
    for idx, c in enumerate(cases):
        if c.fn == "hit_test":
            arg0 = c.args[0] if len(c.args) > 0 else 0.0
            arg1 = c.args[1] if len(c.args) > 1 else 0.0
            expr = f"kernel.hit_test({float(arg0)}, {float(arg1)})"
            lines.extend(_wrap_try_catch(expr, idx, "int"))
        else:
            arg0 = c.args[0] if len(c.args) > 0 else 0
            arg1 = c.args[1] if len(c.args) > 1 else 0
            expr = f"kernel.compute_cell_frequency({int(arg0)}, {int(arg1)})"
            lines.extend(_wrap_try_catch(expr, idx, "double"))
    return lines


def _generate_truax_kernel(cases: List[TestCase], _type_name: Optional[str] = None) -> List[str]:
    lines = []
    for idx, c in enumerate(cases):
        if c.fn == "to_normal_form":
            arg0 = c.args[0] if len(c.args) > 0 else 1.0
            arg1 = c.args[1] if len(c.args) > 1 else 1.0
            expr = f"harmos::kernels::truax::TruaxKernel::to_normal_form({float(arg0)}, {float(arg1)})"
            lines.extend(_wrap_try_catch(expr, idx, "auto", is_vector=True))
        else:
            arg0 = c.args[0] if len(c.args) > 0 else 220.0
            arg1 = c.args[1] if len(c.args) > 1 else 1.0
            arg2 = c.args[2] if len(c.args) > 2 else 1.0
            expr = f"harmos::kernels::truax::TruaxKernel::calc_carrier_freq({float(arg0)}, {float(arg1)}, {float(arg2)})"
            lines.extend(_wrap_try_catch(expr, idx, "double"))
    return lines


def _generate_dsp_kernel(cases: List[TestCase], kernel_type_name: Optional[str] = None) -> List[str]:
    type_name = kernel_type_name or "harmos_demoKernel"
    lines = [f"    harmos::kernels::{type_name} kernel;"]
    for idx, c in enumerate(cases):
        arg0 = c.args[0] if len(c.args) > 0 else 0.0
        arg1 = c.args[1] if len(c.args) > 1 else 1.0
        expr = f"kernel.process_sample({float(arg0)}f, {float(arg1)})"
        lines.extend(_wrap_try_catch(expr, idx, "float"))
    return lines


def _generate_control_kernel(cases: List[TestCase], kernel_type_name: Optional[str] = None) -> List[str]:
    type_name = kernel_type_name or "harmos_demoKernel"
    lines = [f"    harmos::kernels::{type_name} kernel;"]
    for idx, c in enumerate(cases):
        arg0 = c.args[0] if c.args else 0.0
        expr = f"kernel.process_scalar({float(arg0)})"
        lines.extend(_wrap_try_catch(expr, idx, "double"))
    return lines


register_kernel_generator("wilson", _generate_wilson_kernel)
register_kernel_generator("hexslider", _generate_hexslider_kernel)
register_kernel_generator("truax", _generate_truax_kernel)
register_kernel_generator("dsp", _generate_dsp_kernel)
register_kernel_generator("control", _generate_control_kernel)


def generate_cpp_harness(
    kernel_header_path: Union[str, Path],
    cases: List[TestCase],
    kernel_class: str = "wilson",
    kernel_type_name: Optional[str] = None
) -> str:
    """
    Genera el código fuente C++ del arnés de prueba autónomo para evaluar los casos.
    Emite resultados de cada caso en formato JSON por stdout para consumo del oráculo.
    """
    header_posix = Path(kernel_header_path).resolve().as_posix()

    lines = [
        "// =============================================================================",
        "// Harmos Headless Test Harness (Autogenerated)",
        "// =============================================================================",
        "#include <iostream>",
        "#include <iomanip>",
        "#include <vector>",
        "#include <string>",
        "#include <cmath>",
        "#include <exception>",
        f'#include "{header_posix}"',
        "",
        "int main() {",
        "    std::cout << std::setprecision(17);",
        ""
    ]

    generator = _KERNEL_GENERATORS.get(kernel_class, _KERNEL_GENERATORS["control"])
    lines.extend(generator(cases, kernel_type_name))

    lines.extend([
        "",
        "    return 0;",
        "}",
        ""
    ])
    return "\n".join(lines)


def execute_headless_binary(
    binary_path: Union[str, Path],
    timeout_sec: float = 10.0
) -> Tuple[Optional[str], Optional[str]]:
    """
    Ejecuta el binario C++ compilado con timeout.
    Retorna (stdout, error_message).
    """
    try:
        proc = subprocess.run(
            [str(binary_path)],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False
        )
        return proc.stdout, None
    except subprocess.TimeoutExpired:
        return None, f"Timeout ({timeout_sec}s) alcanzado durante la ejecucion del kernel C++."
    except Exception as e:
        return None, f"Error al ejecutar arnes C++ binario: {e}"


def parse_headless_output(stdout: str) -> Tuple[Dict[int, Dict[str, Any]], List[str]]:
    """
    Parsea las líneas JSON emitidas por el arnés C++.
    Retorna (outputs_by_id, parse_errors).
    """
    outputs_by_id: Dict[int, Dict[str, Any]] = {}
    parse_errors: List[str] = []

    for line_num, line in enumerate(stdout.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        if line.startswith("{"):
            if not line.endswith("}"):
                parse_errors.append(f"Linea {line_num}: JSON truncado o incompleto: {line}")
                continue
            try:
                data = json.loads(line)
                if "id" in data:
                    outputs_by_id[data["id"]] = data
                else:
                    parse_errors.append(f"Linea {line_num}: JSON sin campo 'id': {line}")
            except Exception as e:
                parse_errors.append(f"Linea {line_num}: Error al parsear JSON ({e}): {line}")
        else:
            # Línea informativa o log fuera de formato JSON
            pass

    return outputs_by_id, parse_errors


def evaluate_headless_cases(
    cases: List[TestCase],
    outputs_by_id: Dict[int, Dict[str, Any]],
    parse_errors: Optional[List[str]] = None
) -> Tuple[int, int, List[DiffFailure]]:
    """
    Compara las salidas producidas por el arnés C++ contra los casos esperados.
    Retorna (passed_count, failed_count, failures_list).
    """
    passed = 0
    failed = 0
    failures: List[DiffFailure] = []

    for idx, c in enumerate(cases):
        if idx not in outputs_by_id:
            failed += 1
            failures.append(DiffFailure(
                case=c,
                actual=None,
                reason="Sin salida producida por el arnes C++ (posible crash o excepcion no capturada)"
            ))
            continue

        item = outputs_by_id[idx]
        if item.get("status") != "ok":
            failed += 1
            failures.append(DiffFailure(
                case=c,
                actual=None,
                reason=f"Excepcion en C++: {item.get('error', 'desconocido')}"
            ))
            continue

        actual_val = item.get("actual")
        ok, reason = compare_numeric_or_structure(c.expected, actual_val, tolerance=c.tolerance)
        if ok:
            passed += 1
        else:
            failed += 1
            failures.append(DiffFailure(
                case=c,
                actual=actual_val,
                reason=reason or "Discrepancia numerica desconocida"
            ))

    return passed, failed, failures


def run_headless_cases(
    kernel_header_path: Union[str, Path],
    cases: List[TestCase],
    kernel_class: str = "wilson",
    kernel_type_name: Optional[str] = None,
    compiler: Optional[str] = None,
    timeout_sec: float = 10.0
) -> DiffReport:
    """
    Ejecuta casos de prueba headless contra un kernel C++ desacoplado.
    Compila el arnés con el compilador del host y evalúa los resultados con tolerancia.
    """
    chosen_compiler = compiler or find_cpp_compiler()
    if not chosen_compiler:
        return DiffReport(
            total_cases=len(cases),
            passed_cases=0,
            failed_cases=len(cases),
            verdict="BLOCKED (COMPILER_UNAVAILABLE)",
            failures=[],
            details=["Compilador C++ (g++, clang++, cl) no disponible en el host para ejecucion headless."]
        )

    header_path = Path(kernel_header_path).resolve()
    if not header_path.is_file():
        return DiffReport(
            total_cases=len(cases),
            passed_cases=0,
            failed_cases=len(cases),
            verdict="FAIL",
            failures=[],
            details=[f"Header de kernel C++ no encontrado: {header_path}"]
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        harness_src = Path(tmpdir) / "harness.cpp"
        harness_exe = Path(tmpdir) / ("harness.exe" if os.name == "nt" else "harness")

        code = generate_cpp_harness(
            header_path,
            cases,
            kernel_class=kernel_class,
            kernel_type_name=kernel_type_name
        )
        harness_src.write_text(code, encoding="utf-8")

        include_dirs = [header_path.parent]
        ok_compile, compile_msg = compile_cpp_executable(
            harness_src,
            harness_exe,
            include_dirs=include_dirs,
            compiler_path=chosen_compiler
        )
        if not ok_compile:
            return DiffReport(
                total_cases=len(cases),
                passed_cases=0,
                failed_cases=len(cases),
                verdict="FAIL",
                failures=[],
                details=[f"Fallo de compilacion del arnes C++ con {chosen_compiler}: {compile_msg}"]
            )

        stdout, err = execute_headless_binary(harness_exe, timeout_sec=timeout_sec)
        if err or stdout is None:
            return DiffReport(
                total_cases=len(cases),
                passed_cases=0,
                failed_cases=len(cases),
                verdict="FAIL",
                failures=[],
                details=[err or "Ejecucion C++ headless retorno salida vacia."]
            )

        outputs_by_id, parse_errors = parse_headless_output(stdout)
        passed, failed, failures = evaluate_headless_cases(cases, outputs_by_id, parse_errors)

        verdict = "PASS" if failed == 0 else "FAIL"
        details = [
            f"Compilador utilizado: {chosen_compiler}",
            f"Header evaluado: {header_path.name}",
            f"Casos evaluados: {len(cases)} ({passed} exitosos, {failed} fallidos)",
            f"Veredicto: {verdict} (SEMANTICO HEADLESS)"
        ]
        if parse_errors:
            details.extend(parse_errors[:5])

        return DiffReport(
            total_cases=len(cases),
            passed_cases=passed,
            failed_cases=failed,
            verdict=verdict,
            failures=failures,
            details=details
        )
