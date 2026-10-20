# Harmos — Guidelines for Coding Agents

This repository is governed by rigorous engineering practices, test-driven development (TDD), and zero-hardcoding contract matching for Cycling '74 Max MSP.

## Hard Rules

- **Zero Hardcoding**: Never assume or hardcode inlet/outlet numbers. Always validate and resolve types via `core/schema/max_contracts.json` or `core/compiler/contract_engine.py`.
- **Live Runtime Audit Mandatory**: Never certify patches or packages through static inspection alone. All audits must execute `python scripts/audit.py --patcher <path.maxpat>`. If Max runtime is not installed or available on the host, audit status must be reported as `BLOCKED (RUNTIME_UNAVAILABLE)`, never `PASS`.
- **Privacy & Security**: Never commit absolute host paths or local execution scripts (`*.ps1`). Always run `python scripts/check.py` before any commit or push.
- **Domain Separation**: Harmos is an agnostic meta-compiler framework. Downstream suites (e.g. Wilson tuning, TET circles) are benchmarks for stress-testing, not the core framework (see `GLOSSARY.md` and `docs/adr/0001-separacion-motor-y-benchmarks.md`).

## Canonical Commands

- **Run Guardrail (Tests + Schemas + Privacy)**: `python scripts/check.py`
- **Run Tests Only**: `python -m unittest discover tests`
- **Run Live Runtime Audit**: `python scripts/audit.py --patcher <path.maxpat>`
- **Compile IR to Max Package**: `python -m core.compiler.cli <path.ir.json> --out <output_dir>`

## Agent skills

### Issue tracker

Issues are tracked using **GitHub Issues** at `Totopo27/harmos` via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Domain docs

Harmos uses a **single-context** layout (`GLOSSARY.md` at root and `docs/adr/`). See `docs/agents/domain.md`.
