# Trustworthy contract validation
Objective: make missing evidence explicit and reject invalid connections without guessing ports.
Branch: feat/python-version-matrix; baseline: 205f29a0c74f99f31967aaf4089e133358c42cdd. Delivery: ask-on-risk, forecast 650 authored changed lines. Runner: Python unittest.

## Specs

- **S1 — Strict default.** User decision: "Estricto por defecto (Recommended)". Distinguish valid, invalid and unverifiable connections. Missing contracts must not silently approve connections. Preserve the public `(bool, reason)` compatibility shape, but only verified-valid connections return true by default. Any explicit allowance of unverifiable connections remains distinguishable from proof.
- **S2 — No guessed ports.** Remove the incorrect hardcoded MIDI fallback and the unresolved-role fallback to inlet zero. Resolve declared names and correct catalog aliases; reject ambiguous or unknown roles, negative indices and known out-of-range ports. Preserve existing valid connection behavior.
- **S3 — Evidence-preserving integration.** Preserve semantic port names and original type evidence. Support declared union types consistently in connection validation and automatic adaptation. Supply the newly generated object's contract from its IR when creating its test patch; do not globally exempt unknown objects. Rejected operations must not change patch output.
- **S4 — Honest checks.** Separate JSON syntax, dependency-free contract structure validation, and live runtime audit. Reuse catalog validation in loading and the guardrail; do not claim general Draft-07 or full IR validation. Static missing evidence must never become a static PASS. Keep live Max execution mandatory for patch certification.
- **S5 — Scope and verification.** User request: "vamos con todas las optimizaciones que sugieres hacer y ya luego pensamos en esta idea entonces". Implement the existing-engine safeguards first; defer the XML harvester, MCP server, archetypes and extraction/version provenance until that idea is reconsidered. Preserve the pre-existing CI edit. Verify through the engine, TypedPatch, CLI patch generation, auditor and guardrail public seams, with independent verification of shared-contract changes.

## Tasks

- [x] **T1** — S1-S3: strict tri-state engine and emitter/auditor integration, focused regression tests and docs. Route: inline; no writer trigger. Risk: item 3 (shared public contract behavior).
- [x] **T2** — S4: dependency-free catalog shape checks and accurate guardrail reporting, tests and docs. Route: inline; same writer owns the shared engine. Risk: item 3 (catalog consumers).
- [x] **T3** — S1-S5: baseline differential checks, guardrail, live audit, independent verification and applicable native review. Route: inline coordination; long checks use per-action workers, independent verification required by item 3.

## Log

### L1 — Original request

> vamos con todas las optimizaciones que sugieres hacer y ya luego pensamos en esta idea entonces

### L2 — Clarification and accepted policy

The user asked:

> Puedes ampliar la información, detallar más para tratar de entender qué es lo que me dices?

> pero no entiendo, de qué catálogo hablas?

Explained that the existing catalog is `core/schema/max_contracts.json`, not the installed Max XML documentation. The user selected:

> Estricto por defecto (Recommended)

The presented test seams were the engine public methods, TypedPatch connections, auditor and check.py. Tests do not substitute for a real Max execution.

### L3 — Initial evidence and boundaries

- Read-only mapping found guessed MIDI indices, unknown-role fallback zero, permissive missing-contract/out-of-range handling and negative-index acceptance in `core/compiler/contract_engine.py`.
- `TypedPatch` and the live auditor share that engine; CLI-generated objects may lack catalog entries.
- `scripts/check.py` currently parses JSON but does not perform general JSON Schema validation or launch the live audit.
- No new dependency is required for narrow contract structure checks. Full Draft-07/IR validation is explicitly not claimed.
- Catalog corrections change the provenance hash; existing emitted packages may need regeneration.
- Existing uncommitted `.github/workflows/ci.yml` is outside this feature and must remain untouched.
- RDD mode is on by default; candidate consent is separate. No review has started.
- Engram mirror: pending initial synchronization.
- Delivery forecast exceeds the advisory 400-line threshold; resolve chain strategy before a work-unit commit if still applicable. No remote operations are authorized.
