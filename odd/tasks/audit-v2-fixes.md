# Audit v2 — Post-Optimization Fixes

**Branch**: `audit-v2-fixes` (from `main` @ `8a19f78`)
**Chain**: feature-branch-chain (base: `chore/framework-optimization-base` @ `8a19f78`)
**Delivery**: `ask-on-risk`
**Runner**: `python -m unittest discover tests` (183 tests baseline)
**Forecast**: ~600 authored changed lines across 5 phases

## Specs

- S1: Add `Union` to `typing` import in `typed_patch.py`; remove unused `IncompatibleConnectionError` import — user approved audit report Phase 1.1
- S2: Fix clang/MSVC compiler detection in `cpp_headless_runner.py` — strict stem match — Phase 1.2
- S3: Filter JS/TS reserved keywords from `ast_extractor.py` method extraction; restrict attribute scan to class header — Phase 1.5
- S4: Add `.ts`, `.js`, `.tsx`, `.jsx` to `TEXT_EXTENSIONS` in `provenance.py` — Phase 1.6
- S5: Fix `sample_operator<N,N>` arity mismatch in `cpp_generator.py`; handle `symbol`/`bool` attribute types — Phase 1.7
- S6: Update `max_contracts.json` signal-only inlets to `signal/float` for `*~`, `+~`, `-~`, `phasor~`, `tri~`, `saw~`, `rect~`, `lores~` — Phase 2.1
- S7: Add `inlet`, `outlet`, `inlet~`, `outlet~` contracts to `max_contracts.json` — Phase 2.2
- S8: Add missing active-patcher object contracts (`loadbang`, `midiout`, `sprintf` etc.) — Phase 2.3
- S9: Update IR schema `max_object_ir.schema.json` to allow compound types — Phase 2.4
- S10: Add `escape_xml` quote escaping in `maxref_generator.py` — Phase 3.6
- S11: Fix `_compute_statistical_verdict` empty-run crash in `benchmark.py` — Phase 3.9
- S12: Add `Union` annotation introspection test for `typed_patch.py` — Phase 3.1
- S13: Add compilation failure and timeout negative tests for `cpp_headless_runner.py` — Phase 3.4
- S14: Fix global registry leak in `test_cpp_headless_runner.py` — Phase 3.5
- S15: Create `pyproject.toml` with tool configs; fix CI `|| true`, pin deps, deduplicate tests — Phase 4
- S16: Expand `check.py` secret patterns and scan untracked files — Phase 4.6-4.7
- S17: Fix `audit.py` macOS log resolution version matching — Phase 4.8
- S18: Update `README.md` tree, pipeline diagram, CLI examples — Phase 5.6-5.8
- S19: Create `CONTRIBUTING.md` — Phase 5.9
- S20: Expand `GLOSSARY.md` with Tri-State, Dynamic Arity, SHIP/NO_SHIP — Phase 5.12

## Tasks

- [x] T1 (S1, S3-S5; S2 moved to T4) [inline]: Phase 1 compiler bug fixes + `ContractEngine` SHA-256 cache fix — Commit: `b2dd709` (`feat/audit-v2-01-compiler`, replaces draft `139597e` + `1718dad`)
- [x] T2 (S6-S9) [inline]: Phase 2 contract & schema hardening + same-mtime cache test — Commit: `caedcab` (`feat/audit-v2-02-contracts`)
- [x] T3 (S10-S12; S13-S14 moved to T4) [inline]: Phase 3 test suite hardening & benchmark GC guard — Commit: `b2dd709` (`feat/audit-v2-01-compiler`)
- [x] T4 (S2, S13-S17) [inline]: Phase 4 CI/CD, headless runner hardening & scripts — Commit: `7e7fc73` (`feat/audit-v2-03-ci-guardrail`)
- [x] T5 (S18-S20) [inline]: Phase 5 docs & governance — Commit: `feat/audit-v2-04-docs` (this slice)

## Log

- L1: "ve una por una resolviendo absolutamente todas las fases con los puntos de mejora que encontraste" — user approved audit-v2 report artifact with 5 phases, ~78 findings
- L2: Feature document created 2026-11-23. Starting Phase 1 (compiler bugs).
- L3: Closed 2026-11-23 across T1–T5 (`139597e`, `9fe8d2a`, `f87c616`, `1ec5e22`, `c17a2f1`). Each slice passed `scripts/check.py` (`PASS`); Ruff passed on T4. Deferred non-S1..S20 audit items (ADR-0001 domain extraction, full Apache-2.0 LICENSE text, `sc_voice_compiler.py` refactoring, `poly~` dynamic arity) remain open outside this feature slice.
- L4: Independent verifier flagged blockers on S3 (`ast_extractor.py`: constructor excluded from header boundary & primary fallback unguarded) and S5 (`cpp_generator.py`: missing `<string>`, invalid Min `attribute<string>`/unquoted `symbol`/`bool` defaults, and 1-arg `sample_operator`). Fixed in `1718dad` with tests in `tests/test_ast_extractor.py` and `tests/test_cpp_generator.py`; Ruff clean and `scripts/check.py` `PASS`.
- L5: Split `audit-v2-fixes` into a 4-PR Feature Branch Chain over `chore/framework-optimization-base` (`8a19f78`): `feat/audit-v2-01-compiler` (`b2dd709`, incl. `ContractEngine` SHA-256 cache fix) -> `feat/audit-v2-02-contracts` (`caedcab`, incl. same-mtime cache test) -> `feat/audit-v2-03-ci-guardrail` (`7e7fc73`, incl. `S2`/`S13`/`S14` `cpp_headless_runner`) -> `feat/audit-v2-04-docs` (this slice). All 4 slices fit under the 400-line review budget with green `scripts/check.py` gates.
