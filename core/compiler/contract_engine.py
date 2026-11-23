"""
Harmos Contract Engine: Introspección y validación estricta de contratos Max MSP.
Consume core/schema/max_contracts.json.
"""
import json
from pathlib import Path
from typing import Dict, Any, List, NamedTuple, Optional, Tuple, Union


class IncompatibleConnectionError(ValueError):
    """Lanzada cuando se intenta conectar outlets e inlets con tipos o destinos incompatibles."""
    pass


class ConnectionAssessment(NamedTuple):
    status: str
    reason: str


def validate_contracts(data: Any) -> None:
    """Validate the supported catalog structure, not general JSON Schema."""
    if not isinstance(data, dict) or not isinstance(data.get("objects"), dict):
        raise ValueError("Contract catalog must contain an objects mapping.")
    supported_types = {"signal", "float", "int", "number", "symbol", "list", "bang", "anything"}
    for name, contract in data["objects"].items():
        if not isinstance(name, str) or not name.strip() or not isinstance(contract, dict):
            raise ValueError("Each object must have a non-empty name and a contract mapping.")
        for direction in ("inlets", "outlets"):
            ports = contract.get(direction)
            if isinstance(ports, dict):
                keys = {str(i) for i in range(len(ports))}
                if set(ports) != keys:
                    raise ValueError(f"{name}.{direction}: indices must be contiguous from zero.")
                ports = [ports[str(i)] for i in range(len(ports))]
            if not isinstance(ports, list):
                raise ValueError(f"{name}.{direction}: expected a list or indexed mapping.")
            roles = set()
            for index, port in enumerate(ports):
                if not isinstance(port, dict) or not isinstance(port.get("name"), str) or not port["name"].strip():
                    raise ValueError(f"{name}.{direction}: each port needs a non-empty semantic name.")
                if "id" in port and (type(port["id"]) is not int or port["id"] != index):
                    raise ValueError(f"{name}.{direction}: port id does not match its physical index.")
                declared = port.get("type")
                values = [declared] if isinstance(declared, str) else declared
                if (not isinstance(values, list) or not values
                        or any(not isinstance(value, str) or not value for value in values)):
                    raise ValueError(f"{name}.{direction}: each port needs declared types.")
                types = {part for value in values for part in value.split("/")}
                if not types <= supported_types:
                    raise ValueError(f"{name}.{direction}: unresolved or unsupported port type.")
                aliases = port.get("aliases", [])
                if not isinstance(aliases, list) or any(
                    not isinstance(alias, str) or not alias.strip() for alias in aliases
                ):
                    raise ValueError(f"{name}.{direction}: aliases must be non-empty strings.")
                for role in [port["name"], *aliases]:
                    normalized = role.strip().lower()
                    if normalized in roles:
                        raise ValueError(f"{name}.{direction}: duplicate semantic role {role!r}.")
                    roles.add(normalized)


class ContractEngine:
    def __init__(
        self, contracts_path: Optional[str] = None,
        *, object_contracts: Optional[Dict[str, Any]] = None,
    ):
        if contracts_path is None:
            base = Path(__file__).resolve().parent.parent / "schema" / "max_contracts.json"
            self.contracts_path = base
        else:
            self.contracts_path = Path(contracts_path)

        self._contracts: Dict[str, Any] = {}
        self._load_contracts()
        if object_contracts is not None:
            validate_contracts({"objects": object_contracts})
            self._contracts.update(object_contracts)

    def _load_contracts(self) -> None:
        with open(self.contracts_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        validate_contracts(data)
        self._contracts = data["objects"]

    @classmethod
    def from_ir(cls, ir: Dict[str, Any]) -> "ContractEngine":
        """Overlay only the generated object's declared ports; never persist them."""
        contract = {}
        for direction in ("inlets", "outlets"):
            ports = ir.get(direction, [])
            contract[direction] = [
                {**port, "name": port.get("name") or f"{direction}_{port['id']}"}
                for port in ports
            ]
        return cls(object_contracts={ir["object_name"]: contract})

    @staticmethod
    def _base_name(obj_name: str) -> str:
        """Nombre base de un objeto Max (primer token); cadena vacia si no hay token."""
        tokens = str(obj_name).strip().split()
        return tokens[0] if tokens else ""

    def get_object_contract(self, obj_name: str) -> Optional[Dict[str, Any]]:
        base_name = self._base_name(obj_name)
        if not base_name:
            return None
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

    @staticmethod
    def port_types(port: Dict[str, Any]) -> set:
        """Normalize a declared union without changing its source representation."""
        declared = port["type"]
        values = [declared] if isinstance(declared, str) else declared
        return {part for value in values for part in value.split("/")}

    def resolve_inlet_index(self, obj_name: str, semantic_role: str) -> int:
        """
        Resuelve el índice físico de un inlet a partir de su rol semántico
        (ej: "pitch", "pitch_bend", "channel", "cutoff").
        """
        inlets = self.get_inlets(obj_name)
        role_lower = semantic_role.strip().lower()
        if not role_lower:
            raise IncompatibleConnectionError("An inlet role must not be empty.")

        exact = [
            idx for idx, port in enumerate(inlets)
            if role_lower in [port.get("name", "").lower(),
                              *[alias.lower() for alias in port.get("aliases", [])]]
        ]
        matches = exact or [
            idx for idx, port in enumerate(inlets)
            if role_lower in port.get("name", "").lower()
        ]
        if len(matches) == 1:
            return matches[0]
        raise IncompatibleConnectionError(
            f"Inlet role {semantic_role!r} is unknown or ambiguous for {obj_name!r}."
        )

    def assess_connection(self, src_obj: str, src_outlet: int, dest_obj: str, dest_inlet: int) -> ConnectionAssessment:
        """Assess declared evidence without treating missing contracts as approval."""
        src_base = self._base_name(src_obj)
        dest_base = self._base_name(dest_obj)

        for index in (src_outlet, dest_inlet):
            if type(index) is not int or index < 0:
                return ConnectionAssessment("INVALID", "Port indices must be non-negative integers.")

        # Regla 1: Prohibición absoluta de conexiones a comment
        if dest_base == "comment":
            return ConnectionAssessment("INVALID", "Cajas 'comment' carecen de inlets funcionales; conexión ilegal.")

        src_contract = self.get_object_contract(src_base)
        dest_contract = self.get_object_contract(dest_base)

        src_outlets = self.get_outlets(src_base)
        dest_inlets = self.get_inlets(dest_base)

        if src_contract is not None and src_outlet >= len(src_outlets):
            return ConnectionAssessment("INVALID", f"Outlet {src_outlet} is outside the declared contract for {src_base}.")
        if dest_contract is not None and dest_inlet >= len(dest_inlets):
            return ConnectionAssessment("INVALID", f"Inlet {dest_inlet} is outside the declared contract for {dest_base}.")
        if src_contract is None or dest_contract is None:
            return ConnectionAssessment("UNVERIFIABLE", "UNVERIFIABLE: missing object contract.")

        src_type = src_outlets[src_outlet].get("type", "anything")
        dest_type = dest_inlets[dest_inlet].get("type", "anything")
        src_types = self.port_types(src_outlets[src_outlet])
        dest_types = self.port_types(dest_inlets[dest_inlet])

        # Regla MSP: señal de audio a señal de audio (auto-summing)
        if "signal" in src_types and "signal" in dest_types:
            return ConnectionAssessment("VALID", "Conexión de signal MSP válida con auto-summing.")

        # Control a señal o viceversa
        if "signal" in src_types and not dest_types.intersection({"signal", "anything"}):
            return ConnectionAssessment("INVALID", f"Desajuste de tipos: señal de audio ({src_type}) hacia inlet de control ({dest_type}).")

        return ConnectionAssessment("VALID", "Conexión válida.")

    def is_valid_connection(self, src_obj: str, src_outlet: int, dest_obj: str, dest_inlet: int) -> Tuple[bool, str]:
        """Legacy tuple interface; unverifiable is not valid."""
        result = self.assess_connection(src_obj, src_outlet, dest_obj, dest_inlet)
        return result.status == "VALID", result.reason

    def validate_connection(
        self, src_obj: str, src_outlet: int, dest_obj: str, dest_inlet: int,
        *, allow_unverifiable: bool = False,
    ) -> ConnectionAssessment:
        result = self.assess_connection(src_obj, src_outlet, dest_obj, dest_inlet)
        if result.status == "INVALID" or (result.status == "UNVERIFIABLE" and not allow_unverifiable):
            raise IncompatibleConnectionError(
                f"Conexión ilegal entre {src_obj} (outlet {src_outlet}) y {dest_obj} (inlet {dest_inlet}): {result.reason}"
            )
        return result
