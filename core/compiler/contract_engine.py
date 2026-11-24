"""
Harmos Contract Engine: Introspección y validación estricta de contratos Max MSP.
Consume core/schema/max_contracts.json.
"""
import hashlib
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
    _RAW_CONTRACTS_CACHE: Dict[Tuple[str, bytes], Dict[str, Any]] = {}

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
        self._inlet_role_map: Dict[str, Dict[str, int]] = {}
        self._outlet_role_map: Dict[str, Dict[str, int]] = {}
        self._load_contracts()
        if object_contracts is not None:
            validate_contracts({"objects": object_contracts})
            for name, contract in object_contracts.items():
                inlets = self._normalize_ports(contract.get("inlets", []))
                outlets = self._normalize_ports(contract.get("outlets", []))
                self._contracts[name] = {"inlets": inlets, "outlets": outlets}
                self._index_object_roles(name, inlets, outlets)

    def _index_object_roles(self, name: str, inlets: List[Dict[str, Any]], outlets: List[Dict[str, Any]]) -> None:
        inlet_map: Dict[str, int] = {}
        for idx, port in enumerate(inlets):
            inlet_map[port["name"].lower()] = idx
            for alias in port.get("aliases", []):
                inlet_map[alias.lower()] = idx
        self._inlet_role_map[name] = inlet_map

        outlet_map: Dict[str, int] = {}
        for idx, port in enumerate(outlets):
            outlet_map[port["name"].lower()] = idx
            for alias in port.get("aliases", []):
                outlet_map[alias.lower()] = idx
        self._outlet_role_map[name] = outlet_map

    def _load_contracts(self) -> None:
        path_obj = self.contracts_path.resolve()
        raw_bytes = self.contracts_path.read_bytes()
        cache_key = (str(path_obj), hashlib.sha256(raw_bytes).digest())
        if cache_key in self._RAW_CONTRACTS_CACHE:
            data = self._RAW_CONTRACTS_CACHE[cache_key]
        else:
            data = json.loads(raw_bytes.decode("utf-8"))
            validate_contracts(data)
            self._RAW_CONTRACTS_CACHE[cache_key] = data

        self._contracts = {}
        self._inlet_role_map = {}
        self._outlet_role_map = {}
        for name, contract in data["objects"].items():
            inlets = self._normalize_ports(contract.get("inlets", []))
            outlets = self._normalize_ports(contract.get("outlets", []))
            self._contracts[name] = {"inlets": inlets, "outlets": outlets}
            self._index_object_roles(name, inlets, outlets)

    @classmethod
    def from_ir(cls, ir: Dict[str, Any]) -> "ContractEngine":
        """Overlay only the generated object's declared ports; never persist them."""
        if not isinstance(ir, dict) or "object_name" not in ir:
            raise ValueError("IR must be a dictionary with an 'object_name' field.")
        if "inlets" not in ir or not isinstance(ir["inlets"], list):
            raise ValueError("IR must declare an 'inlets' list.")
        if "outlets" not in ir or not isinstance(ir["outlets"], list):
            raise ValueError("IR must declare an 'outlets' list.")

        contract = {}
        for direction in ("inlets", "outlets"):
            ports = ir.get(direction, [])
            contract[direction] = [
                {**port, "name": port.get("name") or f"{direction}_{port.get('id', i)}"}
                for i, port in enumerate(ports)
            ]
        return cls(object_contracts={ir["object_name"]: contract})

    @staticmethod
    def _base_name(obj_name: str) -> str:
        """Nombre base de un objeto Max (primer token); cadena vacia si no hay token."""
        tokens = str(obj_name).strip().split()
        return tokens[0] if tokens else ""

    @staticmethod
    def _synthesize_dynamic_contract(base_name: str, args: List[str]) -> Dict[str, Any]:
        """
        Synthesize dynamic inlet/outlet port layout for variable-arity Max objects:
        unpack, pack, trigger (t), route.
        """
        if base_name == "unpack":
            outlets = []
            for i, arg in enumerate(args):
                arg_l = arg.lower()
                if arg_l.startswith("f") or "." in arg:
                    port_type = "float"
                elif arg_l.startswith("i") or arg.lstrip("-").isdigit():
                    port_type = "int"
                elif arg_l.startswith("s"):
                    port_type = "symbol"
                else:
                    port_type = "anything"
                outlets.append({
                    "id": i,
                    "name": f"element_{i}",
                    "type": port_type,
                    "aliases": [f"elem_{i}", f"val_{i}"]
                })
            return {
                "inlets": [{"id": 0, "name": "input_list", "type": "list", "aliases": ["input", "list_in"]}],
                "outlets": outlets
            }

        elif base_name == "pack":
            inlets = []
            for i, arg in enumerate(args):
                arg_l = arg.lower()
                if arg_l.startswith("f") or "." in arg:
                    port_type = "float"
                elif arg_l.startswith("i") or arg.lstrip("-").isdigit():
                    port_type = "int"
                elif arg_l.startswith("s"):
                    port_type = "symbol"
                else:
                    port_type = "anything"
                inlets.append({
                    "id": i,
                    "name": f"element_{i}",
                    "type": port_type,
                    "aliases": [f"elem_{i}", f"inlet_{i}"]
                })
            return {
                "inlets": inlets,
                "outlets": [{"id": 0, "name": "packed_list", "type": "list", "aliases": ["list_out", "output"]}]
            }

        elif base_name in ("trigger", "t"):
            outlets = []
            for i, arg in enumerate(args):
                arg_l = arg.lower()
                if arg_l in ("b", "bang"):
                    port_type = "bang"
                elif arg_l in ("i", "int"):
                    port_type = "int"
                elif arg_l in ("f", "float") or "." in arg:
                    port_type = "float"
                elif arg_l in ("s", "symbol", "sym"):
                    port_type = "symbol"
                elif arg_l in ("l", "list"):
                    port_type = "list"
                elif arg.lstrip("-").isdigit():
                    port_type = "int"
                else:
                    port_type = "anything"
                outlets.append({
                    "id": i,
                    "name": f"outlet_{i}",
                    "type": port_type,
                    "aliases": [f"out_{i}"]
                })
            return {
                "inlets": [{"id": 0, "name": "input_value", "type": "anything", "aliases": ["input"]}],
                "outlets": outlets
            }

        elif base_name == "route":
            outlets = []
            for i, arg in enumerate(args):
                outlets.append({
                    "id": i,
                    "name": f"match_{arg}",
                    "type": "anything",
                    "aliases": [f"match_{i}", arg]
                })
            outlets.append({
                "id": len(args),
                "name": "unmatched_pass",
                "type": "anything",
                "aliases": ["pass_through", "unmatched", "nomatch"]
            })
            return {
                "inlets": [{"id": 0, "name": "input_message", "type": "anything", "aliases": ["input"]}],
                "outlets": outlets
            }

        return {}

    def get_object_contract(self, obj_name: str) -> Optional[Dict[str, Any]]:
        tokens = str(obj_name).strip().split()
        if not tokens:
            return None
        base_name = tokens[0]
        args = tokens[1:]

        # Dynamic arity synthesis for parameterized objects
        if args and base_name in ("unpack", "pack", "trigger", "t", "route"):
            return self._synthesize_dynamic_contract(base_name, args)

        return self._contracts.get(base_name)

    def _normalize_ports(self, ports_data: Union[Dict[str, Any], List[Any]]) -> List[Dict[str, Any]]:
        """Convierte diccionario {"0": {...}, "1": {...}} o lista en una lista indexada en base 0."""
        if isinstance(ports_data, dict):
            res = []
            for k in sorted(ports_data.keys(), key=lambda x: int(x) if x.isdigit() else 999):
                res.append(ports_data[k])
            return res
        elif isinstance(ports_data, list):
            return list(ports_data)
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
        declared = port.get("type", "anything")
        values = [declared] if isinstance(declared, str) else declared
        return {part for value in values for part in value.split("/")}

    def resolve_inlet_index(self, obj_name: str, semantic_role: str) -> int:
        """
        Resuelve el índice físico de un inlet a partir de su rol semántico
        (ej: "pitch", "pitch_bend", "channel", "cutoff").
        """
        role_lower = semantic_role.strip().lower()
        if not role_lower:
            raise IncompatibleConnectionError("An inlet role must not be empty.")

        # Fast path O(1) para objetos estáticos del catálogo
        tokens = str(obj_name).strip().split()
        if len(tokens) == 1 and tokens[0] in self._inlet_role_map:
            if role_lower in self._inlet_role_map[tokens[0]]:
                return self._inlet_role_map[tokens[0]][role_lower]

        inlets = self.get_inlets(obj_name)
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
        avail = [p.get("name") for p in inlets]
        raise IncompatibleConnectionError(
            f"Inlet role {semantic_role!r} is unknown or ambiguous for {obj_name!r}. Available inlets: {avail}"
        )

    def resolve_outlet_index(self, obj_name: str, semantic_role: str) -> int:
        """
        Resuelve el índice físico de un outlet a partir de su rol semántico
        (ej: "audio_out", "envelope_signal", "voice_index").
        """
        role_lower = semantic_role.strip().lower()
        if not role_lower:
            raise IncompatibleConnectionError("An outlet role must not be empty.")

        # Fast path O(1) para objetos estáticos del catálogo
        tokens = str(obj_name).strip().split()
        if len(tokens) == 1 and tokens[0] in self._outlet_role_map:
            if role_lower in self._outlet_role_map[tokens[0]]:
                return self._outlet_role_map[tokens[0]][role_lower]

        outlets = self.get_outlets(obj_name)
        exact = [
            idx for idx, port in enumerate(outlets)
            if role_lower in [port.get("name", "").lower(),
                              *[alias.lower() for alias in port.get("aliases", [])]]
        ]
        matches = exact or [
            idx for idx, port in enumerate(outlets)
            if role_lower in port.get("name", "").lower()
        ]
        if len(matches) == 1:
            return matches[0]
        avail = [p.get("name") for p in outlets]
        raise IncompatibleConnectionError(
            f"Outlet role {semantic_role!r} is unknown or ambiguous for {obj_name!r}. Available outlets: {avail}"
        )

    def assess_connection(self, src_obj: str, src_outlet: int, dest_obj: str, dest_inlet: int) -> ConnectionAssessment:
        """Assess declared evidence without treating missing contracts as approval."""
        src_base = self._base_name(src_obj)
        dest_base = self._base_name(dest_obj)

        for index in (src_outlet, dest_inlet):
            if type(index) is not int or index < 0:
                return ConnectionAssessment("INVALID", "Port indices must be non-negative integers.")

        # Regla: Prohibición absoluta de conexiones a o desde comment
        if dest_base == "comment":
            return ConnectionAssessment("INVALID", "Comment boxes have no functional inlets; illegal connection.")
        if src_base == "comment":
            return ConnectionAssessment("INVALID", "Comment boxes have no functional outlets; illegal connection.")

        src_contract = self.get_object_contract(src_obj)
        dest_contract = self.get_object_contract(dest_obj)

        src_outlets = self.get_outlets(src_obj)
        dest_inlets = self.get_inlets(dest_obj)

        if src_contract is not None and src_outlet >= len(src_outlets):
            max_idx = max(0, len(src_outlets) - 1)
            return ConnectionAssessment("INVALID", f"Outlet {src_outlet} is outside the declared contract for {src_obj} (range 0..{max_idx}).")
        if dest_contract is not None and dest_inlet >= len(dest_inlets):
            max_idx = max(0, len(dest_inlets) - 1)
            return ConnectionAssessment("INVALID", f"Inlet {dest_inlet} is outside the declared contract for {dest_obj} (range 0..{max_idx}).")
        if src_contract is None or dest_contract is None:
            missing = src_obj if src_contract is None else dest_obj
            return ConnectionAssessment("UNVERIFIABLE", f"UNVERIFIABLE: missing object contract for {missing!r}.")

        src_port = src_outlets[src_outlet]
        dest_port = dest_inlets[dest_inlet]
        src_type = src_port.get("type", "anything")
        dest_type = dest_port.get("type", "anything")
        src_types = self.port_types(src_port)
        dest_types = self.port_types(dest_port)

        # Regla MSP: señal de audio a señal de audio (auto-summing)
        if "signal" in src_types and "signal" in dest_types:
            return ConnectionAssessment("VALID", "Valid MSP signal connection with auto-summing.")

        # Audio signal hacia inlet de control o message (incluso anything) -> Ilegal en Max MSP
        if "signal" in src_types and "signal" not in dest_types:
            return ConnectionAssessment(
                "INVALID",
                f"Type mismatch: audio signal ({src_type}) cannot connect to control inlet ({dest_type})."
            )

        # Control message hacia inlet exclusivo de señal -> Ilegal en Max MSP
        if "signal" not in src_types and dest_types == {"signal"}:
            return ConnectionAssessment(
                "INVALID",
                f"Type mismatch: control message ({src_type}) cannot connect to signal-only inlet ({dest_type})."
            )

        # Control message hacia inlet que acepta signal + control o puramente control
        allowed_dest = dest_types - {"signal"} if "signal" in dest_types else dest_types

        if "anything" in src_types or "anything" in allowed_dest:
            return ConnectionAssessment("VALID", "Valid connection.")

        if src_types.intersection(allowed_dest):
            return ConnectionAssessment("VALID", "Valid connection.")

        # Coerción numérica en Max (int <-> float <-> number)
        numeric_types = {"int", "float", "number"}
        if src_types.intersection(numeric_types) and allowed_dest.intersection(numeric_types):
            return ConnectionAssessment("VALID", "Valid numeric connection with automatic coercion.")

        # Triggers bang
        if "bang" in src_types and allowed_dest:
            return ConnectionAssessment("VALID", "Valid trigger connection (bang).")

        # List unpacking a escalar
        if "list" in src_types and allowed_dest.intersection(numeric_types):
            return ConnectionAssessment("VALID", "Valid connection with list head element extraction.")

        return ConnectionAssessment("INVALID", f"Control type mismatch: {src_type} is incompatible with {dest_type}.")

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
                f"Illegal connection between {src_obj} (outlet {src_outlet}) and {dest_obj} (inlet {dest_inlet}): {result.reason}"
            )
        return result
