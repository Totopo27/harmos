"""Cross-process integration tests for the zero-dependency Node-for-Max live receiver."""
import contextlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Dict, List, Optional

from core.compiler.contract_engine import IncompatibleConnectionError
from core.compiler.live_bridge import LiveBridgeProtocolError, MaxLiveBridge
from scripts import audit

REPO_ROOT = Path(__file__).resolve().parent.parent
RECEIVER_JS = REPO_ROOT / "templates" / "node_script_wrapper" / "harmos_live_receiver.js"
PATCH_JS = REPO_ROOT / "templates" / "node_script_wrapper" / "harmos_live_patch.js"
NODE_BIN = shutil.which("node")


def _write_patcher(path: Path, boxes: List[Dict], lines: List[Dict]) -> Path:
    path.write_text(json.dumps({"patcher": {"boxes": boxes, "lines": lines}}), encoding="utf-8")
    return path


def _box(box_id: str, text: str, maxclass: str = "newobj") -> Dict:
    return {"box": {"id": box_id, "maxclass": maxclass, "text": text}}


def _line(src_id: str, src_out: int, dst_id: str, dst_in: int) -> Dict:
    return {"patchline": {"source": [src_id, src_out], "destination": [dst_id, dst_in]}}


def _read_ready_url(proc: subprocess.Popen, timeout_sec: float = 5.0) -> str:
    found: List[str] = []
    errors: List[str] = []

    def _reader() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            text = line.strip()
            if text.startswith("READY ws://"):
                found.append(text.split(" ", 1)[1].strip())
                return
        if proc.stderr is not None:
            err_text = proc.stderr.read().strip()
            if err_text:
                errors.append(err_text)

    thread = threading.Thread(target=_reader, daemon=True)
    thread.start()
    thread.join(timeout=timeout_sec)
    if not found:
        detail = errors[0] if errors else "no READY line emitted before timeout"
        raise AssertionError(f"Node receiver failed to emit READY ws:// URL: {detail}")
    return found[0]


def _stop_proc(proc: Optional[subprocess.Popen]) -> None:
    if proc is None:
        return
    try:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2.0)
    finally:
        for stream in (proc.stdout, proc.stderr, proc.stdin):
            if stream is not None:
                try:
                    stream.close()
                except OSError:
                    pass


@unittest.skipUnless(NODE_BIN, "node runtime unavailable")
class TestLiveReceiverNode(unittest.TestCase):
    def test_js_syntax_and_max_js_purity(self):
        for script_path in (RECEIVER_JS, PATCH_JS):
            self.assertTrue(script_path.is_file(), f"Missing JS script: {script_path.name}")
            res = subprocess.run(
                [NODE_BIN, "--check", str(script_path)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0, f"node --check failed for {script_path.name}: {res.stderr}")

        patch_src = PATCH_JS.read_text(encoding="utf-8")
        self.assertNotIn("require(", patch_src)

    def test_standalone_receiver_fails_closed_without_max_api(self):
        proc = subprocess.Popen(
            [NODE_BIN, str(RECEIVER_JS), "--port", "0"],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            url = _read_ready_url(proc)
            with MaxLiveBridge(url, timeout=3.0) as bridge:
                ping_res = bridge.ping()
                self.assertTrue(ping_res["ok"])
                self.assertFalse(ping_res["max_api_attached"])

                with self.assertRaises(IncompatibleConnectionError):
                    bridge.connect_objects(
                        patch_id="p1",
                        src_id="b1",
                        src_obj="cycle~",
                        src_outlet=0,
                        dst_id="b2",
                        dst_obj="comment",
                        dst_inlet=0,
                    )

                with self.assertRaises(LiveBridgeProtocolError):
                    bridge.connect_objects(
                        patch_id="p1",
                        src_id="b1",
                        src_obj="cycle~",
                        src_outlet=0,
                        dst_id="b2",
                        dst_obj="ezdac~",
                        dst_inlet=0,
                    )

            with tempfile.TemporaryDirectory() as tmp:
                valid_patcher = _write_patcher(
                    Path(tmp) / "valid.maxpat",
                    [_box("b1", "cycle~ 220"), _box("b2", "ezdac~")],
                    [_line("b1", 0, "b2", 0)],
                )
                verdict, _ = audit.audit_patcher_live(valid_patcher, live_endpoint=url)
                self.assertEqual(verdict, "BLOCKED")

                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    with self.assertRaises(SystemExit) as ctx:
                        audit.main(["--patcher", str(valid_patcher), "--live-endpoint", url, "--json"])
                self.assertEqual(ctx.exception.code, 2)
                env = json.loads(stdout.getvalue())
                self.assertEqual(env["status"], "BLOCKED")
                self.assertEqual(env["exit_code"], 2)
        finally:
            _stop_proc(proc)

    def test_python_bridge_and_audit_against_real_node_receiver(self):
        harness_js = """
const path = require("path");
const { createReceiverServer } = require("./templates/node_script_wrapper/harmos_live_receiver.js");
const longPayload = "x".repeat(320);
const serverHandle = createReceiverServer({
  port: 0,
  handlers: {
    "harmos/inspect_state": (params) => {
      if (params.kind === "buffer~") {
        return { exists: true, kind: "buffer~", name: params.name, framecount: 44100, channelcount: 2 };
      }
      return { exists: true, kind: params.kind, name: params.name, data: { blob: longPayload } };
    },
    "harmos/connect": (params) => ({
      connected: true,
      patch_id: params.patch_id,
      src_id: params.src_id,
      dst_id: params.dst_id,
    }),
    "harmos/audit_patcher": (params) => {
      const base = path.basename(params.patcher_path || "");
      if (base === "bad_runtime.maxpat") {
        return {
          loaded: true,
          runtime: "Max 9",
          console_lines: ["foo: no such object"],
          failed_objects: ["missing.ext"],
        };
      }
      return {
        loaded: true,
        runtime: "Max 9",
        console_lines: ["patcher loaded cleanly"],
        failed_objects: [],
      };
    },
  },
});
serverHandle.listen().then((addr) => {
  process.stdout.write(`READY ws://${addr.host}:${addr.port}\\n`);
});
process.on("SIGTERM", () => serverHandle.close().then(() => process.exit(0)));
process.on("SIGINT", () => serverHandle.close().then(() => process.exit(0)));
"""
        proc = subprocess.Popen(
            [NODE_BIN, "-e", harness_js],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            node_url = _read_ready_url(proc)
            with MaxLiveBridge(node_url, timeout=3.0) as bridge:
                self.assertTrue(bridge.ping()["ok"])

                buf_state = bridge.inspect_state("buffer~", "buf1")
                self.assertEqual(buf_state["framecount"], 44100)

                dict_state = bridge.inspect_state("dict", "d1")
                self.assertEqual(len(dict_state["data"]["blob"]), 320)

                conn_res = bridge.connect_objects(
                    patch_id="p1",
                    src_id="b1",
                    src_obj="cycle~",
                    src_outlet=0,
                    dst_id="b2",
                    dst_obj="ezdac~",
                    dst_inlet=0,
                )
                self.assertTrue(conn_res["connected"])

                with self.assertRaises(IncompatibleConnectionError):
                    bridge.connect_objects(
                        patch_id="p1",
                        src_id="b1",
                        src_obj="cycle~",
                        src_outlet=0,
                        dst_id="b3",
                        dst_obj="comment",
                        dst_inlet=0,
                    )

            with tempfile.TemporaryDirectory() as tmp:
                valid_patcher = _write_patcher(
                    Path(tmp) / "valid.maxpat",
                    [_box("b1", "cycle~ 220"), _box("b2", "ezdac~")],
                    [_line("b1", 0, "b2", 0)],
                )
                bad_runtime_patcher = _write_patcher(
                    Path(tmp) / "bad_runtime.maxpat",
                    [_box("b1", "cycle~ 220"), _box("b2", "ezdac~")],
                    [_line("b1", 0, "b2", 0)],
                )
                illegal_patcher = _write_patcher(
                    Path(tmp) / "illegal.maxpat",
                    [_box("b1", "cycle~ 220"), _box("b2", "note", maxclass="comment")],
                    [_line("b1", 0, "b2", 0)],
                )

                out_pass = io.StringIO()
                with contextlib.redirect_stdout(out_pass):
                    with self.assertRaises(SystemExit) as ctx_pass:
                        audit.main(["--patcher", str(valid_patcher), "--live-endpoint", node_url, "--json"])
                self.assertEqual(ctx_pass.exception.code, 0)
                env_pass = json.loads(out_pass.getvalue())
                self.assertEqual(env_pass["status"], "PASS")
                self.assertEqual(env_pass["artifacts"]["live_endpoint"], node_url)

                out_fail = io.StringIO()
                with contextlib.redirect_stdout(out_fail):
                    with self.assertRaises(SystemExit) as ctx_fail:
                        audit.main(["--patcher", str(bad_runtime_patcher), "--live-endpoint", node_url, "--json"])
                self.assertEqual(ctx_fail.exception.code, 1)
                self.assertEqual(json.loads(out_fail.getvalue())["status"], "FAIL")

                out_static = io.StringIO()
                with contextlib.redirect_stdout(out_static):
                    with self.assertRaises(SystemExit) as ctx_static:
                        audit.main(["--patcher", str(illegal_patcher), "--live-endpoint", node_url, "--json"])
                self.assertEqual(ctx_static.exception.code, 1)
                self.assertEqual(json.loads(out_static.getvalue())["status"], "FAIL")
        finally:
            _stop_proc(proc)

    def test_max_nsrunner_dynamic_import_autostarts_receiver(self):
        env = dict(os.environ)
        env["SCRIPT_PATH"] = str(RECEIVER_JS)
        env["HARMOS_LIVE_PORT"] = "0"
        proc = subprocess.Popen(
            [NODE_BIN, "-e", 'import(require("url").pathToFileURL(process.env.SCRIPT_PATH).href)'],
            cwd=REPO_ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            url = _read_ready_url(proc)
            with MaxLiveBridge(url, timeout=3.0) as bridge:
                ping_res = bridge.ping()
                self.assertTrue(ping_res["ok"])
                self.assertFalse(ping_res["max_api_attached"])

            with tempfile.TemporaryDirectory() as tmp:
                valid_patcher = _write_patcher(
                    Path(tmp) / "valid.maxpat",
                    [_box("b1", "cycle~ 220"), _box("b2", "ezdac~")],
                    [_line("b1", 0, "b2", 0)],
                )
                verdict, _ = audit.audit_patcher_live(valid_patcher, live_endpoint=url)
                self.assertEqual(verdict, "BLOCKED")
        finally:
            _stop_proc(proc)


if __name__ == "__main__":
    unittest.main()
