# Epistemic Taxonomy & Cross-Stack Provenance

## Epistemic Classification

Every finding in an investigation must be classified into one of four mutually exclusive states:

| State | Definition | Admissible Evidence |
|---|---|---|
| **OBSERVATION** | Direct literal fact read from files, AST, or runtime output. | File path + exact line numbers, commit SHA, symbol address, or verified console packet. |
| **DERIVATION** | Logical conclusion proven by deterministic rules from observations. | Named chain of observations proving the conclusion (e.g., A calls B because AST shows direct invocation at line L). |
| **INFERENCE** | Hypothesis, heuristic match, or circumstantial clue. | Candidate pattern cited; MUST be explicitly labeled `[CANDIDATE]` or `[INFERENCE]`. Never asserted as fact. |
| **UNKNOWN** | Unresolved question, interrupted call boundary, or unobservable runtime state. | Recorded via Unknown Ledger: question, blocked boundary, required authority/environment to resolve. |

## Absence vs Non-Exhaustion Rule

- Incomplete search frontiers, partial AST walks, or truncated grep results DO NOT prove absence.
- Never state "function X does not exist" or "message Y is not handled" unless the complete exhaustive boundary is proven.
- If a boundary cannot be fully enumerated, record it as an **UNKNOWN**.

## Cross-Stack Provenance Boundaries (Max / C++ / TS / OSC)

When investigating cross-stack interactions:

1. **OSC / UDP Messages**:
   - Trace string identifier in sender code (e.g., TS `OscService.ts` or Max `udpreceive`).
   - Cite argument count, types, and byte order from sender AND receiver.
   - If receiver source or DSP processing is unverified, mark dispatch effect as `[INFERENCE]`.
2. **Max Patcher (`.maxpat`)**:
   - Cite box ID (`id: "obj-..."`), class name (`maxclass`), patching coordinates, and inlet/outlet connections.
   - Distinguish visual attributes from functional patchcord routing (`lines` array).
3. **C++ Native Externals (Min-Devkit / Max SDK)**:
   - Cite message/inlet/outlet declarations, attribute registrations, and thread context (main thread vs audio thread `perform`).
   - If audio thread lockless safety cannot be statically verified, classify concurrency behavior as `[UNKNOWN]`.
4. **TypeScript / Web Interface**:
   - Cite component lifecycle, state hooks, and exact event dispatch lines.
   - Distinguish UI presentation from underlying network payload generation.
