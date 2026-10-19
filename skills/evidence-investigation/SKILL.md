---
name: evidence-investigation
description: "Trigger: investigar código, rastrear llamadas, call graph, evidence ledger, diagnosis. Investigación basada en evidencia con estricta procedencia y unknowns."
license: Apache-2.0
metadata:
  author: "gentle-ai"
  version: "1.1"
---

# Evidence Investigation

## Activation Contract

Load this skill when:
- Investigating unfamiliar codebase areas, architecture flows, or cross-boundary calls.
- Diagnosing elusive bugs, unexpected behaviors, or discrepancies across C++, Max, OSC, or TypeScript.
- Tracing strings, following calls, mapping dependencies, or performing forensic code analysis.

Do not load for trivial one-line typos, formatting fixes, or already understood mechanical edits.

## Hard Rules

- **Zero Unattributed Claims**: Every factual claim MUST cite concrete provenance (file path, line numbers, box ID, or commit).
- **Epistemic Classification**: Categorize all findings into `OBSERVATION`, `DERIVATION`, `INFERENCE`, or `UNKNOWN`.
- **Pre-Investigation Framing**: Define target questions and required evidence types BEFORE reading or grepping code.
- **Absence Rule**: Truncated search or incomplete call graphs NEVER prove absence; unreached paths remain `UNKNOWN`.
- **Explicit Unknowns**: When execution flow hits dynamic dispatch, external network, or uninspected binaries, immediately log an explicit Unknown with resolution criteria.

## Decision Gates

| Finding Type | Condition | Action |
| :--- | :--- | :--- |
| Direct syntactic reference | Exact string or symbol match | Record as `OBSERVATION` with path and line number |
| Deterministic AST dependency | Type or call dependency proved | Record as `DERIVATION` with underlying observation chain |
| Dynamic dispatch / OSC route | Event handler or address pattern | Record as `INFERENCE [CANDIDATE]` until traced end-to-end |
| Unverified runtime state | Interrupted or opaque call path | Record in `Unknown Ledger` with required authority |
| Cross-stack boundary | TS ↔ OSC ↔ Max ↔ C++ | Trace sender AND receiver endpoints before declaring verified |

## Execution Steps

1. **Plan Checklist**: Define specific questions to answer and the evidence types required for proof.
2. **Scan Boundaries**: Execute bounded searches (`grep`, `glob`, AST or JSON inspection) from known entry points.
3. **Trace Inward**: Follow references, calls, and message routes step-by-step; cite exact file and line for each.
4. **Capture Unknowns**: Log unresolved questions and the exact authority or test needed to resolve them.
5. **Compile Evidence Ledger**: Assemble observations and derivations into a verified summary, separating candidates and unknowns.

## Output Contract

Return the investigation report structured into three mandatory blocks:
1. **Verified Findings**: Table or list of claims backed by path, line number, and epistemic state (`OBSERVATION` / `DERIVATION`).
2. **Inferences & Candidates**: Suspected connections or heuristic matches labeled with confidence and supporting clues.
3. **Unknowns & Open Questions**: Unresolved gaps, interrupted frontiers, and the exact test or environment needed to resolve them.

## References

- `references/epistemic-taxonomy.md` — Epistemic taxonomy, absence rules, and Max/C++/TS cross-stack conventions.
