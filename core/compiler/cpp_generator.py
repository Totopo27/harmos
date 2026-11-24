"""
Harmos Decoupled C++ Generator: Generador desacoplado de Kernel C++ Puro y Wrapper Min-Devkit.
Prerrequisito arquitectónico para el oráculo semántico headless:
- Kernel C++ Puro ({object}_kernel.hpp): 0 dependencias de Max SDK, compilable en cualquier entorno CI.
- Wrapper Min-Devkit ({object}.cpp): Capa delgada que mapea inlets, outlets y atributos al kernel.
"""
from typing import Dict, Any, List
import json
import re


def _is_signal_port(port: Dict[str, Any]) -> bool:
    """Return True when a port accepts or emits a Max MSP audio signal."""
    parts = {part.strip().lower() for part in str(port.get("type", "")).split("/")}
    return "signal" in parts


def _cpp_string_literal(value: Any) -> str:
    """Format any Python value as a properly quoted and escaped C++ string literal."""
    return json.dumps("" if value is None else str(value))


def _cpp_bool_literal(value: Any) -> str:
    """Format an IR boolean default as lowercase C++ 'true' or 'false'."""
    if isinstance(value, str):
        return "true" if value.strip().lower() in ("true", "1", "yes", "on") else "false"
    return "true" if bool(value) else "false"


# Keywords de C++ que no pueden usarse como nombre de miembro.
_CPP_KEYWORDS = frozenset({
    "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor", "bool",
    "break", "case", "catch", "char", "char8_t", "char16_t", "char32_t", "class",
    "compl", "concept", "const", "consteval", "constexpr", "constinit", "const_cast",
    "continue", "co_await", "co_return", "co_yield", "decltype", "default", "delete",
    "do", "double", "dynamic_cast", "else", "enum", "explicit", "export", "extern",
    "false", "float", "for", "friend", "goto", "if", "inline", "int", "long",
    "mutable", "namespace", "new", "noexcept", "not", "not_eq", "nullptr", "operator",
    "or", "or_eq", "private", "protected", "public", "register", "reinterpret_cast",
    "requires", "return", "short", "signed", "sizeof", "static", "static_assert",
    "static_cast", "struct", "switch", "template", "this", "thread_local", "throw",
    "true", "try", "typedef", "typeid", "typename", "union", "unsigned", "using",
    "virtual", "void", "volatile", "wchar_t", "while", "xor", "xor_eq",
})

_IDENTIFIER_UNSAFE = re.compile(r"[^0-9A-Za-z_]")


def cpp_identifier(name: str) -> str:
    """
    Normaliza un nombre del IR a un identificador C++ valido y determinista.

    El nombre original se conserva alli donde Max lo muestra (atributos del
    Inspector): esto solo decide como se llama la variable en C++.
    """
    raw = "" if name is None else str(name).strip()
    identifier = _IDENTIFIER_UNSAFE.sub("_", raw)
    if not identifier:
        raise ValueError(
            f"El nombre '{raw}' no produce ningun identificador C++ valido."
        )
    if identifier[0].isdigit():
        identifier = "_" + identifier
    if identifier in _CPP_KEYWORDS:
        identifier += "_"
    return identifier


def _attribute_identifiers(attributes: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Mapea cada nombre original de atributo a su identificador C++ unico.

    Dos atributos distintos que normalicen al mismo identificador son un error
    explicito: nunca se elige uno en silencio.
    """
    mapping: Dict[str, str] = {}
    owners: Dict[str, str] = {}
    for attr in attributes:
        original = str(attr.get("name", "param"))
        identifier = cpp_identifier(original)
        previous = owners.get(identifier)
        if previous is not None:
            raise ValueError(
                f"Colision de identificadores C++: '{previous}' y '{original}' "
                f"normalizan ambos a '{identifier}'."
            )
        owners[identifier] = original
        mapping[original] = identifier
    return mapping


def generate_cpp_kernel(ir: Dict[str, Any]) -> str:
    """
    Genera el header C++ estándar puro con el algoritmo y estado del objeto.
    No incluye librerías de Cycling '74 ni cabeceras propietarias.
    """
    object_name = ir.get("object_name", "my_object")
    safe_class_name = cpp_identifier(object_name)
    category = ir.get("category", "control")
    attributes = ir.get("attributes", [])
    attribute_ids = _attribute_identifiers(attributes)

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
    lines.append("#include <string>")
    lines.append("")
    lines.append("namespace harmos::kernels {")
    lines.append("")
    lines.append(f"class {safe_class_name}Kernel {{")
    lines.append("public:")

    # Miembros de atributos con tipos C++ estándar
    lines.append("    // Atributos y parametros de estado")
    for attr in attributes:
        attr_name = attribute_ids[str(attr.get("name", "param"))]
        attr_type = attr.get("type", "double")
        raw_def = attr.get("default")
        if attr_type == "float":
            cpp_type = "double"
            default_val = str(0.0 if raw_def is None else raw_def)
        elif attr_type in ["int", "integer"]:
            cpp_type = "int"
            default_val = str(0 if raw_def is None else raw_def)
        elif attr_type in ["symbol", "string"]:
            cpp_type = "std::string"
            default_val = _cpp_string_literal(raw_def)
        elif attr_type == "bool":
            cpp_type = "bool"
            default_val = _cpp_bool_literal(raw_def)
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
    safe_class_name = cpp_identifier(object_name)
    category = ir.get("category", "control")
    inlets = ir.get("inlets", [])
    outlets = ir.get("outlets", [])
    attributes = ir.get("attributes", [])
    attribute_ids = _attribute_identifiers(attributes)

    is_dsp = (category == "dsp")

    lines = []
    lines.append('#include "c74_min.h"')
    lines.append(f'#include "{kernel_header_name}"')
    lines.append("")
    lines.append("using namespace c74::min;")
    lines.append("")
    n_sig_in = max(1, sum(1 for i in inlets if _is_signal_port(i)))
    n_sig_out = max(1, sum(1 for o in outlets if _is_signal_port(o)))

    lines.append(f"class {safe_class_name} : public object<{safe_class_name}>" + (f", public sample_operator<{n_sig_in}, {n_sig_out}>" if is_dsp else "") + " {")
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
        original_name = str(attr.get("name", "param"))
        attr_name = attribute_ids[original_name]
        attr_type = attr.get("type", "float")
        attr_desc = attr.get("description", "Param")
        raw_def = attr.get("default")
        if attr_type in ["symbol", "string"]:
            min_type = "symbol"
            min_def = _cpp_string_literal(raw_def)
            setter_rhs = "std::string(args[0])"
        elif attr_type == "bool":
            min_type = "bool"
            min_def = _cpp_bool_literal(raw_def)
            setter_rhs = "static_cast<bool>(args[0])"
        elif attr_type in ["int", "integer"]:
            min_type = "int"
            min_def = str(0 if raw_def is None else raw_def)
            setter_rhs = "static_cast<int>(args[0])"
        else:
            min_type = "double" if attr_type == "double" else "float"
            min_def = str(0.0 if raw_def is None else raw_def)
            setter_rhs = "static_cast<double>(args[0])"

        lines.append(f'    attribute<{min_type}> {attr_name} {{ this, "{original_name}", {min_def},')
        lines.append(f'        description {{"{attr_desc}"}},')
        lines.append('        setter { MIN_FUNCTION {')
        lines.append(f'            m_kernel.{attr_name} = {setter_rhs};')
        lines.append('            return args;')
        lines.append('        } }')
        lines.append("    };")

    lines.append("")
    lines.append(f"    {safe_class_name}(const atoms& args = {{}}) {{}}")
    lines.append("")

    if is_dsp:
        lines.append("    // Delegación en sample_operator")
        in_names = ["in"] if n_sig_in == 1 else [f"in_{i}" for i in range(n_sig_in)]
        params = ", ".join(f"sample {name}" for name in in_names)
        if n_sig_out == 1:
            lines.append(f"    sample operator()({params}) {{")
            for extra in in_names[1:]:
                lines.append(f"        (void){extra};")
            lines.append(f"        return m_kernel.process_sample({in_names[0]});")
            lines.append("    }")
        else:
            lines.append(f"    samples<{n_sig_out}> operator()({params}) {{")
            for extra in in_names[n_sig_out:]:
                lines.append(f"        (void){extra};")
            calls = ", ".join(
                f"m_kernel.process_sample({in_names[min(ch, n_sig_in - 1)]})"
                for ch in range(n_sig_out)
            )
            lines.append(f"        return {{ {{ {calls} }} }};")
            lines.append("    }")
    else:
        lines.append('    message<> number { this, "number", "Procesa entrada numerica via kernel puro",')
        lines.append("        MIN_FUNCTION {")
        lines.append("            double val = static_cast<double>(args[0]);")
        lines.append("            double res = m_kernel.process_scalar(val);")
        if outlets:
            first_out_id = outlets[0].get("id", 0)
            lines.append(f"            out_{first_out_id}.send(res);")
        lines.append("            return {};")
        lines.append("        }")
        lines.append("    };")

    lines.append("};")
    lines.append("")
    lines.append(f"MIN_EXTERNAL({safe_class_name});")
    lines.append("")

    return "\n".join(lines)
