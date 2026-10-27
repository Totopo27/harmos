"""
Harmos SuperCollider AST Extractor: Análisis estático de SynthDefs y grafos de síntesis (UGens).
Convierte especificaciones de sclang a Representación Intermedia conforme a max_object_ir.schema.json.
"""
import re
from typing import Dict, Any, List, Optional


class SCAstExtractor:
    def __init__(self):
        pass

    def extract(self, source_code: str, default_name: str = "harmos_synth") -> Dict[str, Any]:
        """
        Extrae la Representación Intermedia (IR) desde código SuperCollider que define SynthDefs.
        """
        # 1. Extraer nombre del SynthDef (\name o "name")
        name_match = re.search(r"SynthDef\s*\(\s*[\\'\"]?(\w+)[\\'\"]?", source_code)
        synth_name = name_match.group(1) if name_match else default_name

        # 2. Extraer argumentos (arg out = 0, freq = 440, ...;)
        inlets: List[Dict[str, Any]] = []
        attributes: List[Dict[str, Any]] = []

        arg_block_match = re.search(r"arg\s+([^;]+);", source_code)
        if arg_block_match:
            raw_args = arg_block_match.group(1).split(",")
            idx = 0
            for arg_str in raw_args:
                arg_clean = arg_str.strip()
                if not arg_clean:
                    continue
                parts = [p.strip() for p in arg_clean.split("=")]
                arg_name = parts[0]
                default_val = float(parts[1]) if len(parts) > 1 and self._is_number(parts[1]) else 0.0

                # Clasificación de tipo según rol semántico
                if arg_name in ["out", "outBus"]:
                    continue  # El bus de salida se convierte en outlet, no en inlet de control
                
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

        # 3. Detectar UGens y distinguir .ar (audio) vs .kr (control)
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

        # 4. Outlets: si hay Out.ar o SynthDef de audio, exponer señal estéreo/mono
        outlets: List[Dict[str, Any]] = []
        has_audio = any(u["rate"] == "audio" for u in ugens)
        if has_audio or "Out.ar" in source_code:
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

        return {
            "name": synth_name,
            "version": "1.0.0",
            "category": "dsp" if has_audio else "control",
            "description": f"Generado por Harmos SCAstExtractor a partir de SynthDef \\{synth_name}",
            "inlets": inlets,
            "outlets": outlets,
            "attributes": attributes,
            "algorithm": {
                "source_language": "supercollider",
                "synth_name": synth_name,
                "ugens": ugens
            }
        }

    def _is_number(self, s: str) -> bool:
        try:
            float(s.strip())
            return True
        except ValueError:
            return False


def extract_ir_from_sc_source(source_code: str, default_name: str = "harmos_synth") -> Dict[str, Any]:
    return SCAstExtractor().extract(source_code, default_name=default_name)
