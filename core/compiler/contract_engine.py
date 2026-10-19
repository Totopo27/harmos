"""
Harmos Contract Engine: Introspección y validación estricta de contratos Max MSP.
Consume core/schema/max_contracts.json.
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union


class IncompatibleConnectionError(ValueError):
    """Lanzada cuando se intenta conectar outlets e inlets con tipos o destinos incompatibles."""
    pass


class ContractEngine:
    def __init__(self, contracts_path: Optional[str] = None):
        if contracts_path is None:
            base = Path(__file__).resolve().parent.parent / "schema" / "max_contracts.json"
            self.contracts_path = base
        else:
            self.contracts_path = Path(contracts_path)

        self._contracts: Dict[str, Any] = {}
        self._load_contracts()

    def _load_contracts(self) -> None:
        if self.contracts_path.exists():
            with open(self.contracts_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._contracts = data.get("objects", {})

    def get_object_contract(self, obj_name: str) -> Optional[Dict[str, Any]]:
        base_name = obj_name.strip().split()[0]
        return self._contracts.get(base_name)

    def _normalize_ports(self, ports_data: Union[Dict[str, Any], List[Any]]) -> List[Dict[str, Any]]:
        """Convierte diccionario {"0": {...}, "1": {...}} o lista en una lista indexada en base 0."""
        if isinstance(ports_data, dict):
            # Ordenar por clave numérica
            res = []
            for k in sorted(ports_data.keys(), key=lambda x: int(x) if x.isdigit() else 999):
                res.append(ports_data[k])
            return res
        elif isinstance(ports_data, list):
            return ports_data
        return []

    def get_inlets(self, obj_name: str) -> List[Dict[str, Any]]:
        contract = self.get_object_contract(obj_name)
        if contract and "inlets" in contract:
            return self._normalize_ports(contract["inlets"])
        return []

    def get_outlets(self, obj_name: str) -> List[Dict[str, Any]]:
        contract = self.get_object_contract(obj_name)
        if contract and "outlets" in contract:
            return self._normalize_ports(contract["outlets"])
        return []

    def resolve_inlet_index(self, obj_name: str, semantic_role: str) -> int:
        """
        Resuelve el índice físico de un inlet a partir de su rol semántico
        (ej: "pitch", "pitch_bend", "channel", "cutoff").
        """
        inlets = self.get_inlets(obj_name)
        role_lower = semantic_role.lower()

        # 1. Búsqueda por coincidencia en nombre o descripción
        for idx, inl in enumerate(inlets):
            name = inl.get("name", "").lower()
            desc = inl.get("description", "").lower()
            if role_lower == name or role_lower in name or role_lower in desc:
                return idx

        # 2. Heurística canónica de fallback para objetos estándar de Max
        base_name = obj_name.strip().split()[0]
        if base_name == "midiformat":
            mapping = {
                "pitch": 0,
                "note": 0,
                "velocity": 1,
                "vel": 1,
                "poly_aftertouch": 2,
                "cc": 3,
                "control_change": 3,
                "program_change": 4,
                "pitch_bend": 5,
                "bend": 5,
                "channel": 6,
                "chan": 6,
            }
            if role_lower in mapping:
                return mapping[role_lower]

        return 0

    def is_valid_connection(self, src_obj: str, src_outlet: int, dest_obj: str, dest_inlet: int) -> Tuple[bool, str]:
        src_base = src_obj.strip().split()[0]
        dest_base = dest_obj.strip().split()[0]

        # Regla 1: Prohibición absoluta de conexiones a comment
        if dest_base == "comment":
            return False, "Cajas 'comment' carecen de inlets funcionales; conexión ilegal."

        src_contract = self.get_object_contract(src_base)
        dest_contract = self.get_object_contract(dest_base)

        if not src_contract or not dest_contract:
            return True, "Validación permisiva: objeto sin contrato explícito."

        src_outlets = self.get_outlets(src_base)
        dest_inlets = self.get_inlets(dest_base)

        if src_outlet >= len(src_outlets) or dest_inlet >= len(dest_inlets):
            return True, "Índice fuera de rango formal; permitido por dinamismo de Max."

        src_type = src_outlets[src_outlet].get("type", "anything")
        dest_type = dest_inlets[dest_inlet].get("type", "anything")

        # Regla MSP: señal de audio a señal de audio (auto-summing)
        if src_type == "signal" and dest_type == "signal":
            return True, "Conexión de signal MSP válida con auto-summing."

        # Control a señal o viceversa
        if src_type == "signal" and dest_type not in ["signal", "anything"]:
            return False, f"Desajuste de tipos: señal de audio ({src_type}) hacia inlet de control ({dest_type})."

        return True, "Conexión válida."

    def validate_connection(self, src_obj: str, src_outlet: int, dest_obj: str, dest_inlet: int) -> None:
        valid, reason = self.is_valid_connection(src_obj, src_outlet, dest_obj, dest_inlet)
        if not valid:
            raise IncompatibleConnectionError(
                f"Conexión ilegal entre {src_obj} (outlet {src_outlet}) y {dest_obj} (inlet {dest_inlet}): {reason}"
            )
