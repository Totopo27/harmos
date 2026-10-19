# Max Catalog Matcher Guidelines

## Catalog Lookup Workflow

Before proposing custom external objects or abstraction chains, check:
1. `catalog/max_primitives.json`: Native Max objects providing mathematical operations, MIDI parsing, signal generation, or data dictionaries.
2. `core/schema/max_contracts.json`: Input/output typing specifications for all standard objects.

## Architectural Decision Matrix

- **Native Primitives First**: If `cycle~`, `makenote`, `midiformat`, `dict`, `sprintf`, or `coll` satisfies the requirement, avoid custom code.
- **Max SDK Native Object (Priority Route)**: Implement custom interaction or DSP using Min-Devkit (`ui_operator` with JGraphics, `min.object`, `min.dsp`) or `jsui`.
- **Hybrid View (`jweb`)**: Strictly reserved as an exception when native canvas rendering is conclusively proven unviable.

## Intermediate Representation (IR) Schema

Map chosen primitives and routing to `benchmarks/<proyecto>/<objeto>_ir.json` matching `core/schema/max_object_ir.schema.json`.
