# Harmos Node-for-Max Live Receiver (`templates/node_script_wrapper/`)

Zero-dependency loopback (`ws://127.0.0.1:7400`) WebSocket + JSON-RPC 2.0 receiver for Cycling '74 Max 9 on Windows and macOS. Pairs directly with [`core/compiler/live_bridge.py`](../../core/compiler/live_bridge.py) and [`scripts/audit.py`](../../scripts/audit.py) without installing `npm` packages.

## Files

- `harmos_live_receiver.js` — Node.js built-in (`http` + `crypto`) RFC 6455 WebSocket server for `[node.script]`. Fails closed (`loaded: false`, `BLOCKED`) outside Max when `max-api` is unavailable.
- `harmos_live_patch.js` — Pure ES5 companion for Max `[js]` / `[v8]` handling `harmos/inspect_state` (`buffer~`, `dict`), `harmos/connect`, and `harmos/audit_patcher` (`bogus` object detection).

## Max Patch Wiring

Place these objects inside your host Max 9 patcher (kept in the same folder or Max search path):

```text
[message script start]
        │
        ▼
[node.script harmos_live_receiver.js @autostart 1]
        │                          ▲
        │ (harmos_request <json>)  │ (harmos_reply <json>)
        ▼                          │
[js harmos_live_patch.js] ─────────┘
```

Wire the left outlet of `[node.script]` to the inlet of `[js harmos_live_patch.js]`, and the outlet of `[js harmos_live_patch.js]` back into the inlet of `[node.script]`.

## Usage with Harmos

Run the contract-gated live audit against the running patcher:

```bash
python scripts/audit.py --patcher path/to/your_patch.maxpat --live-endpoint ws://127.0.0.1:7400 --json
```

## Epistemic Scope & Fail-Closed Guarantee

- Running `node templates/node_script_wrapper/harmos_live_receiver.js` outside Max responds to `harmos/ping`, but returns `loaded: false` on `harmos/audit_patcher`, causing `scripts/audit.py` to emit `BLOCKED` (`exit_code: 2`), never `PASS`.
- All wire protocol limits, contract gates, and epistemic limits from [`docs/ORACULO_LIMITES.md`](../../docs/ORACULO_LIMITES.md) still apply.
- This Node receiver implements the same loopback JSON-RPC contract that a future native C++ `Min-DevKit` `.mxe64` external can implement as a drop-in replacement.
