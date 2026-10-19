# Max Patch Validator Contracts Reference

## Zero Hardcoding Contract

Every cable and connection must conform to `core/schema/max_contracts.json`. Never guess inlet or outlet indexes.

### Common Typed Inlets

#### `midiformat`
- **Inlet 0**: Pitch (`int` base note number 0-127).
- **Inlet 1**: Velocity (`int` 0-127).
- **Inlet 2**: Polyphonic Aftertouch (not MIDI channel).
- **Inlet 3**: Control Change (CC value).
- **Inlet 4**: Program Change.
- **Inlet 5**: Pitch Bend (`int` 0 to 16383, center 8192).
- **Inlet 6**: MIDI Channel (`int` 1-16).

Never connect composite lists directly to an inlet expecting a single integer. Always place an intermediate `unpack` object.

### Max Console Diagnostic Strings

- Red console notifications (`can't connect`, `doesn't match type`, `no such object`) trigger immediate gate rejection.
- Clean console state requires 0 red error rows during patcher load and message triggering.
