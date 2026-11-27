"""Tests for the stdlib ContractEngine-gated WebSocket live bridge and audit --live-endpoint."""
import base64
import contextlib
import hashlib
import io
import json
import socket
import struct
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.compiler.cli import compile_ir
from core.compiler.contract_engine import ContractEngine, IncompatibleConnectionError
from core.compiler.live_bridge import (
    LiveBridgeError,
    MaxLiveBridge,
    StdlibWebSocketClient,
    parse_ws_endpoint,
)
from scripts import audit

_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def _recv_exact(sock: socket.socket, count: int) -> bytes:
    buf = bytearray()
    while len(buf) < count:
        chunk = sock.recv(count - len(buf))
        if not chunk:
            raise EOFError("Socket closed while reading frame")
        buf.extend(chunk)
    return bytes(buf)


def _read_client_frame(sock: socket.socket) -> Tuple[int, bytes]:
    b1, b2 = _recv_exact(sock, 2)
    opcode = b1 & 0x0F
    masked = bool(b2 & 0x80)
    length = b2 & 0x7F
    if length == 126:
        (length,) = struct.unpack("!H", _recv_exact(sock, 2))
    elif length == 127:
        (length,) = struct.unpack("!Q", _recv_exact(sock, 8))
    mask_key = _recv_exact(sock, 4) if masked else b""
    payload = bytearray(_recv_exact(sock, length))
    if masked:
        for i in range(length):
            payload[i] ^= mask_key[i % 4]
    return opcode, bytes(payload)


def _send_server_frame(sock: socket.socket, opcode: int, payload: bytes, *, fin: bool = True) -> None:
    first = (0x80 if fin else 0x00) | (opcode & 0x0F)
    length = len(payload)
    if length < 126:
        header = bytes([first, length])
    elif length < 65536:
        header = struct.pack("!BBH", first, 126, length)
    else:
        header = struct.pack("!BBQ", first, 127, length)
    sock.sendall(header + payload)


class _LoopbackWebSocketServer:
    """Minimal RFC 6455 loopback server for deterministic bridge tests."""

    def __init__(
        self,
        handler: Optional[Callable[[str, Dict[str, Any]], Dict[str, Any]]] = None,
        *,
        bad_accept: bool = False,
        send_ping_before_reply: bool = False,
        fragment_response: bool = False,
    ):
        self.handler = handler or (lambda method, params: {"ok": True})
        self.bad_accept = bad_accept
        self.send_ping_before_reply = send_ping_before_reply
        self.fragment_response = fragment_response
        self.connections_count = 0
        self.requests: List[Tuple[str, Dict[str, Any]]] = []
        self.pongs_received: List[bytes] = []
        self.pong_event = threading.Event()
        self._stop = threading.Event()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(8)
        self._sock.settimeout(0.1)
        self.port = self._sock.getsockname()[1]
        self.url = f"ws://127.0.0.1:{self.port}"
        self._thread = threading.Thread(target=self._serve, daemon=True)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self._stop.set()
        try:
            self._sock.close()
        except OSError:
            pass
        self._thread.join(timeout=2.0)

    def _serve(self) -> None:
        while not self._stop.is_set():
            try:
                conn, _ = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self.connections_count += 1
            threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()

    def _handle_client(self, conn: socket.socket) -> None:
        conn.settimeout(2.0)
        try:
            raw_req = b""
            while b"\r\n\r\n" not in raw_req:
                chunk = conn.recv(4096)
                if not chunk:
                    return
                raw_req += chunk
            headers: Dict[str, str] = {}
            for line in raw_req.decode("utf-8", errors="replace").split("\r\n")[1:]:
                if ":" in line:
                    k, v = line.split(":", 1)
                    headers[k.strip().lower()] = v.strip()

            ws_key = headers.get("sec-websocket-key", "")
            accept_raw = hashlib.sha1((ws_key + _WS_GUID).encode("ascii")).digest()
            accept_val = "INVALID_ACCEPT==" if self.bad_accept else base64.b64encode(accept_raw).decode("ascii")
            response = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept_val}\r\n\r\n"
            )
            conn.sendall(response.encode("ascii"))
            if self.bad_accept:
                return

            while not self._stop.is_set():
                try:
                    opcode, payload = _read_client_frame(conn)
                except (EOFError, OSError, socket.timeout):
                    break

                if opcode == 0x8:  # CLOSE
                    _send_server_frame(conn, 0x8, b"")
                    break
                if opcode == 0x9:  # PING
                    _send_server_frame(conn, 0xA, payload)
                    continue
                if opcode == 0xA:  # PONG
                    self.pongs_received.append(payload)
                    self.pong_event.set()
                    continue
                if opcode != 0x1:
                    continue

                req = json.loads(payload.decode("utf-8"))
                method = req.get("method", "")
                params = req.get("params") or {}
                self.requests.append((method, params))
                result = self.handler(method, params)
                reply = json.dumps({"jsonrpc": "2.0", "id": req.get("id"), "result": result}).encode("utf-8")

                if self.send_ping_before_reply:
                    _send_server_frame(conn, 0x9, b"hb")

                if self.fragment_response and len(reply) > 10:
                    mid = len(reply) // 2
                    _send_server_frame(conn, 0x1, reply[:mid], fin=False)
                    _send_server_frame(conn, 0x0, reply[mid:], fin=True)
                else:
                    _send_server_frame(conn, 0x1, reply, fin=True)
        finally:
            try:
                conn.close()
            except OSError:
                pass


def _write_patcher(path: Path, boxes: List[Dict[str, Any]], lines: List[Dict[str, Any]]) -> Path:
    path.write_text(json.dumps({"patcher": {"boxes": boxes, "lines": lines}}), encoding="utf-8")
    return path


def _box(box_id: str, text: str, maxclass: str = "newobj") -> Dict[str, Any]:
    return {"box": {"id": box_id, "maxclass": maxclass, "text": text}}


def _line(src_id: str, src_out: int, dst_id: str, dst_in: int) -> Dict[str, Any]:
    return {"patchline": {"source": [src_id, src_out], "destination": [dst_id, dst_in]}}


class TestLiveBridgeTransportAndContracts(unittest.TestCase):
    def test_parse_ws_endpoint_allows_only_loopback_ws(self):
        self.assertEqual(parse_ws_endpoint("ws://127.0.0.1:7400"), ("127.0.0.1", 7400, "/"))
        self.assertEqual(parse_ws_endpoint("ws://localhost:8123/max"), ("localhost", 8123, "/max"))
        self.assertEqual(parse_ws_endpoint("ws://127.0.0.1"), ("127.0.0.1", 7400, "/"))

        for bad in (
            "http://127.0.0.1:7400",
            "wss://127.0.0.1:7400",
            "file:///tmp/x",
            "ws://example.com:7400",
            "ws://192.168.1.5:7400",
            "ws://:7400",
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(LiveBridgeError):
                    parse_ws_endpoint(bad)

    def test_websocket_client_roundtrip_fragmentation_ping_and_bad_accept(self):
        long_echo = "x" * 300
        with _LoopbackWebSocketServer(
            handler=lambda m, p: {"echo": long_echo, "method": m},
            send_ping_before_reply=True,
            fragment_response=True,
        ) as srv:
            with StdlibWebSocketClient(srv.url, timeout=3.0) as ws:
                req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "harmos/ping", "params": {"pad": long_echo}})
                ws.send_text(req)
                resp = json.loads(ws.recv_text())
            self.assertEqual(resp["result"]["echo"], long_echo)
            self.assertTrue(srv.pong_event.wait(timeout=2.0), "Server did not observe PONG in time")
            self.assertIn(b"hb", srv.pongs_received)

        with _LoopbackWebSocketServer(bad_accept=True) as bad_srv:
            with self.assertRaises(LiveBridgeError):
                with StdlibWebSocketClient(bad_srv.url, timeout=2.0):
                    pass

    def test_bridge_gates_connect_and_inspect_before_sending(self):
        with _LoopbackWebSocketServer(
            handler=lambda method, params: {"connected": True, "params": params}
            if method == "harmos/connect"
            else {"exists": True, "name": params.get("name"), "kind": params.get("kind")}
        ) as srv:
            with MaxLiveBridge(srv.url, timeout=3.0) as bridge:
                ok_res = bridge.connect_objects(
                    patch_id="p1",
                    src_id="obj-1",
                    src_obj="cycle~",
                    src_outlet=0,
                    dst_id="obj-2",
                    dst_obj="ezdac~",
                    dst_inlet=0,
                )
                self.assertTrue(ok_res["connected"])
                self.assertEqual(len(srv.requests), 1)
                self.assertEqual(srv.requests[0][0], "harmos/connect")

                with self.assertRaises(IncompatibleConnectionError):
                    bridge.connect_objects(
                        patch_id="p1",
                        src_id="obj-1",
                        src_obj="cycle~",
                        src_outlet=0,
                        dst_id="obj-3",
                        dst_obj="comment",
                        dst_inlet=0,
                    )
                with self.assertRaises(IncompatibleConnectionError):
                    bridge.connect_objects(
                        patch_id="p1",
                        src_id="obj-1",
                        src_obj="nonexistent.obj",
                        src_outlet=0,
                        dst_id="obj-2",
                        dst_obj="ezdac~",
                        dst_inlet=0,
                    )
                self.assertEqual(len(srv.requests), 1)

                state = bridge.inspect_state("buffer~", "buf1")
                self.assertTrue(state["exists"])
                self.assertEqual(srv.requests[-1][0], "harmos/inspect_state")

                with self.assertRaises(ValueError):
                    bridge.inspect_state("invalid_kind", "x")
                self.assertEqual(len(srv.requests), 2)


class TestAuditLiveEndpoint(unittest.TestCase):
    def test_static_contract_gate_rejects_before_touching_live_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            patcher = _write_patcher(
                Path(tmp) / "illegal.maxpat",
                [_box("b1", "cycle~ 220"), _box("b2", "note", maxclass="comment")],
                [_line("b1", 0, "b2", 0)],
            )
            with _LoopbackWebSocketServer() as srv:
                verdict, _ = audit.audit_patcher_live(patcher, live_endpoint=srv.url)
                self.assertEqual(verdict, "FAIL")
                self.assertEqual(srv.connections_count, 0)

    def test_unreachable_live_endpoint_returns_blocked(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", 0))
            closed_port = probe.getsockname()[1]

        with tempfile.TemporaryDirectory() as tmp:
            patcher = _write_patcher(
                Path(tmp) / "valid.maxpat",
                [_box("b1", "cycle~ 220"), _box("b2", "ezdac~")],
                [_line("b1", 0, "b2", 0)],
            )
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                with self.assertRaises(SystemExit) as ctx:
                    audit.main(
                        ["--patcher", str(patcher), "--live-endpoint", f"ws://127.0.0.1:{closed_port}", "--json"]
                    )
            self.assertEqual(ctx.exception.code, 2)
            env = json.loads(stdout.getvalue())
            self.assertEqual(env["status"], "BLOCKED")
            self.assertEqual(env["exit_code"], 2)

    def test_fail_closed_telemetry_verdicts_and_clean_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            patcher = _write_patcher(
                Path(tmp) / "valid.maxpat",
                [_box("b1", "cycle~ 220"), _box("b2", "ezdac~")],
                [_line("b1", 0, "b2", 0)],
            )

            cases = [
                ("not_loaded", {"loaded": False, "runtime": "Max 9", "console_lines": []}, "BLOCKED", 2),
                ("missing_runtime", {"loaded": True, "runtime": "", "console_lines": []}, "BLOCKED", 2),
                (
                    "pattern_error",
                    {"loaded": True, "runtime": "Max 9", "console_lines": ["foo: no such object"], "failed_objects": []},
                    "FAIL",
                    1,
                ),
                (
                    "log_level_error",
                    {
                        "loaded": True,
                        "runtime": "Max 9",
                        "console_lines": ["[2026-11-27 08:00:00.000 error] [12] broken"],
                        "failed_objects": [],
                    },
                    "FAIL",
                    1,
                ),
                (
                    "failed_objects",
                    {"loaded": True, "runtime": "Max 9", "console_lines": [], "failed_objects": ["missing.ext"]},
                    "FAIL",
                    1,
                ),
            ]
            for label, payload, expected_verdict, expected_exit in cases:
                with self.subTest(label=label):
                    with _LoopbackWebSocketServer(handler=lambda _m, _p, pl=payload: pl) as srv:
                        stdout = io.StringIO()
                        with contextlib.redirect_stdout(stdout):
                            with self.assertRaises(SystemExit) as ctx:
                                audit.main(["--patcher", str(patcher), "--live-endpoint", srv.url, "--json"])
                        self.assertEqual(ctx.exception.code, expected_exit)
                        env = json.loads(stdout.getvalue())
                        self.assertEqual(env["status"], expected_verdict)
                        self.assertEqual(env["exit_code"], expected_exit)

            clean_payload = {"loaded": True, "runtime": "Max 9", "console_lines": ["patcher loaded"], "failed_objects": []}
            with _LoopbackWebSocketServer(handler=lambda _m, _p: clean_payload) as srv:
                stdout_json = io.StringIO()
                with contextlib.redirect_stdout(stdout_json):
                    with self.assertRaises(SystemExit) as ctx_json:
                        audit.main(["--patcher", str(patcher), "--live-endpoint", srv.url, "--json"])
                self.assertEqual(ctx_json.exception.code, 0)
                env = json.loads(stdout_json.getvalue())
                self.assertEqual(env["status"], "PASS")
                self.assertEqual(env["command"], "audit")
                self.assertEqual(env["artifacts"]["live_endpoint"], srv.url)
                self.assertEqual(env["exit_code"], 0)

                stdout_plain = io.StringIO()
                with contextlib.redirect_stdout(stdout_plain):
                    with self.assertRaises(SystemExit) as ctx_plain:
                        audit.main(["--patcher", str(patcher), "--live-endpoint", srv.url])
                self.assertEqual(ctx_plain.exception.code, 0)
                self.assertIn("HARMOS LIVE AUDIT: PASS", stdout_plain.getvalue())

    def test_ir_overlay_with_provenance_passes_live_endpoint(self):
        sample_ir = {
            "object_name": "harmos.bridge_probe",
            "category": "control",
            "inlets": [{"id": 0, "type": "float", "description": "In"}],
            "outlets": [{"id": 0, "type": "float", "description": "Out"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            ir_path = Path(tmp) / "probe.ir.json"
            ir_path.write_text(json.dumps(sample_ir), encoding="utf-8")
            pkg_dir = Path(tmp) / "pkg"
            compiled = compile_ir(str(ir_path), str(pkg_dir), build=False)

            payload = {"loaded": True, "runtime": "Max 9", "console_lines": ["ok"], "failed_objects": []}
            with _LoopbackWebSocketServer(handler=lambda _m, _p: payload) as srv:
                verdict, details = audit.audit_patcher_live(
                    Path(compiled["maxpat_path"]),
                    ir_path=ir_path,
                    live_endpoint=srv.url,
                )
                self.assertEqual(verdict, "PASS")
                self.assertTrue(any("Procedencia verificada" in d for d in details))
                self.assertEqual(srv.connections_count, 1)


if __name__ == "__main__":
    unittest.main()
