"""
Harmos Provenance Engine: Huella criptográfica de procedencia (emitted-from.json).
Inspirado en el estándar de procedencia de rust-anything (recorded-from.json).
Registra hashes SHA-256 inmutables de código fuente, especificación IR y contratos de Max MSP.
"""
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple

HARMOS_VERSION = "0.2.0"


TEXT_EXTENSIONS = {
    ".json", ".maxpat", ".cpp", ".hpp", ".h", ".c", ".txt", ".cmake",
    ".py", ".md", ".xml", ".sc", ".scd", ".yml", ".yaml"
}


def compute_file_sha256(filepath: Path | str, normalize_newlines: bool = True) -> str:
    """
    Calcula el hash SHA-256 de un archivo en modo binario.
    Si el archivo es de texto (o extensión de texto conocida) y normalize_newlines=True,
    normaliza los saltos de línea (CRLF -> LF) para asegurar determinismo multiplataforma.
    """
    p = Path(filepath)
    if not p.is_file():
        raise FileNotFoundError(f"Archivo no encontrado para computar hash: {filepath}")

    hasher = hashlib.sha256()
    is_text = p.suffix.lower() in TEXT_EXTENSIONS or p.name == "CMakeLists.txt"
    if normalize_newlines and is_text:
        with open(p, "rb") as f:
            data = f.read()
        normalized = data.replace(b"\r\n", b"\n")
        hasher.update(normalized)
    else:
        with open(p, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
    return hasher.hexdigest()


def resolve_canonical_contracts_path() -> Path:
    """Localiza el archivo canónico core/schema/max_contracts.json."""
    current_dir = Path(__file__).resolve().parent
    schema_path = current_dir.parent / "schema" / "max_contracts.json"
    if schema_path.is_file():
        return schema_path
    
    # Búsqueda de respaldo en raíz de repo
    root_candidate = current_dir.parent.parent / "core" / "schema" / "max_contracts.json"
    if root_candidate.is_file():
        return root_candidate

    raise FileNotFoundError(f"No se encontró max_contracts.json en la ruta esperada: {schema_path}")


def build_provenance_record(
    ir_path: Path | str,
    source_path: Optional[Path | str] = None,
    contracts_path: Optional[Path | str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None,
    artifacts: Optional[Dict[str, Path | str]] = None
) -> Dict[str, Any]:
    """
    Construye el registro de procedencia inmutable.
    """
    ir_p = Path(ir_path)
    contracts_p = Path(contracts_path) if contracts_path else resolve_canonical_contracts_path()

    ir_hash = compute_file_sha256(ir_p)
    contracts_hash = compute_file_sha256(contracts_p)

    record: Dict[str, Any] = {
        "harmos_version": HARMOS_VERSION,
        "emitted_at": datetime.now(timezone.utc).isoformat(),
        "contracts": {
            "file": contracts_p.name,
            "sha256": contracts_hash
        },
        "ir": {
            "file": ir_p.name,
            "sha256": ir_hash
        }
    }

    if source_path:
        src_p = Path(source_path)
        if src_p.is_file():
            record["source"] = {
                "file": src_p.name,
                "sha256": compute_file_sha256(src_p)
            }

    if artifacts:
        recorded_artifacts: Dict[str, Dict[str, str]] = {}
        for key, artifact_path in artifacts.items():
            artifact_p = Path(artifact_path)
            if artifact_p.is_file():
                recorded_artifacts[key] = {
                    "file": artifact_p.name,
                    "sha256": compute_file_sha256(artifact_p)
                }
        if recorded_artifacts:
            record["artifacts"] = recorded_artifacts

    if extra_metadata:
        record["metadata"] = extra_metadata

    return record


def write_provenance_file(output_dir: Path | str, record: Dict[str, Any]) -> Path:
    """Escribe el archivo emitted-from.json en el directorio objetivo."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target_file = out_dir / "emitted-from.json"
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=4)
    return target_file


def verify_provenance(
    emitted_from_path: Path | str,
    current_contracts_path: Optional[Path | str] = None,
    current_ir_path: Optional[Path | str] = None,
    current_source_path: Optional[Path | str] = None
) -> Tuple[str, List[str]]:
    """
    Verifica un archivo emitted-from.json contra los contratos y fuentes actuales.
    Devuelve (estado, detalles).
    Estados: VALID, STALE_CONTRACTS, STALE_IR, STALE_SOURCE, STALE_ARTIFACTS,
    UNVERIFIABLE, INVALID.

    Regla de honestidad: cuando la evidencia no puede leerse o el registro no
    contiene la huella solicitada, el veredicto es UNVERIFIABLE, nunca VALID.
    """
    p = Path(emitted_from_path)
    if p.is_dir():
        p = p / "emitted-from.json"

    if not p.is_file():
        return "INVALID", [f"Archivo de procedencia no encontrado: {p}"]

    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return "INVALID", [f"Error al parsear emitted-from.json: {e}"]

    details: List[str] = []

    # 0. Integridad estructural: un registro malformado es INVALID, nunca una excepción
    if not isinstance(data, dict):
        return "INVALID", ["La raíz de emitted-from.json no es un objeto JSON."]

    for section in ("contracts", "ir", "source", "artifacts"):
        value = data.get(section)
        if value is not None and not isinstance(value, dict):
            return "INVALID", [
                f"La sección '{section}' de emitted-from.json no es un objeto JSON.",
                "El registro está malformado y no puede usarse como evidencia de procedencia."
            ]

    # 1. Validar contratos (fail-closed: sin contratos legibles no hay veredicto positivo)
    recorded_contracts = data.get("contracts") or {}
    recorded_contracts_hash = recorded_contracts.get("sha256")
    if not recorded_contracts_hash:
        return "UNVERIFIABLE", [
            "El registro de procedencia no contiene la huella SHA-256 de los contratos.",
            "Sin huella de contratos no es posible certificar la ausencia de deriva."
        ]

    try:
        contracts_p = Path(current_contracts_path) if current_contracts_path else resolve_canonical_contracts_path()
        current_contracts_hash = compute_file_sha256(contracts_p)
    except Exception as e:
        return "UNVERIFIABLE", [
            "No se pudo computar el hash de los contratos canónicos de Max MSP.",
            f"Causa: {e}",
            "Sin contratos verificables la procedencia del parche no está certificada."
        ]

    if recorded_contracts_hash != current_contracts_hash:
        return "STALE_CONTRACTS", [
            "Los contratos canónicos de Max MSP han cambiado desde la emisión de este parche.",
            f"Contrato registrado: {recorded_contracts_hash[:12]}...",
            f"Contrato actual:     {current_contracts_hash[:12]}...",
            "Riesgo: El parche emitido puede contener índices o tipos de inlets obsoletos."
        ]
    details.append(f"Contratos OK: {contracts_p.name} ({current_contracts_hash[:8]})")

    # 2. Validar IR si se provee (fail-closed: pedir verificacion con evidencia ausente no es VALID)
    if current_ir_path:
        recorded_ir = data.get("ir") or {}
        recorded_ir_hash = recorded_ir.get("sha256")
        if not recorded_ir_hash:
            return "UNVERIFIABLE", [
                "El registro de procedencia no contiene huella de IR.",
                "Se solicitó verificar el IR actual pero no existe huella registrada contra la cual comparar."
            ]

        ir_p = Path(current_ir_path)
        if not ir_p.is_file():
            return "UNVERIFIABLE", [f"IR actual no encontrado: {ir_p}"]

        current_ir_hash = compute_file_sha256(ir_p)
        if recorded_ir_hash != current_ir_hash:
            return "STALE_IR", [
                f"La especificación IR ({ir_p.name}) ha sido modificada tras la emisión.",
                f"IR registrada: {recorded_ir_hash[:12]}...",
                f"IR actual:     {current_ir_hash[:12]}..."
            ]
        details.append(f"IR OK: {ir_p.name} ({current_ir_hash[:8]})")

    # 3. Validar código fuente si se provee (misma regla fail-closed)
    if current_source_path:
        recorded_src = data.get("source") or {}
        recorded_src_hash = recorded_src.get("sha256")
        if not recorded_src_hash:
            return "UNVERIFIABLE", [
                "El registro de procedencia no contiene huella del código fuente.",
                "Se solicitó verificar el fuente actual pero no existe huella registrada contra la cual comparar."
            ]

        src_p = Path(current_source_path)
        if not src_p.is_file():
            return "UNVERIFIABLE", [f"Código fuente actual no encontrado: {src_p}"]

        current_src_hash = compute_file_sha256(src_p)
        if recorded_src_hash != current_src_hash:
            return "STALE_SOURCE", [
                f"El código fuente ({src_p.name}) ha sido modificado tras la emisión.",
                f"Fuente registrada: {recorded_src_hash[:12]}...",
                f"Fuente actual:     {current_src_hash[:12]}..."
            ]
        details.append(f"Fuente OK: {src_p.name} ({current_src_hash[:8]})")

    # 4. Validar artefactos emitidos (.maxpat, .cpp, CMakeLists.txt)
    recorded_artifacts = data.get("artifacts")
    if recorded_artifacts:
        base_dir = p.parent
        for artifact_key in sorted(recorded_artifacts):
            entry = recorded_artifacts.get(artifact_key)
            if not isinstance(entry, dict):
                return "INVALID", [
                    f"La entrada del artefacto '{artifact_key}' no es un objeto JSON.",
                    "El registro está malformado y no puede usarse como evidencia de procedencia."
                ]
            artifact_hash = entry.get("sha256")
            artifact_file = entry.get("file")
            if not artifact_hash or not artifact_file:
                return "UNVERIFIABLE", [
                    f"Entrada de artefacto '{artifact_key}' incompleta en el registro.",
                    "No es posible certificar la integridad del artefacto emitido."
                ]

            artifact_p = base_dir / artifact_file
            if not artifact_p.is_file():
                return "UNVERIFIABLE", [
                    f"Artefacto registrado no encontrado: {artifact_file}",
                    "El registro declara un artefacto emitido que ya no está junto al archivo de procedencia."
                ]

            current_artifact_hash = compute_file_sha256(artifact_p)
            if artifact_hash != current_artifact_hash:
                return "STALE_ARTIFACTS", [
                    f"El artefacto emitido '{artifact_file}' fue modificado tras la emisión.",
                    f"Artefacto registrado: {artifact_hash[:12]}...",
                    f"Artefacto actual:     {current_artifact_hash[:12]}..."
                ]
            details.append(f"Artefacto OK: {artifact_file} ({current_artifact_hash[:8]})")
    else:
        details.append(
            "Registro sin huella de artefactos: se certifican solo los insumos "
            "(contratos, IR, fuente); la integridad del parche emitido no es verificable."
        )

    emitted_at = data.get("emitted_at", "Desconocido")
    details.append(f"Fecha de emisión: {emitted_at}")
    details.append(f"Versión de Harmos: {data.get('harmos_version', 'Desconocida')}")

    return "VALID", details
