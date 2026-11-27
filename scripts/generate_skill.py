#!/usr/bin/env python3
"""Stdlib-only AST generator and drift verifier for skills/harmos-cli/SKILL.md."""
import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.compiler.cli_output import emit_json_envelope  # noqa: E402

DEFAULT_SKILL_PATH = Path("skills/harmos-cli/SKILL.md")
_UNRESOLVED = object()
_SUPPRESS = object()

_CLI_TARGETS: Tuple[Tuple[str, str], ...] = (
    ("core/compiler/cli.py", "python -m core.compiler.cli"),
    ("scripts/audit.py", "python scripts/audit.py"),
    ("scripts/check.py", "python scripts/check.py"),
)


@dataclass(frozen=True)
class ArgSpec:
    flags: Tuple[str, ...]
    required: bool = False
    default: Optional[str] = None
    choices: Tuple[str, ...] = ()
    action: Optional[str] = None
    help_text: str = ""
    suppressed_default: bool = False

    @property
    def is_positional(self) -> bool:
        return bool(self.flags) and not self.flags[0].startswith("-")


@dataclass(frozen=True)
class SubcommandSpec:
    name: str
    help_text: str = ""
    args: Tuple[ArgSpec, ...] = ()


@dataclass(frozen=True)
class CommandSpec:
    invocation: str
    source_path: str
    description: str = ""
    root_args: Tuple[ArgSpec, ...] = ()
    subcommands: Tuple[SubcommandSpec, ...] = ()


def _collect_module_constants(tree: ast.Module) -> Dict[str, Any]:
    constants: Dict[str, Any] = {}
    for stmt in tree.body:
        target: Optional[ast.AST] = None
        value_node: Optional[ast.AST] = None
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            target = stmt.targets[0]
            value_node = stmt.value
        elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
            target = stmt.target
            value_node = stmt.value
        if isinstance(target, ast.Name):
            evaluated = _eval_literal(value_node, constants)
            if evaluated is not _UNRESOLVED and evaluated is not _SUPPRESS:
                constants[target.id] = evaluated
    return constants


def _eval_literal(node: Optional[ast.AST], constants: Dict[str, Any]) -> Any:
    if node is None:
        return _UNRESOLVED
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id, _UNRESOLVED)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        operand = _eval_literal(node.operand, constants)
        if isinstance(operand, (int, float)) and not isinstance(operand, bool):
            return -operand if isinstance(node.op, ast.USub) else +operand
        return _UNRESOLVED
    if isinstance(node, (ast.List, ast.Tuple)):
        items = [_eval_literal(elt, constants) for elt in node.elts]
        if any(item is _UNRESOLVED or item is _SUPPRESS for item in items):
            return _UNRESOLVED
        return tuple(items) if isinstance(node, ast.Tuple) else items
    if isinstance(node, ast.Attribute):
        if isinstance(node.value, ast.Name) and node.value.id == "argparse" and node.attr == "SUPPRESS":
            return _SUPPRESS
        return _UNRESOLVED
    if isinstance(node, ast.JoinedStr):
        parts: List[str] = []
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                parts.append(part.value)
            elif isinstance(part, ast.FormattedValue):
                val = _eval_literal(part.value, constants)
                if val is _UNRESOLVED or val is _SUPPRESS:
                    return _UNRESOLVED
                parts.append(str(val))
            else:
                return _UNRESOLVED
        return "".join(parts)
    return _UNRESOLVED


def _is_argparse_parser_call(call: ast.Call) -> bool:
    func = call.func
    if isinstance(func, ast.Attribute) and func.attr == "ArgumentParser":
        return isinstance(func.value, ast.Name) and func.value.id == "argparse"
    return isinstance(func, ast.Name) and func.id == "ArgumentParser"


def _kwarg_node(call: ast.Call, name: str) -> Optional[ast.AST]:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _parse_add_argument(call: ast.Call, constants: Dict[str, Any]) -> Optional[ArgSpec]:
    flags: List[str] = []
    for arg in call.args:
        val = _eval_literal(arg, constants)
        if isinstance(val, str):
            flags.append(val)
    if not flags:
        return None

    required_val = _eval_literal(_kwarg_node(call, "required"), constants)
    required = bool(required_val) if isinstance(required_val, bool) else False

    default_val = _eval_literal(_kwarg_node(call, "default"), constants)
    suppressed_default = default_val is _SUPPRESS
    default_str: Optional[str] = None
    if default_val not in (_UNRESOLVED, _SUPPRESS, None) and not isinstance(default_val, bool):
        default_str = str(default_val)

    choices_val = _eval_literal(_kwarg_node(call, "choices"), constants)
    choices: Tuple[str, ...] = ()
    if isinstance(choices_val, (list, tuple)):
        choices = tuple(str(c) for c in choices_val)

    action_val = _eval_literal(_kwarg_node(call, "action"), constants)
    action = str(action_val) if isinstance(action_val, str) else None

    help_val = _eval_literal(_kwarg_node(call, "help"), constants)
    help_text = str(help_val) if isinstance(help_val, str) else ""

    return ArgSpec(
        flags=tuple(flags),
        required=required,
        default=default_str,
        choices=choices,
        action=action,
        help_text=help_text,
        suppressed_default=suppressed_default,
    )


def extract_parser_spec(file_path: Path, invocation: str, rel_source: str) -> CommandSpec:
    """Extract CLI subcommands and arguments from a module's build_parser() via AST."""
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=rel_source)
    constants = _collect_module_constants(tree)

    build_fn: Optional[ast.FunctionDef] = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "build_parser":
            build_fn = node
            break
    if build_fn is None:
        raise ValueError(f"build_parser() not found in {rel_source}")

    root_parser_var: Optional[str] = None
    subparsers_var: Optional[str] = None
    description = ""
    root_args: List[ArgSpec] = []
    subcommands_order: List[str] = []
    subparser_vars: Dict[str, str] = {}
    subcommand_help: Dict[str, str] = {}
    subcommand_args: Dict[str, List[ArgSpec]] = {}

    for stmt in build_fn.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
            target_name = stmt.targets[0].id
            if isinstance(stmt.value, ast.Call):
                call = stmt.value
                if _is_argparse_parser_call(call):
                    root_parser_var = target_name
                    desc_val = _eval_literal(_kwarg_node(call, "description"), constants)
                    if isinstance(desc_val, str):
                        description = desc_val
                    continue

                if (
                    isinstance(call.func, ast.Attribute)
                    and isinstance(call.func.value, ast.Name)
                    and call.func.value.id == root_parser_var
                    and call.func.attr == "add_subparsers"
                ):
                    subparsers_var = target_name
                    continue

                if (
                    subparsers_var is not None
                    and isinstance(call.func, ast.Attribute)
                    and isinstance(call.func.value, ast.Name)
                    and call.func.value.id == subparsers_var
                    and call.func.attr == "add_parser"
                    and call.args
                ):
                    sub_name = _eval_literal(call.args[0], constants)
                    if isinstance(sub_name, str):
                        help_val = _eval_literal(_kwarg_node(call, "help"), constants)
                        subparser_vars[target_name] = sub_name
                        subcommands_order.append(sub_name)
                        subcommand_help[sub_name] = str(help_val) if isinstance(help_val, str) else ""
                        subcommand_args[sub_name] = []
                    continue

        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
            if isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name) and call.func.attr == "add_argument":
                owner = call.func.value.id
                arg_spec = _parse_add_argument(call, constants)
                if arg_spec is None:
                    continue
                if owner == root_parser_var:
                    root_args.append(arg_spec)
                elif owner in subparser_vars:
                    subcommand_args[subparser_vars[owner]].append(arg_spec)

    subcommands = tuple(
        SubcommandSpec(
            name=name,
            help_text=subcommand_help[name],
            args=tuple(subcommand_args[name]),
        )
        for name in subcommands_order
    )
    return CommandSpec(
        invocation=invocation,
        source_path=rel_source,
        description=description,
        root_args=tuple(root_args),
        subcommands=subcommands,
    )


def extract_cli_specs(repo_root: Optional[Path] = None) -> List[CommandSpec]:
    """Extract CommandSpec metadata for all canonical Harmos CLI entrypoints."""
    root = (repo_root or _REPO_ROOT).resolve()
    return [
        extract_parser_spec(root / rel_path, invocation, rel_path)
        for rel_path, invocation in _CLI_TARGETS
    ]


def _format_arg_summary(arg: ArgSpec) -> str:
    label = "/".join(arg.flags)
    if arg.required:
        label += "*"
    if arg.choices:
        label += f" ({'/'.join(arg.choices)})"
    elif arg.default is not None and not arg.suppressed_default:
        label += f" (default: {arg.default})"
    return f"`{label}`"


def render_skill_markdown(specs: Sequence[CommandSpec]) -> str:
    """Render deterministic, compact LLM-first SKILL.md from extracted CLI AST specs."""
    lines: List[str] = [
        "---",
        "name: harmos-cli",
        'description: "Trigger: harmos cli, compile ir, audit maxpat, check guardrail, --json output. Invoke Harmos CLIs with deterministic flags and JSON envelopes."',
        "license: Apache-2.0",
        "metadata:",
        '  author: "harmos-ast-generator"',
        '  version: "1.0"',
        "---",
        "",
        "<!-- Auto-generated from CLI parser AST by scripts/generate_skill.py. Do not edit manually. -->",
        "",
        "# Harmos CLI",
        "",
        "## Activation Contract",
        "",
        "Load when invoking `core.compiler.cli`, `scripts/audit.py`, or `scripts/check.py` to compile IRs, verify provenance, run oracles, audit `.maxpat` files, or run repository guardrails.",
        "",
        "## Hard Rules",
        "",
        "- **Prefer `--json` for Automation**: Pass `--json` to parse deterministic envelopes instead of scraping text output.",
        "- **Live Runtime Audit Mandatory**: Certify `.maxpat` runtime behavior only via `scripts/audit.py`; `BLOCKED` (`exit_code: 2`) is never `PASS`.",
        "- **Zero Hardcoding & Privacy**: Never hardcode Max ports outside `core/schema/max_contracts.json` or commit host paths; run `scripts/check.py` before commits.",
        "",
        "## Decision Gates",
        "",
        "| Task | Entrypoint | Exit Codes |",
        "| :--- | :--- | :--- |",
        "| Compile IR, extract, diff, bench, or emit `.maxref.xml` | `python -m core.compiler.cli` | `0` ok, `1` fail |",
        "| Audit `.maxpat` contracts and Max runtime | `python scripts/audit.py` | `0` PASS, `1` FAIL, `2` BLOCKED |",
        "| Run full tests, schemas, privacy, and skill sync | `python scripts/check.py` | `0` PASS, `1` FAIL |",
        "",
        "## Execution Steps",
        "",
    ]

    for spec in specs:
        lines.append(f"### `{spec.invocation}` (`{spec.source_path}`)")
        lines.append("")
        if spec.root_args:
            root_flags = ", ".join(_format_arg_summary(arg) for arg in spec.root_args)
            lines.append(f"Root options: {root_flags}")
            lines.append("")
        if spec.subcommands:
            lines.append("| Subcommand | Positional | Options |")
            lines.append("| :--- | :--- | :--- |")
            for sub in spec.subcommands:
                pos = ", ".join(_format_arg_summary(a) for a in sub.args if a.is_positional) or "-"
                opts = ", ".join(_format_arg_summary(a) for a in sub.args if not a.is_positional) or "-"
                lines.append(f"| `{sub.name}` | {pos} | {opts} |")
            lines.append("")

    lines.extend([
        "## Output Contract",
        "",
        "Every `--json` invocation emits a single JSON object on stdout with exact keys:",
        '`{"status": str, "command": str, "artifacts": dict, "diagnostics": list[str], "exit_code": int}`.',
        "",
        "## References",
        "",
        "- `AGENTS.md` — Repository hard rules and canonical commands.",
        "- `core/compiler/cli.py` — Compiler, extractor, oracle diff, and doc CLI.",
        "- `scripts/audit.py` — Live Max runtime and contract auditor.",
        "- `scripts/check.py` — Pre-commit guardrail and AST skill drift check.",
        "- `scripts/generate_skill.py` — Stdlib AST generator for this skill.",
    ])

    return "\n".join(lines) + "\n"


def _display_path(target: Path, root: Path) -> str:
    try:
        return target.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return target.name


def verify_skill_sync(
    repo_root: Optional[Path] = None,
    skill_path: Optional[Path] = None,
) -> Tuple[str, List[str]]:
    """Compare target SKILL.md against AST-rendered output without mutating files."""
    root = (repo_root or _REPO_ROOT).resolve()
    target = Path(skill_path) if skill_path is not None else (root / DEFAULT_SKILL_PATH)
    label = _display_path(target, root)
    expected = render_skill_markdown(extract_cli_specs(root))

    if not target.is_file():
        return "MISSING", [f"Generated skill missing ({label}). Run `python scripts/generate_skill.py`."]

    actual = target.read_text(encoding="utf-8").replace("\r\n", "\n")
    if actual != expected:
        return "DRIFT", [f"Generated skill out of sync ({label}). Run `python scripts/generate_skill.py`."]

    return "PASS", [f"Generated skill matches CLI AST ({label})."]


def write_skill_file(
    repo_root: Optional[Path] = None,
    skill_path: Optional[Path] = None,
) -> Path:
    """Render and write the AST-generated SKILL.md deterministically with LF newlines."""
    root = (repo_root or _REPO_ROOT).resolve()
    target = Path(skill_path) if skill_path is not None else (root / DEFAULT_SKILL_PATH)
    content = render_skill_markdown(extract_cli_specs(root))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8", newline="\n")
    return target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate or verify skills/harmos-cli/SKILL.md from Harmos CLI parser ASTs."
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Target SKILL.md path (default: skills/harmos-cli/SKILL.md)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        default=False,
        help="Check whether SKILL.md matches CLI ASTs without writing",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        dest="json_output",
        help="Emitir salida estructurada en formato JSON uniforme",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    target = Path(args.output) if args.output else (_REPO_ROOT / DEFAULT_SKILL_PATH)
    label = _display_path(target, _REPO_ROOT)

    if args.check:
        status, diagnostics = verify_skill_sync(repo_root=_REPO_ROOT, skill_path=target)
        exit_code = 0 if status == "PASS" else 1
    else:
        written = write_skill_file(repo_root=_REPO_ROOT, skill_path=target)
        label = _display_path(written, _REPO_ROOT)
        status = "PASS"
        diagnostics = [f"Generated {label} from CLI AST."]
        exit_code = 0

    if args.json_output:
        emit_json_envelope(
            status=status,
            command="generate-skill",
            artifacts={"skill_path": label},
            diagnostics=diagnostics,
            exit_code=exit_code,
        )
    else:
        for line in diagnostics:
            print(line)

    if exit_code != 0:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
