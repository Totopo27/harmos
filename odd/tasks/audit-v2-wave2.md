# Audit v2 — Wave 2 Remaining Items

**Branch Stack**: `feat/audit-v2-w2-01..05` (from `main` @ `57e4598`)
**Chain**: `stacked-to-main` (`<= 400` authored changed lines per PR)
**Delivery**: `auto-chain` (`stacked-to-main`)
**Runner**: `python scripts/check.py` (200 tests baseline) + `ruff check` + `python scripts/bench.py`
**Forecast**: ~1415 authored changed lines across 5 stacked PR slices (<= 315 per PR)

## Specs

- S1: ADR-0001 domain extraction (`5.2`–`5.4`): relocate `microtonal_engine.py` and `truax_kernel.hpp` out of `core/compiler/` into `benchmarks/truax_fm/`, move pilot suite/kernel generators/benchmarks into `benchmarks/suites.py`, and keep `core/` domain-agnostic with ADR-0001 boundary test.
- S2: `ContractEngine` dynamic `poly~` arity and subpatcher contract overlays (`2.5`), plus strict `assertEqual(res.status, "VALID")` in `test_contract_engine.py` (`3.8`).
- S3: Support Max `message` box (`maxclass == "message"`) contract resolution in `TypedPatch` and `scripts/audit.py`, and insert `"0"` message box between `carrier_env` (`"envelope_completed_bang"`) and `thispoly~` (`"mute_or_voice_messages"`) in `SCVoiceCompiler.compile_fm_voice` (`1.4`).
- S4: Replace all raw integer `patch.connect(...)` calls in `core/compiler/sc_voice_compiler.py` with `patch.connect_semantic(...)` (`1.3`), and remove hardcoded `diesisRosa` filenames/scripts from `sc_voice_compiler.py` (`5.5`, placing `DIESIS_ROSA_CONTROL_IR` in `benchmarks/suites.py`).
- S5: Add E2E SC -> IR -> C++/Patcher -> Audit integration test (`3.7`).
- S6: Isolate POSIX process groups (`start_new_session` + `os.killpg`) in `scripts/audit.py` (`4.9`) and add filesystem tests for `resolve_max_executable()` in `tests/test_audit.py` (`3.2`).
- S7: Alternate `target_fn` / `reference_fn` call order across even/odd iterations in `core/compiler/benchmark.py` (`4.11`) with deterministic order test.
- S8: Replace `LICENSE` with full official Apache License Version 2.0 text (`5.1`).
- S9: Add `.github/PULL_REQUEST_TEMPLATE.md` and `.github/ISSUE_TEMPLATE/{bug_report.md,feature_request.md}` (`5.17`).
- S10: Write Spanish ADRs `0012`–`0015` for dynamic arity, generic UI lowering, C++ sanitization, and fail-closed guardrail (`5.11`).
- S11: Sync `HERRAMIENTAS_Y_SKILLS_MAX.md` §8 (`5.13`), `RESUMEN_ARQUITECTURA_REFACTORIZADA.md` (`5.14`), `meta-skills/max-transpiler-scout/SKILL.md` (`5.15`), and `skills/maxpylang/SKILL.md` (`5.16`).
- S12: Reconcile `odd/tasks/framework-optimization.md` (`5.10`) and close `odd/tasks/audit-v2-wave2.md`.

## Tasks

- [x] T1 (S1 partial: `5.2`, `5.3`, `5.4a`) [inline -> `feat/audit-v2-w2-01-domain-separation`]: Move `microtonal_engine.py` & `truax_kernel.hpp` to `benchmarks/truax_fm/`, extract CLI/headless pilot logic to `benchmarks/suites.py`, update Ruff CI/config. Verified: ruff/check.py PASS, bench.py SHIP.
- [ ] T2 (S2–S5: `1.3`, `1.4`, `2.5`, `3.7`, `3.8`, `5.5`) [inline -> `feat/audit-v2-w2-02-poly-and-sc-voice`]: Dynamic `poly~`, `message` contract resolution, `SCVoiceCompiler` semantic wiring & domain decoupling, E2E SC test.
- [ ] T3 (S1 finish `5.4b`, S6, S7: `3.2`, `4.9`, `4.11`) [inline -> `feat/audit-v2-w2-03-runtime-and-bench`]: Extract pilot benchmarks out of `benchmark.py`, ADR-0001 boundary test, POSIX `killpg`, `resolve_max_executable` disk tests, benchmark order alternation.
- [ ] T4 (S8–S9: `5.1`, `5.17`) [inline -> `chore/audit-v2-w2-04-license-and-templates`]: Full Apache-2.0 `LICENSE` and GitHub PR/Issue templates.
- [ ] T5 (S10–S12: `5.10`, `5.11`, `5.13`–`5.16`) [inline -> `chore/audit-v2-w2-05-adrs-and-skills-sync`]: ADRs 0012–0015, docs/skills sync, ODD reconciliation.

## Log

- L1: "vamos con ello" — User authorized Wave 2 execution across 5 stacked PR slices (<= 400 changed lines each) covering all remaining `harmos-audit-report.md` items.
