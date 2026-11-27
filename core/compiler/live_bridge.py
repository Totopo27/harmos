"""Stdlib WebSocket live bridge to Max MSP gated by ContractEngine."""
import base64
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import socket
import struct
from typing import Any, Callable, Dict, List, Optional, Tuple
import urllib.parse

from core.compiler.contract_engine import (
    ConnectionAssessment,
    ContractEngine,
    IncompatibleConnectionError,
)

_WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
DEFAULT_LIVE_PORT = 7400
MAX_FRAME_BYTES = 4 * 1024 * 1024
_MAX_HANDSHAKE_BYTES = 64 * 1024
INSPECTABLE_STATE_KINDS = frozenset({"buffer~", "dict", "coll"})


class LiveBridgeError(RuntimeError):
    """Base error for live Max bridge transport and protocol failures."""


class LiveBridgeConnectionError(LiveBridgeError):
    """Raised when the loopback WebSocket endpoint cannot be reached or closes."""


class LiveBridgeProtocolError(LiveBridgeError):
    """Raised when handshake, framing, or JSON-RPC payloads violate the protocol."""


@dataclass(frozen=True)
class LiveAuditReceipt:
    """Telemetry returned by a live Max endpoint for a single patcher load."""

    loaded: bool
    runtime: str
    console_lines: Tuple[str, ...]
    failed_objects: Tuple[str, ...]
    endpoint: str


def parse_ws_endpoint(endpoint: str) -> Tuple[str, int, str]:
    """Validate and parse a loopback-only ws:// endpoint into (host, port, path)."""
    if not isinstance(endpoint, str) or not endpoint.strip():
        raise LiveBridgeError("Live endpoint must be a non-empty ws:// URL.")
    try:
        parsed = urllib.parse.urlsplit(endpoint.strip())
    except ValueError as exc:
        raise LiveBridgeError(f"Invalid live endpoint URL: {exc}") from exc

    if parsed.scheme.lower() != "ws":
        raise LiveBridgeError(
            f"Unsupported live endpoint scheme {parsed.scheme!r}; only 'ws://' is allowed."
        )

    host = (parsed.hostname or "").lower()
    if host not in _LOOPBACK_HOSTS:
        raise LiveBridgeError(
            f"Refusing non-loopback live endpoint host {host!r}; only loopback hosts are permitted."
        )

    try:
        port = parsed.port
    except ValueError as exc:
        raise LiveBridgeError(f"Invalid live endpoint port: {exc}") from exc

    if port is None:
        port = DEFAULT_LIVE_PORT
    if not (1 <= port <= 65535):
        raise LiveBridgeError(f"Live endpoint port out of range: {port}")

    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return host, port, path


class StdlibWebSocketClient:
    """Minimal RFC 6455 loopback WebSocket client using only Python stdlib sockets."""

    def __init__(self, endpoint: str, timeout: float = 10.0):
        self.endpoint = endpoint
        self.host, self.port, self.path = parse_ws_endpoint(endpoint)
        self.timeout = max(float(timeout), 0.1)
        self._sock: Optional[socket.socket] = None
        self._rx_buffer = bytearray()

    def __enter__(self) -> "StdlibWebSocketClient":
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def connect(self) -> None:
        """Open TCP socket and complete RFC 6455 upgrade handshake."""
        if self._sock is not None:
            return
        try:
            sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
            sock.settimeout(self.timeout)
        except OSError as exc:
            raise LiveBridgeConnectionError(
                f"Cannot connect to live endpoint {self.endpoint}: {exc}"
            ) from exc

        self._sock = sock
        self._rx_buffer.clear()
        try:
            ws_key = base64.b64encode(os.urandom(16)).decode("ascii")
            host_header = f"[{self.host}]:{self.port}" if ":" in self.host else f"{self.host}:{self.port}"
            request = (
                f"GET {self.path} HTTP/1.1\r\n"
                f"Host: {host_header}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {ws_key}\r\n"
                "Sec-WebSocket-Version: 13\r\n"
                "\r\n"
            )
            try:
                sock.sendall(request.encode("ascii"))

                raw = bytearray()
                while b"\r\n\r\n" not in raw:
                    chunk = sock.recv(4096)
                    if not chunk:
                        raise LiveBridgeConnectionError("WebSocket handshake closed before completion.")
                    raw.extend(chunk)
                    if len(raw) > _MAX_HANDSHAKE_BYTES:
                        raise LiveBridgeProtocolError("WebSocket handshake response exceeded maximum size.")
            except OSError as exc:
                raise LiveBridgeConnectionError(
                    f"WebSocket handshake I/O failed for {self.endpoint}: {exc}"
                ) from exc

            header_end = raw.index(b"\r\n\r\n") + 4
            header_bytes = bytes(raw[:header_end])
            if header_end < len(raw):
                self._rx_buffer.extend(raw[header_end:])

            lines = header_bytes.decode("iso-8859-1").split("\r\n")
            status_line = lines[0] if lines else ""
            if " 101 " not in status_line and not status_line.endswith(" 101"):
                raise LiveBridgeProtocolError(f"WebSocket handshake rejected: {status_line!r}")

            headers: Dict[str, str] = {}
            for line in lines[1:]:
                if ":" in line:
                    k, v = line.split(":", 1)
                    headers[k.strip().lower()] = v.strip()

            expected_accept = base64.b64encode(
                hashlib.sha1((ws_key + _WS_GUID).encode("ascii")).digest()
            ).decode("ascii")
            actual_accept = headers.get("sec-websocket-accept", "")
            if actual_accept != expected_accept:
                raise LiveBridgeProtocolError("Invalid Sec-WebSocket-Accept in handshake response.")
        except Exception:
            self.close()
            raise

    def close(self) -> None:
        """Close the WebSocket connection cleanly."""
        sock = self._sock
        if sock is None:
            return
        self._sock = None
        try:
            self._send_frame_on(sock, 0x8, b"")
        except OSError:
            pass
        try:
            sock.close()
        except OSError:
            pass
        self._rx_buffer.clear()

    def _recv_exact(self, count: int) -> bytes:
        if count == 0:
            return b""
        if self._sock is None:
            raise LiveBridgeConnectionError("WebSocket is not connected.")
        while len(self._rx_buffer) < count:
            try:
                chunk = self._sock.recv(max(4096, count - len(self._rx_buffer)))
            except OSError as exc:
                raise LiveBridgeConnectionError(f"WebSocket read failed: {exc}") from exc
            if not chunk:
                raise LiveBridgeConnectionError("WebSocket closed unexpectedly while reading frame.")
            self._rx_buffer.extend(chunk)
        data = bytes(self._rx_buffer[:count])
        del self._rx_buffer[:count]
        return data

    def _send_frame_on(self, sock: socket.socket, opcode: int, payload: bytes) -> None:
        if len(payload) > MAX_FRAME_BYTES:
            raise LiveBridgeProtocolError(f"Outgoing WebSocket frame exceeds {MAX_FRAME_BYTES} bytes.")
        first = 0x80 | (opcode & 0x0F)
        length = len(payload)
        if length < 126:
            header = bytes([first, 0x80 | length])
        elif length < 65536:
            header = struct.pack("!BBH", first, 0x80 | 126, length)
        else:
            header = struct.pack("!BBQ", first, 0x80 | 127, length)

        mask = os.urandom(4)
        masked = bytearray(payload)
        for i in range(length):
            masked[i] ^= mask[i % 4]
        try:
            sock.sendall(header + mask + bytes(masked))
        except OSError as exc:
            raise LiveBridgeConnectionError(f"WebSocket write failed: {exc}") from exc

    def send_text(self, text: str) -> None:
        """Send a UTF-8 text WebSocket frame."""
        if self._sock is None:
            raise LiveBridgeConnectionError("WebSocket is not connected.")
        self._send_frame_on(self._sock, 0x1, text.encode("utf-8"))

    def _recv_frame(self) -> Tuple[bool, int, bytes]:
        b1, b2 = self._recv_exact(2)
        fin = bool(b1 & 0x80)
        opcode = b1 & 0x0F
        masked = bool(b2 & 0x80)
        length = b2 & 0x7F

        if length == 126:
            (length,) = struct.unpack("!H", self._recv_exact(2))
        elif length == 127:
            (length,) = struct.unpack("!Q", self._recv_exact(8))

        if length > MAX_FRAME_BYTES:
            raise LiveBridgeProtocolError(f"Incoming WebSocket frame exceeds {MAX_FRAME_BYTES} bytes.")

        mask = self._recv_exact(4) if masked else b""
        payload = bytearray(self._recv_exact(length))
        if masked:
            for i in range(length):
                payload[i] ^= mask[i % 4]
        return fin, opcode, bytes(payload)

    def recv_text(self) -> str:
        """Receive the next complete UTF-8 text message, answering control pings."""
        fragments: List[bytes] = []
        assembling = False
        total_bytes = 0

        while True:
            fin, opcode, payload = self._recv_frame()
            if opcode == 0x8:  # CLOSE
                self.close()
                raise LiveBridgeConnectionError("WebSocket closed by remote endpoint.")
            if opcode == 0x9:  # PING
                if self._sock is not None:
                    self._send_frame_on(self._sock, 0xA, payload)
                continue
            if opcode == 0xA:  # PONG
                continue

            if opcode in (0x1, 0x2):
                if assembling:
                    raise LiveBridgeProtocolError("Unexpected new data frame before previous message completed.")
                if opcode == 0x2:
                    raise LiveBridgeProtocolError("Binary WebSocket frames are not supported.")
                assembling = True
                fragments.append(payload)
                total_bytes += len(payload)
            elif opcode == 0x0:
                if not assembling:
                    raise LiveBridgeProtocolError("Unexpected WebSocket continuation frame.")
                fragments.append(payload)
                total_bytes += len(payload)
            else:
                raise LiveBridgeProtocolError(f"Unsupported WebSocket opcode: {opcode}")

            if total_bytes > MAX_FRAME_BYTES:
                raise LiveBridgeProtocolError(f"Reassembled WebSocket message exceeds {MAX_FRAME_BYTES} bytes.")

            if fin:
                raw = b"".join(fragments)
                try:
                    return raw.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise LiveBridgeProtocolError(f"Invalid UTF-8 in WebSocket text message: {exc}") from exc


class MaxLiveBridge:
    """JSON-RPC 2.0 client over loopback WebSocket gated by ContractEngine."""

    def __init__(
        self,
        endpoint: str,
        *,
        contract_engine: Optional[ContractEngine] = None,
        timeout: float = 10.0,
        transport_factory: Optional[Callable[..., Any]] = None,
    ):
        self.endpoint = endpoint
        parse_ws_endpoint(endpoint)
        self.contract_engine = contract_engine or ContractEngine()
        self.timeout = timeout
        self._transport_factory = transport_factory or StdlibWebSocketClient
        self._transport: Optional[Any] = None
        self._next_id = 1

    def __enter__(self) -> "MaxLiveBridge":
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def connect(self) -> None:
        if self._transport is None:
            client = self._transport_factory(self.endpoint, timeout=self.timeout)
            client.connect()
            self._transport = client

    def close(self) -> None:
        if self._transport is not None:
            try:
                self._transport.close()
            finally:
                self._transport = None

    def call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Invoke a JSON-RPC 2.0 method and return its dict result."""
        req_id = self._next_id
        self._next_id += 1
        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "method": method,
                "params": params if params is not None else {},
            }
        )

        transient = False
        transport = self._transport
        if transport is None:
            transport = self._transport_factory(self.endpoint, timeout=self.timeout)
            transport.connect()
            transient = True

        try:
            transport.send_text(payload)
            while True:
                raw_reply = transport.recv_text()
                try:
                    message = json.loads(raw_reply)
                except json.JSONDecodeError as exc:
                    raise LiveBridgeProtocolError(f"Malformed JSON-RPC reply: {exc}") from exc
                if not isinstance(message, dict):
                    raise LiveBridgeProtocolError("JSON-RPC reply must be a JSON object.")
                if "id" not in message:
                    continue
                if message["id"] != req_id:
                    raise LiveBridgeProtocolError(
                        f"Mismatched JSON-RPC response id: expected {req_id}, got {message['id']!r}."
                    )
                if "error" in message and message["error"] is not None:
                    raise LiveBridgeProtocolError(f"JSON-RPC error from {method}: {message['error']}")
                result = message.get("result")
                if not isinstance(result, dict):
                    raise LiveBridgeProtocolError(f"JSON-RPC result from {method} must be an object.")
                return result
        finally:
            if transient:
                transport.close()

    def ping(self) -> Dict[str, Any]:
        return self.call("harmos/ping")

    def validate_connection(
        self, src_obj: str, src_outlet: int, dst_obj: str, dst_inlet: int
    ) -> ConnectionAssessment:
        """Validate a connection strictly against ContractEngine before live mutation."""
        assessment = self.contract_engine.assess_connection(src_obj, src_outlet, dst_obj, dst_inlet)
        if assessment.status != "VALID":
            raise IncompatibleConnectionError(assessment.reason)
        return assessment

    def connect_objects(
        self,
        *,
        patch_id: str,
        src_id: str,
        src_obj: str,
        src_outlet: int,
        dst_id: str,
        dst_obj: str,
        dst_inlet: int,
    ) -> Dict[str, Any]:
        """Validate connection contracts locally, then request live patchcord creation."""
        self.validate_connection(src_obj, src_outlet, dst_obj, dst_inlet)
        return self.call(
            "harmos/connect",
            {
                "patch_id": patch_id,
                "src_id": src_id,
                "src_obj": src_obj,
                "src_outlet": src_outlet,
                "dst_id": dst_id,
                "dst_obj": dst_obj,
                "dst_inlet": dst_inlet,
            },
        )

    def inspect_state(self, kind: str, name: str, *, patch_id: Optional[str] = None) -> Dict[str, Any]:
        """Inspect live Max runtime state for buffer~, dict, or coll objects."""
        if kind not in INSPECTABLE_STATE_KINDS:
            raise ValueError(
                f"Unsupported state inspection kind {kind!r}; expected one of {sorted(INSPECTABLE_STATE_KINDS)}."
            )
        if not isinstance(name, str) or not name.strip():
            raise ValueError("State target name must be a non-empty string.")
        params: Dict[str, Any] = {"kind": kind, "name": name}
        if patch_id is not None:
            params["patch_id"] = patch_id
        return self.call("harmos/inspect_state", params)

    def audit_patcher(self, patcher_path: Path, *, timeout_seconds: int = 30) -> LiveAuditReceipt:
        """Request live patcher loading and console capture from the Max endpoint."""
        result = self.call(
            "harmos/audit_patcher",
            {
                "patcher_path": str(patcher_path),
                "timeout_seconds": int(timeout_seconds),
            },
        )
        loaded = result.get("loaded")
        if type(loaded) is not bool:
            raise LiveBridgeProtocolError("Live audit result missing boolean 'loaded'.")
        runtime = result.get("runtime", "")
        if not isinstance(runtime, str):
            raise LiveBridgeProtocolError("Live audit result field 'runtime' must be a string.")
        raw_lines = result.get("console_lines", [])
        if not isinstance(raw_lines, list) or any(not isinstance(item, str) for item in raw_lines):
            raise LiveBridgeProtocolError("Live audit result field 'console_lines' must be a list of strings.")
        raw_failed = result.get("failed_objects", [])
        if not isinstance(raw_failed, list) or any(not isinstance(item, str) for item in raw_failed):
            raise LiveBridgeProtocolError("Live audit result field 'failed_objects' must be a list of strings.")

        return LiveAuditReceipt(
            loaded=loaded,
            runtime=runtime,
            console_lines=tuple(raw_lines),
            failed_objects=tuple(raw_failed),
            endpoint=self.endpoint,
        )
