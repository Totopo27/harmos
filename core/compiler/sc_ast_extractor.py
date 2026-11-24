"""
Harmos SuperCollider AST Extractor: Análisis estático de SynthDefs y grafos de síntesis (UGens).
Convierte especificaciones de sclang a Representación Intermedia conforme a max_object_ir.schema.json.
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from core.compiler.sc_control_extractor import SCControlExtractor


class SCAstExtractor:
    def __init__(self):
        self.control_extractor = SCControlExtractor()

    def _extract_synth_name(self, source_code: str, default_name: str) -> str:
        """Extrae el nombre del SynthDef (\\name o 'name')."""
        name_match = re.search(r"SynthDef\s*\(\s*[\\'\"]?(\w+)[\\'\"]?", source_code)
        return name_match.group(1) if name_match else default_name

    def _parse_synth_args(self, source_code: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Extrae argumentos del SynthDef y los mapea a inlets y atributos."""
        inlets: List[Dict[str, Any]] = []
        attributes: List[Dict[str, Any]] = []

        arg_block_match = re.search(r"arg\s+([^;]+);", source_code)
        if not arg_block_match:
            return inlets, attributes

        raw_args = arg_block_match.group(1).split(",")
        idx = 0
        for arg_str in raw_args:
            arg_clean = arg_str.strip()
            if not arg_clean:
                continue
            parts = [p.strip() for p in arg_clean.split("=")]
            arg_name = parts[0]
            default_val = float(parts[1]) if len(parts) > 1 and self._is_number(parts[1]) else 0.0

            # El bus de salida se convierte en outlet, no en inlet de control
            if arg_name in ["out", "outBus"]:
                continue

            arg_type = "signal" if "sig" in arg_name else "float"
            if arg_name in ["gate", "trigger"]:
                arg_type = "float"

            inlets.append({
                "id": idx,
                "type": arg_type,
                "description": f"Param {arg_name} (default: {default_val})"
            })
            attributes.append({
                "name": arg_name,
                "type": "float",
                "default": default_val
            })
            idx += 1

        return inlets, attributes

    def _classify_ugens(self, source_code: str) -> List[Dict[str, Any]]:
        """Detecta UGens y clasifica su tasa de muestreo (.ar, .kr, .ir)."""
        ugens: List[Dict[str, Any]] = []
        ugen_matches = re.finditer(r"(\w+)\.(ar|kr|ir)\s*\((.*?)\)", source_code)
        for m in ugen_matches:
            u_class = m.group(1)
            u_rate_str = m.group(2)
            u_args = m.group(3).strip()

            rate = "audio" if u_rate_str == "ar" else ("control" if u_rate_str == "kr" else "scalar")
            ugens.append({
                "class": u_class,
                "rate": rate,
                "args_raw": u_args
            })
        return ugens

    def _build_outlets(self, ugens: List[Dict[str, Any]], source_code: str) -> Tuple[List[Dict[str, Any]], bool]:
        """Determina los outlets de audio o control según la presencia de Out.ar o UGens de audio."""
        has_audio = any(u["rate"] == "audio" for u in ugens) or "Out.ar" in source_code
        outlets: List[Dict[str, Any]] = []
        if has_audio:
            outlets.append({
                "id": 0,
                "type": "signal",
                "description": "Left / Main Audio Signal"
            })
            outlets.append({
                "id": 1,
                "type": "signal",
                "description": "Right Audio Signal"
            })
        else:
            outlets.append({
                "id": 0,
                "type": "anything",
                "description": "Control output"
            })
        return outlets, has_audio

    def extract(self, source_code: str, default_name: str = "harmos_synth") -> Dict[str, Any]:
        """
        Extrae la Representación Intermedia (IR) desde código SuperCollider que define SynthDefs
        y/o módulos de control y tablas de afinación.
        """
        synth_name = self._extract_synth_name(source_code, default_name)

        # Extraer tablas y conmutadores de control si están presentes
        control_ir = self.control_extractor.extract(source_code, module_name=synth_name)
        data_tables = control_ir.get("data_tables", [])
        control_interfaces = control_ir.get("control_interfaces", [])

        inlets, attributes = self._parse_synth_args(source_code)
        ugens = self._classify_ugens(source_code)
        outlets, has_audio = self._build_outlets(ugens, source_code)

        if not inlets:
            inlets.append({
                "id": 0,
                "type": "anything",
                "description": "Default control inlet"
            })

        category = "dsp" if has_audio else "control"

        result = {
            "object_name": synth_name,
            "name": synth_name,
            "version": "1.0.0",
            "category": category,
            "target_runtime": "cpp_min_devkit",
            "thread_safety": "audio_dsp_perform" if has_audio else "main_thread_only",
            "description": f"Generado por Harmos SCAstExtractor a partir de fuente SuperCollider \\{synth_name}",
            "inlets": inlets,
            "outlets": outlets,
            "attributes": attributes,
            "algorithm": {
                "source_language": "supercollider",
                "synth_name": synth_name,
                "ugens": ugens
            }
        }

        if data_tables:
            result["data_tables"] = data_tables
        if control_interfaces:
            result["control_interfaces"] = control_interfaces

        return result

    def _is_number(self, s: str) -> bool:
        try:
            float(s.strip())
            return True
        except ValueError:
            return False


def extract_ir_from_sc_source(source_code: str, default_name: str = "harmos_synth") -> Dict[str, Any]:
    return SCAstExtractor().extract(source_code, default_name=default_name)
