## Summary

<!-- Describe what changed and why. Reference the related issue or ODD spec (`S#`). -->

## Chain Context

<!-- Keep or delete this section if this is a standalone PR <= 400 changed lines. -->
| Order | PR | Scope | Changed Lines |
| :--- | :--- | :--- | :--- |
| 1 | #... | ... | ... |

## Verification

- Guardrail (`python scripts/check.py`): <!-- Paste observed PASS summary + test count -->
- Static lint (`ruff check core/ scripts/ benchmarks/ tests/`): <!-- Paste observed result -->
- Live runtime audit (`python scripts/audit.py --patcher <path.maxpat>`): <!-- `PASS` / `BLOCKED (RUNTIME_UNAVAILABLE)` / `N/A` (static-only change) -->

## Risk

<!-- Record ODD risk assessment (`Risk: none` or `Risk: item N (reason)`). -->
