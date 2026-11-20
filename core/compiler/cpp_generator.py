"""
Harmos Decoupled C++ Generator: Generador desacoplado de Kernel C++ Puro y Wrapper Min-Devkit.
Prerrequisito arquitectónico para el oráculo semántico headless:
- Kernel C++ Puro ({object}_kernel.hpp): 0 dependencias de Max SDK, compilable en cualquier entorno CI.
- Wrapper Min-Devkit ({object}.cpp): Capa delgada que mapea inlets, outlets y atributos al kernel.
"""
from typing import Dict, Any, List


def generate_cpp_kernel(ir: Dict[str, Any]) -> str:
    """
    Genera el header C++ estándar puro con el algoritmo y estado del objeto.
    No incluye librerías de Cycling '74 ni cabeceras propietarias.
    """
    object_name = ir.get("object_name", "my_object")
    safe_class_name = object_name.replace(".", "_")
    category = ir.get("category", "control")
    attributes = ir.get("attributes", [])
    inlets = ir.get("inlets", [])
    outlets = ir.get("outlets", [])

    is_dsp = (category == "dsp")

    lines = []
    lines.append("#pragma once")
    lines.append("// =============================================================================")
    lines.append(f"// Harmos Pure C++ Kernel: {safe_class_name}")
    lines.append("// Desacoplado de la API de Max MSP. Apto para ejecucion y testing headless en CI.")
    lines.append("// =============================================================================")
    lines.append("#include <vector>")
    lines.append("#include <cmath>")
    lines.append("#include <algorithm>")
    lines.append("#include <cstddef>")
    lines.append("")
    lines.append("namespace harmos::kernels {")
    lines.append("")
    lines.append(f"class {safe_class_name}Kernel {{")
    lines.append("public:")

    # Miembros de atributos con tipos C++ estándar
    lines.append("    // Atributos y parametros de estado")
    for attr in attributes:
        attr_name = attr.get("name", "param")
        attr_type = attr.get("type", "double")
        if attr_type == "float":
            cpp_type = "double"
            default_val = str(attr.get("default", 0.0))
        elif attr_type in ["int", "integer"]:
            cpp_type = "int"
            default_val = str(attr.get("default", 0))
        else:
            cpp_type = "double"
            default_val = "0.0"

        lines.append(f"    {cpp_type} {attr_name}{{{default_val}}};")

    lines.append("")
    lines.append(f"    {safe_class_name}Kernel() = default;")
    lines.append("")

    # Métodos de procesamiento según categoría
    if is_dsp:
        lines.append("    // Procesamiento DSP muestra a muestra o por bloque (puro)")
        lines.append("    inline float process_sample(float in_sample, double gain_factor = 1.0) noexcept {")
        lines.append("        return in_sample * static_cast<float>(gain_factor);")
        lines.append("    }")
        lines.append("")
        lines.append("    void process_block(const float* in, float* out, size_t n_samples) noexcept {")
        lines.append("        for (size_t i = 0; i < n_samples; ++i) {")
        lines.append("            out[i] = process_sample(in[i]);")
        lines.append("        }")
        lines.append("    }")
    else:
        lines.append("    // Procesamiento de datos de control / matematicas escalares")
        lines.append("    double process_scalar(double input_val) noexcept {")
        lines.append("        return input_val;")
        lines.append("    }")
        lines.append("")
        lines.append("    std::vector<double> process_list(const std::vector<double>& input_list) {")
        lines.append("        std::vector<double> result;")
        lines.append("        result.reserve(input_list.size());")
        lines.append("        for (double v : input_list) {")
        lines.append("            result.push_back(process_scalar(v));")
        lines.append("        }")
        lines.append("        return result;")
        lines.append("    }")

    lines.append("};")
    lines.append("")
    lines.append("} // namespace harmos::kernels")
    lines.append("")

    return "\n".join(lines)


def generate_min_wrapper(ir: Dict[str, Any], kernel_header_name: str) -> str:
    """
    Genera el wrapper delgado de Min-Devkit que aloja el kernel puro.
    Solo se encarga de los puertos (inlets/outlets) y mensajería de Max.
    """
    object_name = ir.get("object_name", "my_object")
    safe_class_name = object_name.replace(".", "_")
    category = ir.get("category", "control")
    inlets = ir.get("inlets", [])
    outlets = ir.get("outlets", [])
    attributes = ir.get("attributes", [])

    is_dsp = (category == "dsp")

    lines = []
    lines.append('#include "c74_min.h"')
    lines.append(f'#include "{kernel_header_name}"')
    lines.append("")
    lines.append("using namespace c74::min;")
    lines.append("")
    lines.append(f"class {safe_class_name} : public object<{safe_class_name}>" + (f", public sample_operator<2, 2>" if is_dsp else "") + " {")
    lines.append("private:")
    lines.append(f"    harmos::kernels::{safe_class_name}Kernel m_kernel;")
    lines.append("")
    lines.append("public:")
    lines.append(f'    MIN_DESCRIPTION {{"{ir.get("description", object_name)} (Harmos Decoupled)"}};')
    lines.append(f'    MIN_TAGS        {{"harmos, generated, {category}"}};')
    lines.append('    MIN_AUTHOR      {"Harmos Compiler Architecture"};')
    lines.append('    MIN_RELATED     {"cycle~, scale, kslider"};')
    lines.append("")

    # Inlets
    for inl in inlets:
        inl_id = inl.get("id", 0)
        inl_type = inl.get("type", "anything")
        desc = inl.get("description", "Inlet")
        lines.append(f'    inlet<> in_{inl_id} {{ this, "({inl_type}) {desc}", "{inl_type}" }};')

    lines.append("")

    # Outlets
    for out in outlets:
        out_id = out.get("id", 0)
        out_type = out.get("type", "anything")
        desc = out.get("description", "Outlet")
        lines.append(f'    outlet<> out_{out_id} {{ this, "({out_type}) {desc}", "{out_type}" }};')

    lines.append("")

    # Atributos vinculados al kernel
    for attr in attributes:
        attr_name = attr.get("name", "param")
        attr_type = attr.get("type", "float")
        attr_def = attr.get("default", 0.0 if attr_type == "float" else 0)
        attr_desc = attr.get("description", "Param")
        lines.append(f'    attribute<{attr_type}> {attr_name} {{ this, "{attr_name}", {attr_def},')
        lines.append(f'        description {{"{attr_desc}"}},')
        lines.append(f'        setter {{ MIN_FUNCTION {{')
        lines.append(f'            m_kernel.{attr_name} = static_cast<double>(args[0]);')
        lines.append(f'            return args;')
        lines.append(f'        }} }}')
        lines.append("    };")

    lines.append("")
    lines.append(f"    {safe_class_name}(const atoms& args = {{}}) {{}}")
    lines.append("")

    if is_dsp:
        lines.append("    // Delegación en sample_operator")
        lines.append("    sample operator()(sample in) {")
        lines.append("        return m_kernel.process_sample(in);")
        lines.append("    }")
    else:
        lines.append('    message<> number { this, "number", "Procesa entrada numerica via kernel puro",')
        lines.append("        MIN_FUNCTION {")
        lines.append("            double val = static_cast<double>(args[0]);")
        lines.append("            double res = m_kernel.process_scalar(val);")
        if outlets:
            lines.append("            out_0.send(res);")
        lines.append("            return {};")
        lines.append("        }")
        lines.append("    };")

    lines.append("};")
    lines.append("")
    lines.append(f"MIN_EXTERNAL({safe_class_name});")
    lines.append("")

    return "\n".join(lines)
