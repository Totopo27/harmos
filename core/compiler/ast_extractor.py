"""
Harmos AST Extractor: Análisis estático de código TypeScript/JavaScript para síntesis de IR.
Genera especificaciones conforme a core/schema/max_object_ir.schema.json.
"""
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


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


def extract_ir_from_ts_source(source_code: str, object_name: str = "harmos_object") -> Dict[str, Any]:
    """Extrae la Representación Intermedia (IR) desde código fuente TypeScript."""
    # 1. Buscar clases o funciones exportadas
    class_match = re.search(r"export\s+class\s+(\w+)", source_code)
    func_match = re.search(r"export\s+function\s+(\w+)\s*\((.*?)\)(?:\s*:\s*([\w\[\]]+))?", source_code)

    inlets: List[Dict[str, Any]] = []
    outlets: List[Dict[str, Any]] = []
    attributes: List[Dict[str, Any]] = []
    messages: List[Dict[str, Any]] = []
    category = "control"

    if class_match:
        class_name = class_match.group(1)
        # Buscar método principal: process(), compute() o similar
        method_match = re.search(r"(\w+)\s*\((.*?)\)(?:\s*:\s*([\w\[\]]+))?\s*\{", source_code)
        
        # Buscar todos los métodos para discernir el principal vs mensajes
        all_methods = re.findall(r"(\w+)\s*\((.*?)\)(?:\s*:\s*([\w\[\]]+))?\s*\{", source_code)
        primary_method = None

        for m_name, m_params, m_return in all_methods:
            if m_name in ["process", "compute", "calculate", "run", "step"]:
                primary_method = (m_name, m_params, m_return)
                break
        
        if not primary_method and all_methods:
            # Descartar constructor como método de cómputo primario si hay otros
            non_ctor = [m for m in all_methods if m[0] != "constructor"]
            primary_method = non_ctor[0] if non_ctor else all_methods[0]

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
        for m_name, m_params, _ in all_methods:
            if primary_method and m_name == primary_method[0]:
                continue
            if m_name != "constructor":
                messages.append({
                    "name": m_name,
                    "description": f"Invoke {m_name}({m_params})"
                })

        # Extraer atributos/propiedades de la clase (ej: gain: number = 1.0;)
        props = re.findall(r"(\w+)\s*:\s*(\w+)(?:\s*=\s*([^;]+))?;", source_code)
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

    elif func_match:
        func_name = func_match.group(1)
        params_str = func_match.group(2)
        return_str = func_match.group(3) or "void"

        inlets = parse_parameters(params_str)
        ret_type = map_ts_type_to_max(return_str)
        if ret_type != "void":
            outlets.append({
                "id": 0,
                "type": ret_type,
                "description": f"Return of {func_name} ({return_str})"
            })

    # Si no se detectaron inlets por omisión, garantizar al menos 1
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


from core.compiler.sc_ast_extractor import extract_ir_from_sc_source


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
