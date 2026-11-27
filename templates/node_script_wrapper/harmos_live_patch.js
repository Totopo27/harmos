/*
 * Harmos Live Patcher Companion for Cycling '74 Max [js] / [v8].
 * Pure ES5 without CommonJS imports. Pair with [node.script harmos_live_receiver.js].
 */

inlets = 1;
outlets = 1;

function _reply(id, result, errorMsg) {
    var payload = { id: id };
    if (errorMsg) {
        payload.error = { code: -32000, message: String(errorMsg) };
    } else {
        payload.result = result || {};
    }
    outlet(0, "harmos_reply", JSON.stringify(payload));
}

function _inspectState(params) {
    var kind = params && params.kind ? String(params.kind) : "";
    var name = params && params.name ? String(params.name) : "";
    if (!name) {
        throw new Error("inspect_state requires a non-empty name.");
    }

    if (kind === "buffer~") {
        var buf = new Buffer(name);
        var frames = buf.framecount();
        var channels = buf.channelcount();
        var lengthMs = buf.length();
        return {
            exists: frames > 0 || channels > 0 || lengthMs > 0,
            kind: "buffer~",
            name: name,
            framecount: frames,
            channelcount: channels,
            length_ms: lengthMs
        };
    }

    if (kind === "dict") {
        var dict = new Dict(name);
        var keys = dict.getkeys();
        var keyList = [];
        if (typeof keys === "string") {
            keyList = [keys];
        } else if (keys && keys.length) {
            for (var i = 0; i < keys.length; i += 1) {
                keyList.push(String(keys[i]));
            }
        }
        var serialized = dict.stringify();
        return {
            exists: keyList.length > 0 || (serialized && serialized !== "{}"),
            kind: "dict",
            name: name,
            keys: keyList,
            data: serialized ? JSON.parse(serialized) : {}
        };
    }

    if (kind === "coll") {
        return {
            exists: false,
            kind: "coll",
            name: name,
            supported: false,
            reason: "coll inspection requires direct patcher messaging"
        };
    }

    throw new Error("Unsupported inspect_state kind: " + kind);
}

function _connectObjects(params) {
    if (!params) {
        throw new Error("connect requires params.");
    }
    var src = this.patcher.getnamed(String(params.src_id || ""));
    var dst = this.patcher.getnamed(String(params.dst_id || ""));
    if (!src) {
        throw new Error("Source box scripting name not found: " + params.src_id);
    }
    if (!dst) {
        throw new Error("Destination box scripting name not found: " + params.dst_id);
    }
    this.patcher.connect(src, Number(params.src_outlet || 0), dst, Number(params.dst_inlet || 0));
    return {
        connected: true,
        patch_id: params.patch_id ? String(params.patch_id) : "",
        src_id: String(params.src_id),
        dst_id: String(params.dst_id)
    };
}

function _auditPatcher(params) {
    var patcherPath = params && params.patcher_path ? String(params.patcher_path) : "";
    if (!patcherPath) {
        return {
            loaded: false,
            runtime: "",
            console_lines: ["Missing patcher_path parameter."],
            failed_objects: []
        };
    }

    var runtimeLabel = (typeof max !== "undefined" && max.version) ? ("Max " + max.version) : "Max";
    var target = this.patcher;
    if (target.filepath && patcherPath.indexOf(target.name) === -1 && target.filepath !== patcherPath) {
        return {
            loaded: false,
            runtime: runtimeLabel,
            console_lines: [
                "BLOCKED: target patcher is not the currently attached host patcher (" + target.name + ")."
            ],
            failed_objects: []
        };
    }

    var failed = [];
    var obj = target.firstobject;
    while (obj) {
        if (obj.maxclass === "bogus") {
            failed.push(String(obj.varname || "bogus"));
        }
        obj = obj.nextobject;
    }

    return {
        loaded: true,
        runtime: runtimeLabel,
        console_lines: ["patcher inspected inside Max runtime (" + target.name + ")"],
        failed_objects: failed
    };
}

function harmos_request(jsonStr) {
    var req;
    try {
        req = typeof jsonStr === "string" ? JSON.parse(jsonStr) : jsonStr;
    } catch (e) {
        return;
    }
    if (!req || req.id === undefined) {
        return;
    }

    try {
        var method = String(req.method || "");
        var params = req.params || {};
        if (method === "harmos/inspect_state") {
            _reply(req.id, _inspectState(params), null);
        } else if (method === "harmos/connect") {
            _reply(req.id, _connectObjects(params), null);
        } else if (method === "harmos/audit_patcher") {
            _reply(req.id, _auditPatcher(params), null);
        } else {
            _reply(req.id, null, "Unsupported Max patch handler method: " + method);
        }
    } catch (err) {
        _reply(req.id, null, err && err.message ? err.message : String(err));
    }
}
