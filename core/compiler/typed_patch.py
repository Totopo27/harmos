"""
Harmos TypedPatch: Compilador de parches de Max MSP (.maxpat) con validación estricta de contratos.
Genera el árbol JSON nativo de Cycling '74 sin cables hardcodeados a ciegas.
"""
import json
from typing import Dict, Any, List, Optional, Union
from core.compiler.contract_engine import ContractEngine


class MaxBox:
    def __init__(
        self,
        box_id: str,
        text: str,
        x: float,
        y: float,
        w: float = 120.0,
        h: float = 22.0,
        extra_attributes: Optional[Dict[str, Any]] = None
    ):
        self.box_id = box_id
        self.text = text
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.extra_attributes = dict(extra_attributes) if extra_attributes else {}
        self.maxclass = self.extra_attributes.get("maxclass") or self._determine_maxclass(text)

    def _determine_maxclass(self, text: str) -> str:
        first = text.strip().split()[0] if text.strip() else ""
        if first == "comment":
            return "comment"
        elif first in ["message", "msg"]:
            return "message"
        elif first in ["flonum", "number"]:
            return first
        elif first in ["umenu", "radiogroup", "tab", "gain~", "ezdac~"]:
            return first
        return "newobj"

    def to_dict(self) -> Dict[str, Any]:
        box_data = {
            "id": self.box_id,
            "maxclass": self.maxclass,
            "numinlets": 1,
            "numoutlets": 1,
            "outlettype": [""],
            "patching_rect": [self.x, self.y, self.w, self.h],
            "text": self.text
        }
        if self.extra_attributes:
            box_data.update(self.extra_attributes)
        return {"box": box_data}


class TypedPatch:
    def __init__(self, contract_engine: Optional[ContractEngine] = None):
        self.engine = contract_engine or ContractEngine()
        self.boxes: List[MaxBox] = []
        self.lines: List[Dict[str, Any]] = []
        self.unverifiable_connections = []
        self._next_id = 1
        self._cursor_x = 50.0
        self._cursor_y = 50.0

    @staticmethod
    def format_umenu_items(options: List[str]) -> List[str]:
        """
        Formatea una lista de opciones al formato nativo de items de umenu en Max MSP:
        ['opcion1', ',', 'opcion2', ',', 'opcion3']
        """
        items: List[str] = []
        for i, opt in enumerate(options):
            items.append(str(opt))
            if i < len(options) - 1:
                items.append(",")
        return items

    def add_box(
        self,
        text: str,
        x: Optional[float] = None,
        y: Optional[float] = None,
        w: float = 120.0,
        h: float = 22.0,
        extra_attributes: Optional[Dict[str, Any]] = None
    ) -> MaxBox:
        bx = self._cursor_x if x is None else x
        by = self._cursor_y if y is None else y

        box_id = f"obj-{self._next_id}"
        self._next_id += 1

        box = MaxBox(box_id, text, bx, by, w, h, extra_attributes=extra_attributes)
        self.boxes.append(box)

        # Mover cursor verticalmente por omisión para evitar colisión
        if y is None:
            self._cursor_y += 45.0

        return box

    def add_message(
        self,
        text: str,
        x: Optional[float] = None,
        y: Optional[float] = None,
        w: float = 80.0,
        h: float = 22.0,
    ) -> MaxBox:
        """Create a Max message box whose literal payload is sent as a message."""
        return self.add_box(text, x=x, y=y, w=w, h=h, extra_attributes={"maxclass": "message"})

    @staticmethod
    def _contract_spec(box: MaxBox) -> str:
        """Resolve the contract lookup string for a MaxBox (message boxes map to 'message')."""
        return "message" if box.maxclass == "message" else box.text

    def connect(
        self, src: MaxBox, src_outlet: int, dest: MaxBox, dest_inlet: int,
        *, allow_unverifiable: bool = False,
    ) -> None:
        # Validación de contrato en tiempo de diseño
        assessment = self.engine.validate_connection(
            self._contract_spec(src), src_outlet, self._contract_spec(dest), dest_inlet,
            allow_unverifiable=allow_unverifiable,
        )

        line = {
            "patchline": {
                "destination": [dest.box_id, dest_inlet],
                "source": [src.box_id, src_outlet]
            }
        }
        self.lines.append(line)
        if assessment.status == "UNVERIFIABLE":
            self.unverifiable_connections.append(assessment)

    def connect_auto_adapt(self, src: MaxBox, src_outlet: int, dest: MaxBox, dest_inlet: int) -> Optional[MaxBox]:
        """
        Inserta de forma transparente una caja adaptadora si hay discrepancia de tipos
        compatible (ej. salida 'list' conectada a entrada escalar 'float' o 'int').
        """
        src_spec = self._contract_spec(src)
        dest_spec = self._contract_spec(dest)
        self.engine.validate_connection(src_spec, src_outlet, dest_spec, dest_inlet)

        src_outlets = self.engine.get_outlets(src_spec)
        dest_inlets = self.engine.get_inlets(dest_spec)

        src_types = self.engine.port_types(src_outlets[src_outlet])
        dest_types = self.engine.port_types(dest_inlets[dest_inlet])

        # Caso: Emisor lista hacia receptor escalar
        if src_types == {"list"} and dest_types <= {"float", "int", "number"}:
            # Posición intermedia entre src y dest
            adapter_x = (src.x + dest.x) / 2.0
            adapter_y = (src.y + dest.y) / 2.0 if dest.y > src.y else src.y + 35.0

            # Tipo de unpack según destino
            unpack_type = "f" if dest_types == {"float"} else "i"
            adapter_text = f"unpack {unpack_type} {unpack_type}"
            self.engine.validate_connection(src_spec, src_outlet, adapter_text, 0)
            self.engine.validate_connection(adapter_text, 0, dest_spec, dest_inlet)
            adapter_box = self.add_box(adapter_text, x=adapter_x, y=adapter_y)

            # Trazar cables: src -> unpack (inlet 0) y unpack (outlet 0) -> dest (inlet solicitado)
            self.connect(src, src_outlet, adapter_box, 0)
            self.connect(adapter_box, 0, dest, dest_inlet)
            return adapter_box

        # Si son directamente compatibles, conectar directo
        self.connect(src, src_outlet, dest, dest_inlet)
        return None

    def connect_semantic(
        self,
        src: MaxBox,
        src_outlet: Union[int, str],
        dest: MaxBox,
        semantic_role: Union[int, str]
    ) -> None:
        """
        Resuelve dinámicamente los índices físicos de outlet e inlet mediante el contrato y conecta.
        CERO Hardcoding.
        """
        src_spec = self._contract_spec(src)
        dest_spec = self._contract_spec(dest)
        src_idx = (
            self.engine.resolve_outlet_index(src_spec, src_outlet)
            if isinstance(src_outlet, str)
            else src_outlet
        )
        dest_idx = (
            self.engine.resolve_inlet_index(dest_spec, semantic_role)
            if isinstance(semantic_role, str)
            else semantic_role
        )
        self.connect(src, src_idx, dest, dest_idx)

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
