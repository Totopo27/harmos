"""
Harmos TypedPatch: Compilador de parches de Max MSP (.maxpat) con validación estricta de contratos.
Genera el árbol JSON nativo de Cycling '74 sin cables hardcodeados a ciegas.
"""
import json
from typing import Dict, Any, List, Optional
from core.compiler.contract_engine import ContractEngine, IncompatibleConnectionError


class MaxBox:
    def __init__(self, box_id: str, text: str, x: float, y: float, w: float = 120.0, h: float = 22.0):
        self.box_id = box_id
        self.text = text
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.maxclass = self._determine_maxclass(text)

    def _determine_maxclass(self, text: str) -> str:
        first = text.strip().split()[0] if text.strip() else ""
        if first == "comment":
            return "comment"
        elif first in ["message", "msg"]:
            return "message"
        elif first in ["flonum", "number"]:
            return first
        return "newobj"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "box": {
                "id": self.box_id,
                "maxclass": self.maxclass,
                "numinlets": 1,
                "numoutlets": 1,
                "outlettype": [""],
                "patching_rect": [self.x, self.y, self.w, self.h],
                "text": self.text
            }
        }


class TypedPatch:
    def __init__(self, contract_engine: Optional[ContractEngine] = None):
        self.engine = contract_engine or ContractEngine()
        self.boxes: List[MaxBox] = []
        self.lines: List[Dict[str, Any]] = []
        self._next_id = 1
        self._cursor_x = 50.0
        self._cursor_y = 50.0

    def add_box(self, text: str, x: Optional[float] = None, y: Optional[float] = None, w: float = 120.0, h: float = 22.0) -> MaxBox:
        bx = self._cursor_x if x is None else x
        by = self._cursor_y if y is None else y

        box_id = f"obj-{self._next_id}"
        self._next_id += 1

        box = MaxBox(box_id, text, bx, by, w, h)
        self.boxes.append(box)

        # Mover cursor verticalmente por omisión para evitar colisión
        if y is None:
            self._cursor_y += 45.0

        return box

    def connect(self, src: MaxBox, src_outlet: int, dest: MaxBox, dest_inlet: int) -> None:
        # Validación de contrato en tiempo de diseño
        self.engine.validate_connection(src.text, src_outlet, dest.text, dest_inlet)

        line = {
            "patchline": {
                "destination": [dest.box_id, dest_inlet],
                "source": [src.box_id, src_outlet]
            }
        }
        self.lines.append(line)

    def connect_auto_adapt(self, src: MaxBox, src_outlet: int, dest: MaxBox, dest_inlet: int) -> Optional[MaxBox]:
        """
        Inserta de forma transparente una caja adaptadora si hay discrepancia de tipos
        compatible (ej. salida 'list' conectada a entrada escalar 'float' o 'int').
        """
        src_base = src.text.strip().split()[0]
        dest_base = dest.text.strip().split()[0]

        src_outlets = self.engine.get_outlets(src_base)
        dest_inlets = self.engine.get_inlets(dest_base)

        src_type = src_outlets[src_outlet].get("type", "anything") if src_outlet < len(src_outlets) else "anything"
        dest_type = dest_inlets[dest_inlet].get("type", "anything") if dest_inlet < len(dest_inlets) else "anything"

        # Caso: Emisor lista hacia receptor escalar
        if src_type == "list" and dest_type in ["float", "int", "number"]:
            # Posición intermedia entre src y dest
            adapter_x = (src.x + dest.x) / 2.0
            adapter_y = (src.y + dest.y) / 2.0 if dest.y > src.y else src.y + 35.0

            # Tipo de unpack según destino
            unpack_type = "f" if dest_type == "float" else "i"
            adapter_box = self.add_box(f"unpack {unpack_type} {unpack_type}", x=adapter_x, y=adapter_y)

            # Trazar cables: src -> unpack (inlet 0) y unpack (outlet 0) -> dest (inlet solicitado)
            self.connect(src, src_outlet, adapter_box, 0)
            self.connect(adapter_box, 0, dest, dest_inlet)
            return adapter_box

        # Si son directamente compatibles, conectar directo
        self.connect(src, src_outlet, dest, dest_inlet)
        return None

    def connect_semantic(self, src: MaxBox, src_outlet: int, dest: MaxBox, semantic_role: str) -> None:
        """
        Resuelve dinámicamente el inlet físico mediante el contrato y conecta.
        CERO Hardcoding.
        """
        dest_inlet = self.engine.resolve_inlet_index(dest.text, semantic_role)
        self.connect(src, src_outlet, dest, dest_inlet)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patcher": {
                "fileversion": 1,
                "appversion": {
                    "major": 9,
                    "minor": 0,
                    "revision": 0,
                    "architecture": "x64",
                    "modern": 1
                },
                "classnamespace": "box",
                "rect": [100.0, 100.0, 800.0, 600.0],
                "bglocked": 0,
                "openinpresentation": 0,
                "default_fontsize": 12.0,
                "default_fontname": "Arial",
                "boxes": [b.to_dict() for b in self.boxes],
                "lines": self.lines
            }
        }

    def save(self, filepath: str) -> None:
        data = self.to_dict()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
