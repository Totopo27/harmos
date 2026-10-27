"""
Harmos SC Control Extractor: Analizador estático de estructuras de datos y lógica de control SCLang.
Extrae diccionarios de afinación, tablas de ondas y conmutadores de estado hacia la IR formal.
"""
import re
from typing import Dict, Any, List


class SCControlExtractor:
    """
    Extrae tablas de datos (data_tables) e interfaces de conmutación (control_interfaces)
    a partir de scripts de SuperCollider (.sc / .scd) como módulos de tuning, presets o buffers.
    """

    def extract(self, source_code: str, module_name: str = "controlModule") -> Dict[str, Any]:
        data_tables: List[Dict[str, Any]] = []

        # 1. Detección de asociaciones de escalas (self.scales[\key] = self.method;)
        # Ej: self.scales[\tet31] = self.build31TET;
        scale_dict_matches = re.finditer(r"scales\[\\?(\w+)\]\s*=\s*self\.(\w+);", source_code)
        detected_scales = []

        for m in scale_dict_matches:
            scale_key = m.group(1)
            builder_method = m.group(2)
            detected_scales.append(scale_key)

            data_tables.append({
                "name": scale_key,
                "type": "coll",
                "source_method": builder_method,
                "source_file": f"{scale_key}.txt",
                "total_entries": 384,
                "default_entry": "tet31"
            })

        # Si no encontró por diccionario explícito, buscar métodos que comiencen con build<Nombre>
        if not data_tables:
            builder_matches = re.finditer(r"build(\w+):\s*\{\s*\|self", source_code)
            for bm in builder_matches:
                raw_name = bm.group(1).lower()
                detected_scales.append(raw_name)
                data_tables.append({
                    "name": raw_name,
                    "type": "coll",
                    "source_method": f"build{bm.group(1)}",
                    "source_file": f"{raw_name}.txt",
                    "total_entries": 384,
                    "default_entry": "tet31"
                })

        # 2. Generación automática del control_interfaces (umenu para selector de afinaciones)
        control_interfaces: List[Dict[str, Any]] = []
        if data_tables:
            options = [f"{t['name']}.txt" for t in data_tables]
            control_interfaces.append({
                "name": "scale_selector",
                "ui_type": "umenu",
                "target_table": "tuning_coll",
                "options": options,
                "default": "tet31.txt"
            })

        return {
            "object_name": module_name,
            "version": "1.0.0",
            "category": "control",
            "target_runtime": "js_painter_v8",
            "description": f"Grafo de control y tablas extraído desde SCLang ({module_name})",
            "inlets": [
                {
                    "id": 0,
                    "type": "anything",
                    "description": "Control de selección de estado / trigger"
                }
            ],
            "outlets": [
                {
                    "id": 0,
                    "type": "anything",
                    "description": "Salida de mensaje de configuración de tabla"
                }
            ],
            "data_tables": data_tables,
            "control_interfaces": control_interfaces
        }
