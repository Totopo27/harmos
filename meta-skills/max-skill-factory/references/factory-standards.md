# Max Skill Factory Standards

## Responsibility Isolation

Each generated Max skill must govern exactly one technical domain:
1. **Mathematical / Microtonal Auditors**: Precision arithmetic, octave normalization, harmonic factor matrices, cents conversion.
2. **UI / Geometry Experts**: Vectorial coordinates, Bézier polar arcs, JGraphics / `jsui` rendering pipelines.
3. **Protocol / Architecture Validators**: Inlets/outlets strict typing, memory thread barriers (DSP vs UI), Max contracts schema compliance.

## Structural Validation Checklist

Before saving a new skill:
- Frontmatter YAML parsed and validated without multi-line breaks.
- Description starts with `Trigger: `, is enclosed in double quotes, and is <= 160 characters (max 250).
- All 7 canonical sections present in exact order.
- Imperative instructions addressed to the model, zero tutorial prose.
