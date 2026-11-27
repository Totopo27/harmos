"""Uniform JSON output envelope helpers for Harmos CLI entrypoints."""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

ENVELOPE_KEYS = ("status", "command", "artifacts", "diagnostics", "exit_code")


def _normalize_value(value: Any) -> Any:
    """Recursively convert Path objects and containers into JSON-safe primitives."""
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _normalize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize_value(item) for item in value]
    return value


def build_json_envelope(
    *,
    status: str,
    command: str,
    artifacts: Optional[Dict[str, Any]] = None,
    diagnostics: Optional[Sequence[str]] = None,
    exit_code: int,
) -> Dict[str, Any]:
    """Build the canonical Harmos CLI JSON response envelope."""
    normalized_artifacts = _normalize_value(dict(artifacts)) if artifacts else {}
    normalized_diagnostics: List[str] = [str(item) for item in diagnostics] if diagnostics else []
    return {
        "status": str(status),
        "command": str(command),
        "artifacts": normalized_artifacts,
        "diagnostics": normalized_diagnostics,
        "exit_code": int(exit_code),
    }


def format_json_envelope(envelope: Dict[str, Any]) -> str:
    """Serialize a JSON envelope deterministically using ASCII-safe escaping."""
    return json.dumps(envelope, indent=2, ensure_ascii=True)


def emit_json_envelope(
    *,
    status: str,
    command: str,
    artifacts: Optional[Dict[str, Any]] = None,
    diagnostics: Optional[Sequence[str]] = None,
    exit_code: int,
) -> Dict[str, Any]:
    """Build, print to stdout, and return the canonical Harmos JSON envelope."""
    envelope = build_json_envelope(
        status=status,
        command=command,
        artifacts=artifacts,
        diagnostics=diagnostics,
        exit_code=exit_code,
    )
    print(format_json_envelope(envelope))
    return envelope
