---
name: harmos-cli
description: "Trigger: harmos cli, compile ir, audit maxpat, check guardrail, --json output. Invoke Harmos CLIs with deterministic flags and JSON envelopes."
license: Apache-2.0
metadata:
  author: "harmos-ast-generator"
  version: "1.0"
---

<!-- Auto-generated from CLI parser AST by scripts/generate_skill.py. Do not edit manually. -->

# Harmos CLI

## Activation Contract

Load when invoking `core.compiler.cli`, `scripts/audit.py`, or `scripts/check.py` to compile IRs, verify provenance, run oracles, audit `.maxpat` files, or run repository guardrails.

## Hard Rules

- **Prefer `--json` for Automation**: Pass `--json` to parse deterministic envelopes instead of scraping text output.
- **Live Runtime Audit Mandatory**: Certify `.maxpat` runtime behavior only via `scripts/audit.py`; `BLOCKED` (`exit_code: 2`) is never `PASS`.
- **Zero Hardcoding & Privacy**: Never hardcode Max ports outside `core/schema/max_contracts.json` or commit host paths; run `scripts/check.py` before commits.

## Decision Gates

| Task | Entrypoint | Exit Codes |
| :--- | :--- | :--- |
| Compile IR, extract, diff, bench, or emit `.maxref.xml` | `python -m core.compiler.cli` | `0` ok, `1` fail |
| Audit `.maxpat` contracts and Max runtime | `python scripts/audit.py` | `0` PASS, `1` FAIL, `2` BLOCKED |
| Run full tests, schemas, privacy, and skill sync | `python scripts/check.py` | `0` PASS, `1` FAIL |

## Execution Steps

### `python -m core.compiler.cli` (`core/compiler/cli.py`)

Root options: `--json`

| Subcommand | Positional | Options |
| :--- | :--- | :--- |
| `compile` | `ir_file` | `--out (default: ./build_harmos)`, `--source`, `--no-build`, `--json` |
| `extract` | `source_file` | `--out*`, `--name`, `--json` |
| `verify-provenance` | `path` | `--ir`, `--source`, `--json` |
| `bench` | - | `--suite (truax/tables/all)`, `--json` |
| `harvest` | - | `--suite (truax/wilson/hexslider)`, `--out*`, `--tolerance (default: 1e-07)`, `--json` |
| `diff` | `cases` | `--suite (truax/wilson/hexslider)`, `--cpp-kernel`, `--kernel-class (wilson/control/dsp/hexslider/truax)`, `--kernel-type-name`, `--json` |
| `doc` | `ir_file` | `--out`, `--author (default: Harmos Meta-Compiler)`, `--json` |

### `python scripts/audit.py` (`scripts/audit.py`)

Root options: `--patcher*`, `--ir`, `--timeout (default: 60)`, `--live-endpoint`, `--json`

### `python scripts/check.py` (`scripts/check.py`)

Root options: `--json`

## Output Contract

Every `--json` invocation emits a single JSON object on stdout with exact keys:
`{"status": str, "command": str, "artifacts": dict, "diagnostics": list[str], "exit_code": int}`.

## References

- `AGENTS.md` — Repository hard rules and canonical commands.
- `core/compiler/cli.py` — Compiler, extractor, oracle diff, and doc CLI.
- `scripts/audit.py` — Live Max runtime and contract auditor.
- `scripts/check.py` — Pre-commit guardrail and AST skill drift check.
- `scripts/generate_skill.py` — Stdlib AST generator for this skill.
