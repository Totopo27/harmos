"""
Harmos AST Extractor: Análisis estático de código TypeScript/JavaScript para síntesis de IR.
Genera especificaciones conforme a core/schema/max_object_ir.schema.json.
"""
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from core.compiler.sc_ast_extractor import extract_ir_from_sc_source


def map_ts_type_to_max(ts_type: str, param_name: str = "") -> str:
    """Mapea tipos de TypeScript a tipos canónicos de Max MSP."""
    t = ts_type.strip().lower()
    name = param_name.strip().lower()

    if "signal" in t:
        return "signal"
    if t in ["number", "float", "double"]:
        if any(term in name for term in ["count", "divisions", "index", "sum", "id", "channel", "velocity"]):
            return "int"
        return "float"
    if t in ["int", "integer"]:
        return "int"
    if "[]" in t or "array" in t or "list" in t:
        return "list"
    if t in ["string", "symbol"]:
        return "symbol"
    return "anything"


def parse_parameters(params_str: str) -> List[Dict[str, Any]]:
    """Parsea una cadena de parámetros 'a: number, b: string' a lista tipada."""
    inlets = []
    if not params_str.strip():
        return inlets

    raw_params = [p.strip() for p in params_str.split(",") if p.strip()]
    for idx, p in enumerate(raw_params):
        if ":" in p:
            parts = p.split(":", 1)
            name = parts[0].strip()
            ts_type = parts[1].strip()
        else:
            name = p.strip()
            ts_type = "any"

        max_type = map_ts_type_to_max(ts_type, name)
        inlets.append({
            "id": idx,
            "type": max_type,
            "description": f"Param {name} ({ts_type})"
        })

    return inlets


def _extract_from_class(
    source_code: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """Extrae inlets, outlets, atributos, mensajes y categoría desde una clase TypeScript."""
    inlets: List[Dict[str, Any]] = []
    outlets: List[Dict[str, Any]] = []
    attributes: List[Dict[str, Any]] = []
    messages: List[Dict[str, Any]] = []
    category = "control"

    _CONTROL_FLOW_KEYWORDS = frozenset({
        "if", "else", "while", "for", "switch", "catch", "try", "finally",
        "function", "return", "throw", "new", "delete", "typeof",
        "instanceof", "class", "import", "export", "default", "break", "continue",
    })

    all_methods = re.findall(r"(\w+)\s*\((.*?)\)(?:\s*:\s*([\w\[\]]+))?\s*\{", source_code)
    callable_methods = [m for m in all_methods if m[0] not in _CONTROL_FLOW_KEYWORDS]
    primary_method = None

    for m_name, m_params, m_return in callable_methods:
        if m_name in ["process", "compute", "calculate", "run", "step"]:
            primary_method = (m_name, m_params, m_return)
            break

    if not primary_method and callable_methods:
        non_ctor = [m for m in callable_methods if m[0] != "constructor"]
        primary_method = non_ctor[0] if non_ctor else callable_methods[0]

    if primary_method:
        m_name, m_params, m_return = primary_method
        inlets = parse_parameters(m_params)
        ret_type = map_ts_type_to_max(m_return or "any")
        if ret_type != "anything" or m_return:
            outlets.append({
                "id": 0,
                "type": ret_type,
                "description": f"Output of {m_name} ({m_return})"
            })

        if any(inl["type"] == "signal" for inl in inlets) or ret_type == "signal":
            category = "dsp"

    # Métodos mutadores o secundarios se registran como messages
    for m_name, m_params, _ in callable_methods:
        if primary_method and m_name == primary_method[0]:
            continue
        if m_name != "constructor":
            messages.append({
                "name": m_name,
                "description": f"Invoke {m_name}({m_params})"
            })

    # Extraer atributos/propiedades de la clase (ej: gain: number = 1.0;)
    # Restrict to class header before the first method (including constructor) to skip local vars.
    first_method_pos = None
    for m in re.finditer(r"(\w+)\s*\(.*?\)(?:\s*:\s*[\w\[\]]+)?\s*\{", source_code):
        name = m.group(1)
        if name and name not in _CONTROL_FLOW_KEYWORDS:
            first_method_pos = m.start()
            break
    class_header = source_code[:first_method_pos] if first_method_pos is not None else source_code
    props = re.findall(r"(\w+)\s*:\s*(\w+)(?:\s*=\s*([^;]+))?;", class_header)
    for p_name, p_type, p_def in props:
        max_attr_type = "float" if p_type == "number" else "symbol"
        default_val = 0.0
        if p_def:
            try:
                default_val = float(p_def.strip())
            except ValueError:
                default_val = p_def.strip()

        attributes.append({
            "name": p_name,
            "type": max_attr_type,
            "default": default_val,
            "description": f"Property {p_name}"
        })

    return inlets, outlets, attributes, messages, category


def _extract_from_func(
    func_match: re.Match
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """Extrae inlets, outlets y categoría desde una función exportada de nivel superior."""
    func_name = func_match.group(1)
    params_str = func_match.group(2)
    return_str = func_match.group(3) or "void"

    inlets = parse_parameters(params_str)
    outlets = []
    ret_type = map_ts_type_to_max(return_str)
    if ret_type != "void":
        outlets.append({
            "id": 0,
            "type": ret_type,
            "description": f"Return of {func_name} ({return_str})"
        })

    category = "dsp" if any(i["type"] == "signal" for i in inlets) or ret_type == "signal" else "control"
    return inlets, outlets, category


def extract_ir_from_ts_source(source_code: str, object_name: str = "harmos_object") -> Dict[str, Any]:
    """Extrae la Representación Intermedia (IR) desde código fuente TypeScript."""
    class_match = re.search(r"export\s+class\s+(\w+)", source_code)
    func_match = re.search(r"export\s+function\s+(\w+)\s*\((.*?)\)(?:\s*:\s*([\w\[\]]+))?", source_code)

    inlets: List[Dict[str, Any]] = []
    outlets: List[Dict[str, Any]] = []
    attributes: List[Dict[str, Any]] = []
    messages: List[Dict[str, Any]] = []
    category = "control"

    if class_match:
        inlets, outlets, attributes, messages, category = _extract_from_class(source_code)
    elif func_match:
        inlets, outlets, category = _extract_from_func(func_match)

    if not inlets:
        inlets = [{"id": 0, "type": "anything", "description": "Default input"}]
    if not outlets:
        outlets = [{"id": 0, "type": "anything", "description": "Default output"}]

    return {
        "object_name": object_name,
        "category": category,
        "target_runtime": "cpp_min_devkit",
        "thread_safety": "main_thread_only" if category != "dsp" else "audio_dsp_perform",
        "inlets": inlets,
        "outlets": outlets,
        "attributes": attributes,
        "messages": messages
    }


def extract_ir_from_file(source_path: str, object_name: Optional[str] = None) -> Dict[str, Any]:
    path = Path(source_path)
    if not path.exists():
        raise FileNotFoundError(f"Archivo de origen no encontrado: {source_path}")

    obj_name = object_name or f"harmos.{path.stem}"
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    # Despacho políglota según extensión
    ext = path.suffix.lower()
    if ext in [".sc", ".scd"]:
        return extract_ir_from_sc_source(code, default_name=obj_name)

    return extract_ir_from_ts_source(code, object_name=obj_name)
