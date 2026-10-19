# MaxPyLang M4L and Patching DSL Guide

## Overview

`maxpylang` is a Python package (developed by Barnard College / Columbia University) for programmatic creation, manipulation, and compilation of Max MSP (`.maxpat`) and Max for Live (`.amxd`) devices.

## Installation

```bash
pip install maxpylang
```

## Layout Constants and Geometry Rules

To generate visually legible and collision-free patchers, follow standard spacing offsets:

- `Y_STEP = 40`: Vertical distance between sequentially chained objects.
- `SECTION_GAP = 80`: Vertical margin separating distinct functional blocks.
- `COL_WIDTH = 160`: Horizontal distance between parallel signal chains (e.g., voices, LFOs).
- **Flow Direction**: Top-to-bottom signal flow (increasing $y$ coordinates).
- **Comments**: Place `comment` boxes 20 pixels above the target object.

## Max for Live (`.amxd`) Device Compilation

When calling `patch.save(path, device_type=...)`, `maxpylang` configures specific routing and metadata:

| `device_type` | Audio / Signal In | Audio / Signal Out | Live Track Type | Save Call |
| :--- | :--- | :--- | :--- | :--- |
| `"instrument"` | `notein` / `midiparse` | `plugout~` | MIDI Track | `patch.save("synth.amxd", device_type="instrument")` |
| `"audio_effect"` | `plugin~` | `plugout~` | Audio Track | `patch.save("fx.amxd", device_type="audio_effect")` |
| `"midi_effect"` | `midiin` → `midiparse` | `midiformat` → `midiout` | MIDI Track | `patch.save("midi.amxd", device_type="midi_effect")` |

## Critical Safeguards for M4L

1. **Safety Limiter**: Always insert `clip~ -1. 1.` immediately before `plugout~` to protect speakers and ears from digital blowups.
2. **Master Gain Delegation**: Ableton Live manages channel mixer gain; do not insert redundant master gain faders before `plugout~`.
3. **Automatable Controls**: Use `live.dial`, `live.slider`, or `live.numbox` so controls are exposed to Live's device view, automations, and push controllers.
4. **Stereo Continuity**: `plugout~` has 2 audio inlets (left and right). Both channels must be connected.
