"use strict";

/**
 * Zero-dependency loopback RFC 6455 WebSocket + JSON-RPC 2.0 receiver for Cycling '74 Max [node.script].
 * Fails closed when running standalone outside Max (no max-api available).
 */

const crypto = require("crypto");
const http = require("http");
const path = require("path");

const WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";
const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost", "::1"]);
const DEFAULT_PORT = 7400;
const MAX_FRAME_BYTES = 4 * 1024 * 1024;
const DEFAULT_MAX_TIMEOUT_MS = 15000;
const SUPPORTED_MAX_METHODS = new Set([
  "harmos/audit_patcher",
  "harmos/inspect_state",
  "harmos/connect",
]);

function computeAcceptKey(wsKey) {
  return crypto.createHash("sha1").update(wsKey + WS_GUID, "ascii").digest("base64");
}

function encodeFrame(opcode, payload) {
  const payloadBuf = Buffer.isBuffer(payload) ? payload : Buffer.from(String(payload), "utf8");
  const firstByte = 0x80 | (opcode & 0x0f);
  const length = payloadBuf.length;

  let header;
  if (length < 126) {
    header = Buffer.from([firstByte, length]);
  } else if (length < 65536) {
    header = Buffer.alloc(4);
    header[0] = firstByte;
    header[1] = 126;
    header.writeUInt16BE(length, 2);
  } else {
    header = Buffer.alloc(10);
    header[0] = firstByte;
    header[1] = 127;
    header.writeBigUInt64BE(BigInt(length), 2);
  }
  return Buffer.concat([header, payloadBuf]);
}

function decodeNextFrame(buffer) {
  if (buffer.length < 2) {
    return null;
  }

  const fin = (buffer[0] & 0x80) !== 0;
  const opcode = buffer[0] & 0x0f;
  const masked = (buffer[1] & 0x80) !== 0;
  let length = buffer[1] & 0x7f;

  if (!masked) {
    throw new Error("Client WebSocket frames must be masked.");
  }

  let offset = 2;
  if (length === 126) {
    if (buffer.length < 4) {
      return null;
    }
    length = buffer.readUInt16BE(2);
    offset = 4;
  } else if (length === 127) {
    if (buffer.length < 10) {
      return null;
    }
    const bigLength = buffer.readBigUInt64BE(2);
    if (bigLength > BigInt(MAX_FRAME_BYTES)) {
      throw new Error(`WebSocket frame exceeds maximum allowed size (${MAX_FRAME_BYTES} bytes).`);
    }
    length = Number(bigLength);
    offset = 10;
  }

  if (length > MAX_FRAME_BYTES) {
    throw new Error(`WebSocket frame exceeds maximum allowed size (${MAX_FRAME_BYTES} bytes).`);
  }

  const totalBytes = offset + 4 + length;
  if (buffer.length < totalBytes) {
    return null;
  }

  const maskKey = buffer.subarray(offset, offset + 4);
  const payload = Buffer.from(buffer.subarray(offset + 4, totalBytes));
  for (let i = 0; i < length; i += 1) {
    payload[i] ^= maskKey[i % 4];
  }

  return {
    frame: { fin, opcode, payload },
    remaining: buffer.subarray(totalBytes),
  };
}

function resolveMaxApi(explicitMaxApi, hasCustomHandlers) {
  if (explicitMaxApi !== undefined) {
    return explicitMaxApi;
  }
  if (hasCustomHandlers) {
    return null;
  }
  try {
    return require("max-api");
  } catch (_) {
    return null;
  }
}

function createReceiverServer(options = {}) {
  const host = options.host || "127.0.0.1";
  if (!LOOPBACK_HOSTS.has(host)) {
    throw new Error(`Refusing non-loopback host '${host}'; only loopback hosts are allowed.`);
  }

  const port = options.port !== undefined ? Number(options.port) : DEFAULT_PORT;
  if (!Number.isInteger(port) || port < 0 || port > 65535) {
    throw new Error(`Invalid port: ${options.port}`);
  }

  const handlers = options.handlers || null;
  const requestTimeoutMs = Number(options.requestTimeoutMs || DEFAULT_MAX_TIMEOUT_MS);
  const maxApi = resolveMaxApi(options.maxApi, Boolean(handlers));

  const sockets = new Set();
  const pendingRequests = new Map();
  let nextBridgeSeq = 1;

  if (maxApi && typeof maxApi.addHandler === "function") {
    maxApi.addHandler("harmos_reply", (rawPayload) => {
      let msg;
      try {
        msg = typeof rawPayload === "string" ? JSON.parse(rawPayload) : rawPayload;
      } catch (_) {
        return;
      }
      if (!msg || typeof msg !== "object" || msg.id === undefined) {
        return;
      }
      const entry = pendingRequests.get(msg.id);
      if (!entry) {
        return;
      }
      clearTimeout(entry.timer);
      pendingRequests.delete(msg.id);
      if (msg.error) {
        const err = new Error(String(msg.error.message || msg.error));
        err.rpcCode = typeof msg.error.code === "number" ? msg.error.code : -32000;
        entry.reject(err);
      } else {
        entry.resolve(msg.result && typeof msg.result === "object" ? msg.result : {});
      }
    });
  }

  async function forwardToMax(method, params) {
    if (!maxApi || typeof maxApi.outlet !== "function") {
      const err = new Error("max-api unavailable: receiver must run inside Cycling '74 Max");
      err.rpcCode = -32001;
      throw err;
    }

    const reqId = `max-${nextBridgeSeq}`;
    nextBridgeSeq += 1;

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pendingRequests.delete(reqId);
        const err = new Error(`Timed out waiting for Max reply on '${method}'.`);
        err.rpcCode = -32002;
        reject(err);
      }, requestTimeoutMs);

      pendingRequests.set(reqId, { resolve, reject, timer });
      try {
        Promise.resolve(
          maxApi.outlet("harmos_request", JSON.stringify({ id: reqId, method, params }))
        ).catch((outletErr) => {
          const entry = pendingRequests.get(reqId);
          if (entry) {
            clearTimeout(entry.timer);
            pendingRequests.delete(reqId);
            entry.reject(outletErr);
          }
        });
      } catch (syncErr) {
        const entry = pendingRequests.get(reqId);
        if (entry) {
          clearTimeout(entry.timer);
          pendingRequests.delete(reqId);
        }
        reject(syncErr);
      }
    });
  }

  async function dispatchRpc(method, params) {
    if (method === "harmos/ping") {
      return {
        ok: true,
        bridge: "harmos-node-for-max",
        max_api_attached: Boolean(maxApi),
      };
    }

    if (!SUPPORTED_MAX_METHODS.has(method)) {
      const err = new Error(`Method not found: ${method}`);
      err.rpcCode = -32601;
      throw err;
    }

    if (handlers && typeof handlers[method] === "function") {
      return handlers[method](params || {});
    }

    if (maxApi) {
      return forwardToMax(method, params || {});
    }

    if (method === "harmos/audit_patcher") {
      return {
        loaded: false,
        runtime: "",
        console_lines: [
          "BLOCKED (RUNTIME_UNAVAILABLE): max-api unavailable; receiver must run inside Cycling '74 Max.",
        ],
        failed_objects: [],
      };
    }

    const err = new Error("max-api unavailable: receiver must run inside Cycling '74 Max");
    err.rpcCode = -32001;
    throw err;
  }

  function sendJson(socket, payloadObj) {
    if (!socket.destroyed && socket.writable) {
      socket.write(encodeFrame(0x1, JSON.stringify(payloadObj)));
    }
  }

  async function handleTextMessage(socket, text) {
    let req;
    try {
      req = JSON.parse(text);
    } catch (parseErr) {
      sendJson(socket, {
        jsonrpc: "2.0",
        id: null,
        error: { code: -32700, message: `Parse error: ${parseErr.message}` },
      });
      return;
    }

    if (!req || typeof req !== "object" || typeof req.method !== "string") {
      sendJson(socket, {
        jsonrpc: "2.0",
        id: req && req.id !== undefined ? req.id : null,
        error: { code: -32600, message: "Invalid JSON-RPC request" },
      });
      return;
    }

    const rpcId = req.id !== undefined ? req.id : null;
    try {
      const result = await dispatchRpc(req.method, req.params);
      if (rpcId !== null) {
        sendJson(socket, { jsonrpc: "2.0", id: rpcId, result });
      }
    } catch (err) {
      if (rpcId !== null) {
        sendJson(socket, {
          jsonrpc: "2.0",
          id: rpcId,
          error: {
            code: typeof err.rpcCode === "number" ? err.rpcCode : -32000,
            message: err.message || String(err),
          },
        });
      }
    }
  }

  const server = http.createServer((_req, res) => {
    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("Harmos WebSocket endpoint expects ws:// upgrade.");
  });

  server.on("upgrade", (req, socket, head) => {
    const upgradeHeader = String(req.headers.upgrade || "").toLowerCase();
    const wsKey = req.headers["sec-websocket-key"];
    if (upgradeHeader !== "websocket" || typeof wsKey !== "string" || !wsKey.trim()) {
      socket.write("HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n");
      socket.destroy();
      return;
    }

    const acceptKey = computeAcceptKey(wsKey.trim());
    socket.write(
      "HTTP/1.1 101 Switching Protocols\r\n" +
        "Upgrade: websocket\r\n" +
        "Connection: Upgrade\r\n" +
        `Sec-WebSocket-Accept: ${acceptKey}\r\n\r\n`
    );

    sockets.add(socket);
    let rxBuffer = head && head.length > 0 ? Buffer.from(head) : Buffer.alloc(0);
    let fragments = [];
    let assembling = false;
    let totalBytes = 0;

    function processBufferedFrames() {
      while (rxBuffer.length > 0) {
        let decoded;
        try {
          decoded = decodeNextFrame(rxBuffer);
        } catch (_) {
          if (!socket.destroyed) {
            socket.write(encodeFrame(0x8, Buffer.alloc(0)));
            socket.destroy();
          }
          return;
        }
        if (!decoded) {
          return;
        }
        rxBuffer = decoded.remaining;
        const { fin, opcode, payload } = decoded.frame;

        if (opcode === 0x8) {
          if (!socket.destroyed && socket.writable) {
            socket.write(encodeFrame(0x8, Buffer.alloc(0)));
          }
          socket.end();
          return;
        }
        if (opcode === 0x9) {
          if (!socket.destroyed && socket.writable) {
            socket.write(encodeFrame(0xa, payload));
          }
          continue;
        }
        if (opcode === 0xa) {
          continue;
        }

        if (opcode === 0x1) {
          if (assembling) {
            socket.destroy();
            return;
          }
          assembling = true;
          fragments = [payload];
          totalBytes = payload.length;
        } else if (opcode === 0x0) {
          if (!assembling) {
            socket.destroy();
            return;
          }
          fragments.push(payload);
          totalBytes += payload.length;
        } else {
          socket.write(encodeFrame(0x8, Buffer.alloc(0)));
          socket.destroy();
          return;
        }

        if (totalBytes > MAX_FRAME_BYTES) {
          socket.write(encodeFrame(0x8, Buffer.alloc(0)));
          socket.destroy();
          return;
        }

        if (fin) {
          const text = Buffer.concat(fragments).toString("utf8");
          fragments = [];
          assembling = false;
          totalBytes = 0;
          void handleTextMessage(socket, text);
        }
      }
    }

    socket.on("data", (chunk) => {
      rxBuffer = rxBuffer.length === 0 ? Buffer.from(chunk) : Buffer.concat([rxBuffer, chunk]);
      processBufferedFrames();
    });
    socket.on("close", () => {
      sockets.delete(socket);
    });
    socket.on("error", () => {
      sockets.delete(socket);
    });

    if (rxBuffer.length > 0) {
      processBufferedFrames();
    }
  });

  function getAddress() {
    const addr = server.address();
    if (!addr || typeof addr === "string") {
      return { host, port };
    }
    return { host: addr.address, port: addr.port };
  }

  function listen() {
    return new Promise((resolve, reject) => {
      const onError = (err) => {
        server.removeListener("listening", onListening);
        reject(err);
      };
      const onListening = () => {
        server.removeListener("error", onError);
        resolve(getAddress());
      };
      server.once("error", onError);
      server.once("listening", onListening);
      server.listen(port, host);
    });
  }

  function close() {
    for (const entry of pendingRequests.values()) {
      clearTimeout(entry.timer);
      entry.reject(new Error("Receiver server shutting down."));
    }
    pendingRequests.clear();

    for (const sock of sockets) {
      try {
        if (!sock.destroyed && sock.writable) {
          sock.write(encodeFrame(0x8, Buffer.alloc(0)));
        }
        sock.destroy();
      } catch (_) {
        // Ignore teardown socket errors.
      }
    }
    sockets.clear();

    return new Promise((resolve) => {
      if (!server.listening) {
        resolve();
        return;
      }
      server.close(() => resolve());
    });
  }

  return { server, listen, close, getAddress, maxApi };
}

function parseCliPort(argv) {
  let port = Number(process.env.HARMOS_LIVE_PORT || DEFAULT_PORT);
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--port" && i + 1 < argv.length) {
      port = Number(argv[i + 1]);
      i += 1;
    } else if (arg.startsWith("--port=")) {
      port = Number(arg.slice("--port=".length));
    }
  }
  return port;
}

function isMaxHostedScript(env = process.env, currentFilename = __filename) {
  if (!env || typeof env.SCRIPT_PATH !== "string" || !env.SCRIPT_PATH.trim()) {
    return false;
  }
  const resolvedScript = path.resolve(env.SCRIPT_PATH);
  const resolvedCurrent = path.resolve(currentFilename);
  if (process.platform === "win32") {
    return resolvedScript.toLowerCase() === resolvedCurrent.toLowerCase();
  }
  return resolvedScript === resolvedCurrent;
}

const isCliMain = require.main === module;
const isMaxHosted = isMaxHostedScript();

if (isCliMain || isMaxHosted) {
  const port = parseCliPort(process.argv.slice(2));
  const receiver = createReceiverServer({ port });
  receiver
    .listen()
    .then((addr) => {
      const url = `ws://${addr.host}:${addr.port}`;
      process.stdout.write(`READY ${url}\n`);
      if (receiver.maxApi && typeof receiver.maxApi.post === "function") {
        receiver.maxApi.post(`Harmos live receiver listening on ${url}`);
      }
    })
    .catch((err) => {
      process.stderr.write(`ERROR ${err.message}\n`);
      if (isCliMain) {
        process.exit(1);
      }
    });

  const shutdown = () => {
    receiver.close().then(() => {
      if (isCliMain) {
        process.exit(0);
      }
    });
  };
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}

module.exports = {
  DEFAULT_PORT,
  LOOPBACK_HOSTS,
  MAX_FRAME_BYTES,
  computeAcceptKey,
  createReceiverServer,
  decodeNextFrame,
  encodeFrame,
  isMaxHostedScript,
};
