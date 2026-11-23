"""
Harmos CLI Compiler: Sintetizador de paquetes Max MSP a partir de Representaciones Intermedias (IR).
Genera parches .maxpat validados con TypedPatch y esqueletos C++ Min-Devkit con CMakeLists.txt.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from core.compiler.typed_patch import TypedPatch
from core.compiler.contract_engine import ContractEngine
from core.compiler.ast_extractor import extract_ir_from_file
from core.compiler.cpp_generator import generate_cpp_kernel, generate_min_wrapper
from core.compiler.maxref_generator import write_maxref_file
from core.compiler.oracle_harvest import (
    write_cases_jsonl,
    read_cases_jsonl,
    harvest_from_callable
)
from core.compiler.oracle_diff import evaluate_diff
from core.compiler.provenance import (
    build_provenance_record,
    write_provenance_file,
    verify_provenance
)


def handle_extract(source_file: str, output_path: str, object_name: str = None) -> Dict[str, Any]:
    """Extrae la IR desde código fuente y la persiste como JSON."""
    ir_data = extract_ir_from_file(source_file, object_name=object_name)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ir_data, f, indent=4)
    return {
        "success": True,
        "object_name": ir_data["object_name"],
        "ir_path": output_path
    }


def generate_cpp_min_devkit(ir: Dict[str, Any], output_path: str, kernel_path: Optional[str] = None) -> str:
    """
    Genera la implementación C++ desacoplada:
    1. Kernel C++ puro ({object}_kernel.hpp): 0 dependencias de Max SDK.
    2. Wrapper delgado ({object}.cpp): Capa Min-Devkit que aloja el kernel.
    """
    if not kernel_path:
        base_dir = os.path.dirname(os.path.abspath(output_path))
        object_name = ir.get("object_name", "my_object")
        kernel_path = os.path.join(base_dir, f"{object_name}_kernel.hpp")

    # 1. Generar Kernel Puro
    kernel_code = generate_cpp_kernel(ir)
    with open(kernel_path, "w", encoding="utf-8") as f:
        f.write(kernel_code)

    # 2. Generar Wrapper Min-Devkit
    kernel_header_name = os.path.basename(kernel_path)
    wrapper_code = generate_min_wrapper(ir, kernel_header_name)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(wrapper_code)

    return kernel_path


def resolve_min_api_dir(explicit_path: Optional[str] = None) -> Path:
    """Resuelve la ruta al directorio source/min-api de Min-DevKit sin hardcodear rutas de host."""
    if explicit_path:
        p = Path(explicit_path)
        if p.is_dir():
            return p.resolve()
        raise FileNotFoundError(f"Ruta de Min-DevKit especificada no existe: {explicit_path}")

    env_min = os.environ.get("C74_MIN_API_DIR")
    if env_min and Path(env_min).is_dir():
        return Path(env_min).resolve()

    env_devkit = os.environ.get("MIN_DEVKIT_DIR")
    if env_devkit:
        candidate = Path(env_devkit) / "source" / "min-api"
        if candidate.is_dir():
            return candidate.resolve()

    # Raiz del repositorio: c74support/min-devkit/source/min-api
    repo_root = Path(__file__).resolve().parent.parent.parent
    candidate = repo_root / "c74support" / "min-devkit" / "source" / "min-api"
    if candidate.is_dir():
        return candidate.resolve()

    raise FileNotFoundError(
        "No se pudo localizar el directorio source/min-api de Min-DevKit. "
        "Configure la variable de entorno MIN_DEVKIT_DIR o C74_MIN_API_DIR."
    )


def generate_cmakelists(object_name: str, output_path: str, min_api_dir: Optional[str] = None) -> None:
    content = f"""cmake_minimum_required(VERSION 3.15)

if (NOT DEFINED C74_MIN_API_DIR)
    if (DEFINED ENV{{C74_MIN_API_DIR}})
        set(C74_MIN_API_DIR "$ENV{{C74_MIN_API_DIR}}")
    elseif (DEFINED ENV{{MIN_DEVKIT_DIR}})
        set(C74_MIN_API_DIR "$ENV{{MIN_DEVKIT_DIR}}/source/min-api")
    else ()
        find_path(C74_MIN_API_DIR NAMES script/min-pretarget.cmake
            PATHS
            "${{CMAKE_CURRENT_SOURCE_DIR}}/c74support/min-devkit/source/min-api"
            "${{CMAKE_CURRENT_SOURCE_DIR}}/../c74support/min-devkit/source/min-api"
            "${{CMAKE_CURRENT_SOURCE_DIR}}/../../c74support/min-devkit/source/min-api"
            "${{CMAKE_CURRENT_SOURCE_DIR}}/../../../c74support/min-devkit/source/min-api"
        )
    endif ()
endif ()

if (NOT DEFINED C74_LIBRARY_OUTPUT_DIRECTORY)
    set(C74_LIBRARY_OUTPUT_DIRECTORY "${{CMAKE_CURRENT_SOURCE_DIR}}")
endif ()

include("${{C74_MIN_API_DIR}}/script/min-pretarget.cmake")

project({object_name})
set({object_name}_EXTERN_OUTPUT_NAME "{object_name}")

include_directories(
    "${{C74_INCLUDES}}"
    "${{CMAKE_CURRENT_SOURCE_DIR}}"
)

set(SOURCE_FILES
    {object_name}.cpp
)

add_library(
    {object_name}
    MODULE
    ${{SOURCE_FILES}}
)

include("${{C74_MIN_API_DIR}}/script/min-posttarget.cmake")

if (WIN32)
    target_link_libraries({object_name} PUBLIC ${{MaxAPI_LIB}} ${{MaxAudio_LIB}} ${{Jitter_LIB}})
endif ()
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


def build_external(
    output_dir: str,
    object_name: str,
    min_api_dir: Optional[str] = None
) -> str:
    """
    Configura y compila el external nativo (.mxe64 en Windows) usando CMake y Min-DevKit.
    Coloca el binario resultante en output_dir (junto al patcher) y en output_dir/externals/.
    """
    out_p = Path(output_dir).resolve()
    resolved_min_api = resolve_min_api_dir(min_api_dir)

    cmake_bin = shutil.which("cmake")
    if not cmake_bin:
        raise RuntimeError(
            "cmake no fue detectado en PATH. Se requiere CMake para construir el external nativo."
        )

    build_dir = out_p / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    posix_out = out_p.as_posix()
    posix_min_api = resolved_min_api.as_posix()

    cfg_cmd = [
        cmake_bin,
        "-S", str(out_p),
        "-B", str(build_dir),
        f"-DC74_MIN_API_DIR={posix_min_api}",
        f"-DC74_LIBRARY_OUTPUT_DIRECTORY={posix_out}"
    ]

    if sys.platform == "win32":
        cfg_cmd.extend(["-G", "Visual Studio 17 2022", "-A", "x64"])

    res_cfg = subprocess.run(cfg_cmd, capture_output=True, text=True)
    if res_cfg.returncode != 0:
        if sys.platform == "win32" and "-G" in cfg_cmd:
            fallback_cmd = [
                cmake_bin,
                "-S", str(out_p),
                "-B", str(build_dir),
                f"-DC74_MIN_API_DIR={posix_min_api}",
                f"-DC74_LIBRARY_OUTPUT_DIRECTORY={posix_out}"
            ]
            res_cfg = subprocess.run(fallback_cmd, capture_output=True, text=True)

    if res_cfg.returncode != 0:
        raise RuntimeError(
            f"Fallo al configurar CMake para '{object_name}':\n{res_cfg.stderr or res_cfg.stdout}"
        )

    bld_cmd = [
        cmake_bin,
        "--build", str(build_dir),
        "--config", "Release"
    ]
    res_bld = subprocess.run(bld_cmd, capture_output=True, text=True)
    if res_bld.returncode != 0:
        raise RuntimeError(
            f"Fallo al compilar '{object_name}' con CMake:\n{res_bld.stderr or res_bld.stdout}"
        )

    ext_suffix = ".mxe64" if sys.platform == "win32" else ".mxo"
    expected_name = f"{object_name}{ext_suffix}"

    candidate = out_p / expected_name
    if not candidate.is_file():
        found = list(build_dir.rglob(f"*{ext_suffix}"))
        if found:
            shutil.copy2(found[0], candidate)

    if not candidate.is_file():
        raise FileNotFoundError(
            f"La compilacion finalizo pero no se encontro el binario '{expected_name}' en {out_p}."
        )

    pkg_externals = out_p / "externals"
    pkg_externals.mkdir(parents=True, exist_ok=True)
    pkg_candidate = pkg_externals / expected_name
    if not pkg_candidate.is_file() or candidate.resolve() != pkg_candidate.resolve():
        shutil.copy2(candidate, pkg_candidate)

    return str(candidate)


def generate_test_maxpat(ir: Dict[str, Any], output_path: str) -> None:
    object_name = ir.get("object_name", "my_object")
    patch = TypedPatch(ContractEngine.from_ir({**ir, "object_name": object_name}))

    # Caja del objeto sintetizado
    obj_box = patch.add_box(object_name, x=150.0, y=100.0)

    # Añadir generador o estímulo según el primer inlet
    inlets = ir.get("inlets", [])
    if inlets:
        first_type = inlets[0].get("type", "anything")
        if first_type == "signal":
            src = patch.add_box("cycle~ 220", x=150.0, y=40.0)
            patch.connect(src, 0, obj_box, 0)
        elif first_type in ["float", "int", "number"]:
            src = patch.add_box("flonum", x=150.0, y=40.0)
            patch.connect(src, 0, obj_box, 0)

    # Añadir monitor según el primer outlet
    outlets = ir.get("outlets", [])
    if outlets:
        first_out_type = outlets[0].get("type", "anything")
        if first_out_type == "signal":
            dac = patch.add_box("ezdac~", x=150.0, y=180.0)
            patch.connect(obj_box, 0, dac, 0)
            patch.connect(obj_box, 0, dac, 1)
        elif first_out_type in ["float", "int", "number"]:
            monitor = patch.add_box("flonum", x=150.0, y=180.0)
            patch.connect(obj_box, 0, monitor, 0)

    patch.save(output_path)


def handle_doc(
    ir_file_path: str,
    output_path: Optional[str] = None,
    author: str = "Harmos Meta-Compiler"
) -> str:
    """Extrae la especificación IR y sintetiza la documentación canónica .maxref.xml."""
    with open(ir_file_path, "r", encoding="utf-8") as f:
        ir_data = json.load(f)
    object_name = ir_data.get("object_name", "harmos_object")
    if not output_path:
        output_path = f"{object_name}.maxref.xml"
    elif os.path.isdir(output_path) or output_path.endswith("/") or output_path.endswith("\\"):
        output_path = os.path.join(output_path, f"{object_name}.maxref.xml")
    elif not output_path.endswith(".xml"):
        output_path = os.path.join(output_path, f"{object_name}.maxref.xml")

    return write_maxref_file(ir_data, output_path, author=author)


def compile_ir(
    ir_file_path: str,
    output_dir: str,
    source_path: Optional[str] = None,
    build: bool = False,
    min_api_dir: Optional[str] = None
) -> Dict[str, Any]:
    with open(ir_file_path, "r", encoding="utf-8") as f:
        ir_data = json.load(f)

    os.makedirs(output_dir, exist_ok=True)
    object_name = ir_data.get("object_name", "harmos_object")

    maxpat_path = os.path.join(output_dir, f"{object_name}_test.maxpat")
    cpp_path = os.path.join(output_dir, f"{object_name}.cpp")
    kernel_path = os.path.join(output_dir, f"{object_name}_kernel.hpp")
    cmake_path = os.path.join(output_dir, "CMakeLists.txt")

    docs_dir = os.path.join(output_dir, "docs")
    maxref_path = os.path.join(docs_dir, f"{object_name}.maxref.xml")
    flat_maxref_path = os.path.join(output_dir, f"{object_name}.maxref.xml")

    generate_test_maxpat(ir_data, maxpat_path)
    generate_cpp_min_devkit(ir_data, cpp_path, kernel_path=kernel_path)
    generate_cmakelists(object_name, cmake_path, min_api_dir=min_api_dir)
    write_maxref_file(ir_data, maxref_path)
    write_maxref_file(ir_data, flat_maxref_path)

    external_path: Optional[str] = None
    if build:
        external_path = build_external(output_dir, object_name, min_api_dir=min_api_dir)

    # Generar huella de procedencia criptografica (emitted-from.json)
    artifacts: Dict[str, Any] = {
        "maxpat": maxpat_path,
        "cpp": cpp_path,
        "kernel": kernel_path,
        "cmake": cmake_path,
        "maxref": maxref_path,
    }
    if external_path and os.path.exists(external_path):
        artifacts["external"] = external_path

    prov_record = build_provenance_record(
        ir_file_path,
        source_path=source_path,
        artifacts=artifacts
    )
    prov_path = write_provenance_file(output_dir, prov_record)

    res = {
        "success": True,
        "object_name": object_name,
        "maxpat_path": maxpat_path,
        "cpp_path": cpp_path,
        "kernel_path": kernel_path,
        "cmake_path": cmake_path,
        "maxref_path": maxref_path,
        "provenance_path": str(prov_path)
    }
    if external_path:
        res["external_path"] = external_path

    return res


# =============================================================================
# Funciones de Referencia Deduplicadas
# =============================================================================

def wilson_reduce_to_octave(ratio: float) -> float:
    """Reduce un intervalo a la octava [1.0, 2.0)."""
    if ratio <= 0.0:
        return 1.0
    while ratio >= 2.0:
        ratio /= 2.0
    while ratio < 1.0:
        ratio *= 2.0
    return ratio


def ref_hex_freq(col: int, row: int) -> float:
    """Frecuencia de referencia para una celda hexagonal en 31-EDO."""
    base_freq = 261.625565
    edo = 31.0
    step_x = 1
    step_y = 5
    step_count = col * step_x + row * step_y
    return base_freq * (2.0 ** (step_count / edo))


def ref_hex_hit(x: float, y: float) -> int:
    """Hit-test de referencia para cuadrícula hexagonal Wilson."""
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


# =============================================================================
# Subcommand Dispatch Handlers
# =============================================================================

def _dispatch_compile(args: argparse.Namespace) -> int:
    build_native = not args.no_build
    res = compile_ir(args.ir_file, args.out, source_path=args.source, build=build_native)
    print(f"Compilacion exitosa para: {res['object_name']}")
    print(f"  Patcher de prueba: {res['maxpat_path']}")
    print(f"  Fuente C++:        {res['cpp_path']}")
    print(f"  CMakeLists:        {res['cmake_path']}")
    print(f"  Maxref XML:        {res['maxref_path']}")
    print(f"  Procedencia:       {res['provenance_path']}")
    if res.get("external_path"):
        print(f"  External nativo:   {res['external_path']}")
    return 0


def _dispatch_doc(args: argparse.Namespace) -> int:
    out_file = handle_doc(args.ir_file, output_path=args.out, author=args.author)
    print(f"Documentacion Maxref generada con exito: {out_file}")
    return 0


def _dispatch_extract(args: argparse.Namespace) -> int:
    res = handle_extract(args.source_file, args.out, object_name=args.name)
    print(f"Extraccion exitosa para: {res['object_name']}")
    print(f"  Archivo IR generado: {res['ir_path']}")
    return 0


def _dispatch_verify_provenance(args: argparse.Namespace) -> int:
    verdict, details = verify_provenance(args.path, current_ir_path=args.ir, current_source_path=args.source)
    print(f"\nHARMOS PROVENANCE: {verdict}")
    for d in details:
        print(f"  {d}")
    return 0 if verdict == "VALID" else 1


def _dispatch_bench(args: argparse.Namespace) -> int:
    from core.compiler.benchmark import get_standard_benchmarks, format_benchmark_report
    suites = get_standard_benchmarks(args.suite)
    print("\n" + format_benchmark_report(suites))
    return 1 if any(v.verdict != "SHIP" for v in suites) else 0


def _dispatch_harvest(args: argparse.Namespace) -> int:
    cases = []
    if args.suite == "truax":
        from core.compiler.microtonal_engine import MicrotonalEngine
        eng = MicrotonalEngine()
        truax_inputs = [
            [1.0, 1.0], [1.0, 2.0], [3.0, 2.0], [5.0, 3.0], [7.0, 4.0], [9.0, 5.0]
        ]
        cases.extend(harvest_from_callable(eng.to_normal_form, "to_normal_form", truax_inputs, tolerance=args.tolerance))
        carrier_inputs = [
            [220.0, 1.0, 1.0], [220.0, 3.0, 2.0], [440.0, 5.0, 3.0]
        ]
        cases.extend(harvest_from_callable(eng.calc_carrier_freq, "calc_carrier_freq", carrier_inputs, tolerance=args.tolerance))
    elif args.suite == "wilson":
        w_inputs = [[0.5], [1.0], [1.5], [2.0], [3.0], [5.0], [7.0]]
        cases.extend(harvest_from_callable(wilson_reduce_to_octave, "reduce_to_octave", w_inputs, tolerance=args.tolerance))
    elif args.suite == "hexslider":
        freq_inputs = [[0, 0], [1, 0], [0, 1], [5, 2], [10, 4]]
        cases.extend(harvest_from_callable(ref_hex_freq, "compute_cell_frequency", freq_inputs, tolerance=args.tolerance))
        hit_inputs = [[12.0, 10.392], [0.0, 0.0], [30.0, 20.784], [500.0, 500.0]]
        cases.extend(harvest_from_callable(ref_hex_hit, "hit_test", hit_inputs, tolerance=args.tolerance))

    count = write_cases_jsonl(cases, args.out)
    print(f"Cosecha exitosa: {count} casos guardados en '{args.out}'.")
    return 0


def _dispatch_diff(args: argparse.Namespace) -> int:
    cases = read_cases_jsonl(args.cases)
    if getattr(args, "cpp_kernel", None):
        from core.compiler.cpp_headless_runner import run_headless_cases
        report = run_headless_cases(
            args.cpp_kernel,
            cases,
            kernel_class=args.kernel_class,
            kernel_type_name=args.kernel_type_name
        )
    else:
        registry = {}
        if args.suite == "truax":
            from core.compiler.microtonal_engine import MicrotonalEngine
            eng = MicrotonalEngine()
            registry["to_normal_form"] = eng.to_normal_form
            registry["calc_carrier_freq"] = eng.calc_carrier_freq
        elif args.suite == "wilson":
            registry["reduce_to_octave"] = wilson_reduce_to_octave
        elif args.suite == "hexslider":
            registry["compute_cell_frequency"] = ref_hex_freq
            registry["hit_test"] = ref_hex_hit

        report = evaluate_diff(cases, registry)

    print("\n" + "=" * 50)
    print(f" HARMOS ORACLE DIFF: {report.verdict} (SEMANTIC)")
    print("=" * 50)
    for d in report.details:
        print(f"  {d}")
    if report.failures:
        print("\n  Fallas detectadas:")
        for f in report.failures[:10]:
            print(f"    - {f.case.fn}{tuple(f.case.args)}: {f.reason}")
    print("-" * 50)
    return 0 if report.verdict == "PASS" else 1


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser de línea de comandos con todos los subcomandos de Harmos."""
    parser = argparse.ArgumentParser(description="Harmos CLI: Compilador y extractor de especificaciones IR hacia Max MSP.")
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # compile
    compile_parser = subparsers.add_parser("compile", help="Compilar un archivo IR (.ir.json) a C++ y .maxpat")
    compile_parser.add_argument("ir_file", help="Ruta al archivo de especificación IR (.ir.json)")
    compile_parser.add_argument("--out", default="./build_harmos", help="Directorio destino de generación")
    compile_parser.add_argument("--source", default=None, help="Ruta al código fuente original (opcional para procedencia)")
    compile_parser.add_argument("--no-build", action="store_true", default=False, help="Emitir solo archivos fuente sin compilar el binario nativo")

    # extract
    extract_parser = subparsers.add_parser("extract", help="Extraer una especificación IR desde código fuente (TypeScript/JS)")
    extract_parser.add_argument("source_file", help="Ruta al archivo fuente (.ts / .js)")
    extract_parser.add_argument("--out", required=True, help="Ruta del archivo IR destino (.ir.json)")
    extract_parser.add_argument("--name", default=None, help="Nombre del objeto en Max (ej. harmos.gain_meter)")

    # verify-provenance
    verify_prov_parser = subparsers.add_parser("verify-provenance", help="Verificar la validez de la huella emitted-from.json")
    verify_prov_parser.add_argument("path", help="Ruta al archivo emitted-from.json o al directorio generado")
    verify_prov_parser.add_argument("--ir", default=None, help="Ruta al archivo IR actual (opcional)")
    verify_prov_parser.add_argument("--source", default=None, help="Ruta al código fuente actual (opcional)")

    # bench
    bench_parser = subparsers.add_parser("bench", help="Evaluar presupuestos de rendimiento en tiempo real (SHIP / NO_SHIP)")
    bench_parser.add_argument("--suite", choices=["truax", "tables", "all"], default="all", help="Suite a evaluar")

    # harvest
    harvest_parser = subparsers.add_parser("harvest", help="Cosechar vectores de prueba semanticos hacia cases.jsonl")
    harvest_parser.add_argument("--suite", choices=["truax", "wilson", "hexslider"], default="truax", help="Suite estandar a cosechar")
    harvest_parser.add_argument("--out", required=True, help="Ruta del archivo destino (cases.jsonl)")
    harvest_parser.add_argument("--tolerance", type=float, default=1e-7, help="Tolerancia numerica float")

    # diff
    diff_parser = subparsers.add_parser("diff", help="Evaluar equivalencia semantica de cases.jsonl contra un target")
    diff_parser.add_argument("cases", help="Ruta al archivo cases.jsonl")
    diff_parser.add_argument("--suite", choices=["truax", "wilson", "hexslider"], default="truax", help="Registro objetivo a evaluar")
    diff_parser.add_argument("--cpp-kernel", help="Ruta al header de kernel C++ puro (*_kernel.hpp) para evaluacion headless en CI")
    diff_parser.add_argument("--kernel-class", choices=["wilson", "control", "dsp", "hexslider", "truax"], default="wilson", help="Tipo de arnes C++ a generar")
    diff_parser.add_argument("--kernel-type-name", help="Nombre exacto del tipo C++ (para control/dsp)")

    # doc
    doc_parser = subparsers.add_parser("doc", help="Generar documentacion canonica .maxref.xml a partir de una IR (.ir.json)")
    doc_parser.add_argument("ir_file", help="Ruta al archivo de especificacion IR (.ir.json)")
    doc_parser.add_argument("--out", default=None, help="Ruta de destino del archivo .maxref.xml o directorio docs/")
    doc_parser.add_argument("--author", default="Harmos Meta-Compiler", help="Nombre del autor para metadatos XML")

    return parser


def main():
    parser = build_parser()

    # Compatibilidad con sintaxis directa previa: 'harmos <ir_file> --out <dir>'
    if len(sys.argv) > 1 and sys.argv[1] not in ["compile", "extract", "verify-provenance", "bench", "harvest", "diff", "doc", "-h", "--help"]:
        sys.argv.insert(1, "compile")

    args = parser.parse_args()

    dispatch_table = {
        "compile": _dispatch_compile,
        "doc": _dispatch_doc,
        "extract": _dispatch_extract,
        "verify-provenance": _dispatch_verify_provenance,
        "bench": _dispatch_bench,
        "harvest": _dispatch_harvest,
        "diff": _dispatch_diff,
    }

    handler = dispatch_table.get(args.command)
    if not handler:
        parser.print_help()
        sys.exit(0)

    try:
        exit_code = handler(args)
        if exit_code != 0:
            sys.exit(exit_code)
    except Exception as e:
        print(f"Error durante la ejecucion: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
