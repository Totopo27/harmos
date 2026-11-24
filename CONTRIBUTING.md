# Contributing to Harmos

Harmos is governed by test-driven development, zero-hardcoding contract matching for Cycling '74 Max MSP, and strict verification boundaries. Read this guide before opening a branch or pull request.

---

## Core Invariants

1. **Zero Hardcoding**: Never hardcode physical inlet or outlet indices when wiring patchers. Declare and resolve object signatures via [`core/schema/max_contracts.json`](./core/schema/max_contracts.json) and `ContractEngine` / `TypedPatch.connect_semantic()`.
2. **Live Runtime Audit Mandatory**: Never certify a `.maxpat` or external through static checks alone. Execute `python scripts/audit.py --patcher <path.maxpat>`. If Max is absent on the host, report `BLOCKED (RUNTIME_UNAVAILABLE)` — never `PASS`. See [`docs/ORACULO_LIMITES.md`](./docs/ORACULO_LIMITES.md).
3. **Privacy & Security**: Never commit absolute host paths, tokens/secrets, or local execution scripts (`*.ps1`, `*.bat`, `*.cmd`). `scripts/check.py` enforces this on both tracked and untracked-non-ignored files.
4. **Domain Separation**: Harmos is a domain-agnostic meta-compiler. Stress-test suites (`benchmarks/`, `packages/`) validate the engine and must not leak domain assumptions into the core architecture (see [`GLOSSARY.md`](./GLOSSARY.md) and [`docs/adr/0001-separacion-motor-y-benchmarks.md`](./docs/adr/0001-separacion-motor-y-benchmarks.md)).

---

## Local Setup

- **Python 3.11+** (the core test suite has zero runtime dependencies outside the standard library).
- **Development dependencies** (for linting and coverage matching CI):

```bash
python -m pip install --group dev
```

- **Optional toolchains**:
  - A C++17 compiler (`g++`, `clang++`, or MSVC `cl`) for `cpp_headless_runner.py` tests and semantic diff checks.
  - CMake 3.24+ and `c74support/min-devkit` (`git submodule update --init --recursive`) for building native `.mxe64` / `.mxo` externals.
  - Cycling '74 Max 8.x or 9.x for live runtime audits (`scripts/audit.py`).

---

## Development Workflow (ODD)

1. **Single-context documentation**: Keep canonical architectural terms in [`GLOSSARY.md`](./GLOSSARY.md) and record significant architectural decisions under [`docs/adr/`](./docs/adr/) (see [`docs/agents/domain.md`](./docs/agents/domain.md)).
2. **Feature tracking**: Multi-slice work is tracked via Organic Driven Development (ODD) specs (`S#`), tasks (`T#`), and log entries (`L#`) in `odd/tasks/<feature>.md`.
3. **TDD & contracts**: Reproduce failures with a failing test before fixing (`python -m unittest discover tests`), and update `max_contracts.json` + contract tests when changing object port rules or compound types.
4. **Conventional Commits**: Use clean Conventional Commit messages (`feat(...)`, `fix(...)`, `ci(...)`, `docs(...)`, `test(...)`) in atomic slices, keeping tests and docs alongside the behavior they verify. Do not add AI attribution or `Co-Authored-By` trailers.

---

## Pre-Commit Checklist

Run these checks from the repository root before every commit or PR:

```bash
# 1. Mandatory guardrail (full unittest suite + JSON/contract structure + leak scan)
python scripts/check.py

# 2. Static lint check (matches CI config in pyproject.toml)
ruff check core/ scripts/ tests/

# 3. Performance budget check (host Python simulation: SHIP / NO_SHIP)
python scripts/bench.py

# 4. Live runtime audit whenever patchers or externals are added or changed
python scripts/audit.py --patcher <path.maxpat>
```
