"""
Harmos CLI Compiler: Sintetizador de paquetes Max MSP a partir de Representaciones Intermedias (IR).
Genera parches .maxpat validados con TypedPatch y esqueletos C++ Min-Devkit con CMakeLists.txt.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from core.compiler.typed_patch import TypedPatch
from core.compiler.ast_extractor import extract_ir_from_file
from core.compiler.cpp_generator import generate_cpp_kernel, generate_min_wrapper
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


def generate_cmakelists(object_name: str, output_path: str) -> None:
    content = f"""c74_min_project({object_name})
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


def generate_test_maxpat(ir: Dict[str, Any], output_path: str) -> None:
    object_name = ir.get("object_name", "my_object")
    patch = TypedPatch()

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


def compile_ir(ir_file_path: str, output_dir: str, source_path: Optional[str] = None) -> Dict[str, Any]:
    with open(ir_file_path, "r", encoding="utf-8") as f:
        ir_data = json.load(f)

    os.makedirs(output_dir, exist_ok=True)
    object_name = ir_data.get("object_name", "harmos_object")

    maxpat_path = os.path.join(output_dir, f"{object_name}_test.maxpat")
    cpp_path = os.path.join(output_dir, f"{object_name}.cpp")
    kernel_path = os.path.join(output_dir, f"{object_name}_kernel.hpp")
    cmake_path = os.path.join(output_dir, "CMakeLists.txt")

    generate_test_maxpat(ir_data, maxpat_path)
    generate_cpp_min_devkit(ir_data, cpp_path, kernel_path=kernel_path)
    generate_cmakelists(object_name, cmake_path)

    # Generar huella de procedencia criptográfica (emitted-from.json)
    prov_record = build_provenance_record(
        ir_file_path,
        source_path=source_path,
        artifacts={
            "maxpat": maxpat_path,
            "cpp": cpp_path,
            "kernel": kernel_path,
            "cmake": cmake_path,
        }
    )
    prov_path = write_provenance_file(output_dir, prov_record)

    return {
        "success": True,
        "object_name": object_name,
        "maxpat_path": maxpat_path,
        "cpp_path": cpp_path,
        "kernel_path": kernel_path,
        "cmake_path": cmake_path,
        "provenance_path": str(prov_path)
    }


def main():
    parser = argparse.ArgumentParser(description="Harmos CLI: Compilador y extractor de especificaciones IR hacia Max MSP.")
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # Subcomando compile (por defecto o explícito)
    compile_parser = subparsers.add_parser("compile", help="Compilar un archivo IR (.ir.json) a C++ y .maxpat")
    compile_parser.add_argument("ir_file", help="Ruta al archivo de especificación IR (.ir.json)")
    compile_parser.add_argument("--out", default="./build_harmos", help="Directorio destino de generación")
    compile_parser.add_argument("--source", default=None, help="Ruta al código fuente original (opcional para procedencia)")

    # Subcomando extract
    extract_parser = subparsers.add_parser("extract", help="Extraer una especificación IR desde código fuente (TypeScript/JS)")
    extract_parser.add_argument("source_file", help="Ruta al archivo fuente (.ts / .js)")
    extract_parser.add_argument("--out", required=True, help="Ruta del archivo IR destino (.ir.json)")
    extract_parser.add_argument("--name", default=None, help="Nombre del objeto en Max (ej. harmos.gain_meter)")

    # Subcomando verify-provenance
    verify_prov_parser = subparsers.add_parser("verify-provenance", help="Verificar la validez de la huella emitted-from.json")
    verify_prov_parser.add_argument("path", help="Ruta al archivo emitted-from.json o al directorio generado")
    verify_prov_parser.add_argument("--ir", default=None, help="Ruta al archivo IR actual (opcional)")
    verify_prov_parser.add_argument("--source", default=None, help="Ruta al código fuente actual (opcional)")

    # Subcomando bench
    bench_parser = subparsers.add_parser("bench", help="Evaluar presupuestos de rendimiento en tiempo real (SHIP / NO_SHIP)")
    bench_parser.add_argument("--suite", choices=["truax", "tables", "all"], default="all", help="Suite a evaluar")

    # Compatibilidad con sintaxis directa previa: 'harmos <ir_file> --out <dir>'
    if len(sys.argv) > 1 and sys.argv[1] not in ["compile", "extract", "verify-provenance", "bench", "-h", "--help"]:
        sys.argv.insert(1, "compile")

    args = parser.parse_args()

    try:
        if args.command == "compile":
            res = compile_ir(args.ir_file, args.out, source_path=args.source)
            print(f"Compilacion exitosa para: {res['object_name']}")
            print(f"  Patcher de prueba: {res['maxpat_path']}")
            print(f"  Fuente C++:        {res['cpp_path']}")
            print(f"  CMakeLists:        {res['cmake_path']}")
            print(f"  Procedencia:       {res['provenance_path']}")
        elif args.command == "extract":
            res = handle_extract(args.source_file, args.out, object_name=args.name)
            print(f"Extraccion exitosa para: {res['object_name']}")
            print(f"  Archivo IR generado: {res['ir_path']}")
        elif args.command == "verify-provenance":
            verdict, details = verify_provenance(args.path, current_ir_path=args.ir, current_source_path=args.source)
            print(f"\nHARMOS PROVENANCE: {verdict}")
            for d in details:
                print(f"  {d}")
            if verdict != "VALID":
                sys.exit(1)
        elif args.command == "bench":
            from scripts.bench import benchmark_truax_normal_form, benchmark_scale_generation_384
            suites = []
            if args.suite in ["truax", "all"]:
                suites.append(benchmark_truax_normal_form())
            if args.suite in ["tables", "all"]:
                suites.append(benchmark_scale_generation_384())

            all_ship = True
            print("\n" + "=" * 60)
            print(" HARMOS BENCHMARK & TIMING EVALUATION")
            print("=" * 60)
            print(
                "[i] AVISO: Evaluacion en Python host. No certifica DSP en Max MSP (ver docs/ORACULO_LIMITES.md).\n"
            )
            for v in suites:
                speedup_info = f", speedup: {v.speedup:.2f}x" if v.speedup is not None else ""
                print(f"[*] {v.name}: [{v.verdict}] (mediana: {v.median_latency_us:.2f} us{speedup_info})")
                for r in v.reasons:
                    print(f"    - {r}")
                if v.verdict != "SHIP":
                    all_ship = False
            print("-" * 60)
            print(f"EVALUACION FINAL DE RENDIMIENTO: {'SHIP' if all_ship else 'NO_SHIP'}")
            if not all_ship:
                sys.exit(1)
        else:
            parser.print_help()
    except Exception as e:
        print(f"Error durante la ejecucion: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
