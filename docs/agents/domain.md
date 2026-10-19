# Domain Docs

This repository uses a **single-context** domain doc layout:

- **Glossary**: `GLOSSARY.md` at the repository root holds the shared domain terminology.
- **Architectural Decision Records**: `docs/adr/` holds the system-wide architecture decisions.

## Consumer Rules

1. Any skill creating, renaming, or defining concepts must check and update `GLOSSARY.md`.
2. Architecture decisions that are hard to reverse, surprising without context, or result from real trade-offs must be recorded in `docs/adr/`.
3. Never conflate core Harmos compiler concepts with downstream benchmark pilot cases (see `docs/adr/0001-separacion-motor-y-benchmarks.md`).
