# Max Project Scout Methodology

## Language Agnostic Architecture Analysis

When auditing a foreign codebase (Rust, C++, TypeScript, Python, C#, WebAssembly):
1. **Entry Points**: Identify core entry points, lifecycle hooks, and dependency descriptors (`package.json`, `Cargo.toml`, `CMakeLists.txt`, `requirements.txt`).
2. **Logic Isolation**: Separate mathematical calculations, state management, and DSP from user interface rendering.
3. **UI Assessment**: Document all interactive capabilities, canvas viewports, custom widgets, and context menus.

## Native Max SDK Priority Hierarchy

1. **Tier 1 (Mandatory Priority)**: Implement as a native Max object via C++ Min-Devkit (`min.object`, `min.dsp`, `ui_operator` with JGraphics) or vector scripting (`jsui` with `mgraphics`).
2. **Tier 2 (Prototyping / Mass Generation)**: MaxPyLang or Node for Max (`node.script`).
3. **Tier 3 (Constrained Exception)**: `jweb` embedded view — only permitted after empirical proof that native canvas implementation is technically impossible without discarding core functionality.

## Comparative Parity Testing

Establish a local harness (e.g. localhost server or native CLI build) to run the source project concurrently with the Max patcher to verify 1:1 acoustic and visual output.
