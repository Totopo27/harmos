# Max/MSP MCP Patching Mechanics Reference

## Detailed Positioning Protocol

To avoid visual overlaps and tangled patchcords when automating patch creation via MCP:
- Always call `get_avoid_rect_position()` to read existing object boundaries `[left, top, right, bottom]`.
- Vertical placement for new rows: `y = bottom + 50`.
- Horizontal placement in current row: `x = prev_right + 25`.

## JSON Numeric Typing Gotchas

Standard JSON serializers prune trailing zeros (`440.0` -> `440`). Max interprets unpointed numbers as integers (`int`), breaking MSP and DSP mathematical objects.
- **Pass float strings**: Use `["0", "127", "0", "25."]` instead of bare numbers when decimal precision is needed.
- **Explicit type flags**: In `unpack`, pass typed atom strings: `["f", "f", "f"]`.
- **Affected objects**: `+`, `-`, `*`, `/`, `%`, `pow`, `scale`, `pack`, `pak`, `unpack`.

## Trigger Order and Audio Summing

- **Trigger (`[t]`) Right-to-Left**: In Max, outlets of a trigger object fire strictly from right to left in discrete logical time. For example, `[t b f]` fires float from the right outlet first, then bang from the left outlet second.
- **MSP Inlets Auto-Summing**: Inlets on MSP audio objects (`~`) automatically sum multiple incoming audio patchlines. Never insert `+~` solely to merge two audio signals.
- **Feedback Loops**: In delay networks, route feedback signals directly into `tapin~` without intermediate mixing stages.

## Interface Controls (`dial` vs `live.dial`)

- Standard Max patches prefer `dial` over `live.dial`:
  - Normalized float range (0.0 to 1.0): `['@size', 1, '@floatoutput', 1]`
  - Bipolar float range (-1.0 to 1.0): `['@min', -1, '@size', 2, '@floatoutput', 1, '@mode', 6]`
  - MIDI integer range (0 to 127): `['@size', 127]`
  - `@size` limit: If size exceeds 255, dial UI degrades; use `flonum` or `number` instead.

## Data Persistence (`coll`)

- Always instantiate `coll` with `@embed 1` so stored tables persist when saving the patcher.

## Comment Box Protection & Forensic Log Audit

- `comment` objects are visual annotations and have NO functional inlets. Connecting patchlines to `comment` throws `error connecting outlet X to comment inlet Y`.
- Audit `Max.log` at `%APPDATA%\Cycling '74\Max X\Logs` post-execution for any warning or error strings (`error`, `warning`, `cannot`, `fail`).
