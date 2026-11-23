#!/usr/bin/env node
/**
 * Affinity 3 local MCP client for authorized Windows desktop sessions.
 * Zero dependencies. Talks only to local IPv6/IPv4 loopback.
 * Hold one legacy HTTP/SSE MCP session for handshake, preamble and actions.
 *
 * node scripts/affinity_mcp_cli.mjs probe
 * node scripts/affinity_mcp_cli.mjs inspect
 * node scripts/affinity_mcp_cli.mjs docs document.js
 * node scripts/affinity_mcp_cli.mjs run scripts/my_test.js --allow-write
 * node scripts/affinity_mcp_cli.mjs render DOCUMENT_UUID 0 work/test.jpg
 *
 * Never blindly retry timed-out mutating execute_script actions.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createHash } from "node:crypto";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SSE = "http://[::1]:6767/sse";
const PROTOCOL = "2025-11-25";
const RESP_TIMEOUT_MS = 30000;
const MAX_FRAME = 8_000_000;
const MAX_SCRIPT = 150_000;

function assert(ok, message) {
  if (!ok) throw new Error(message);
}
function parseEvent(frame) {
  const parts = frame.split("\n");
  const event = parts.filter(x => x.startsWith("event:")).map(x => x.slice(6).trim())[0] || "";
  const data = parts.filter(x => x.startsWith("data:")).map(x => x.slice(5).trimStart()).join("\n");
  return { event, data };
}
function onlyLocal(url) {
  const v = new URL(url);
  assert(v.protocol === "http:" && ["[::1]", "127.0.0.1", "localhost"].includes(v.hostname),
    "Affinity MCP must be loopback only");
  assert(!v.username && !v.password, "Do not place credentials in MCP URLs");
  return v;
}
function inside(base, input, mustExist = false) {
  assert(typeof input === "string" && input.length > 0,
    "A non-empty local path is required");
  const root = fs.realpathSync(base);
  const requested = path.resolve(input);
  const actual = mustExist ? fs.realpathSync(requested) :
    path.join(fs.realpathSync(path.dirname(requested)), path.basename(requested));
  const rel = path.relative(root, actual);
  assert(rel === "" || (!rel.startsWith("..") && !path.isAbsolute(rel)),
    "Outside local agent-affinity working directory: " + actual);
  return actual;
}
function flatten(result) {
  if (!result || !Array.isArray(result.content)) return "";
  return result.content.filter(x => x.type === "text").map(x => String(x.text || "")).join("\n");
}

class Session {
  constructor() {
    this.sse = onlyLocal(process.env.AFFINITY_MCP_URL || SSE);
    assert(this.sse.pathname === "/sse", "Unexpected MCP SSE path");
    this.abort = new AbortController();
    this.pending = new Map();
    this.waiters = [];
    this.next = 0;
    this.endpoint = null;
    this.closed = false;
  }
  async start() {
    const timer = setTimeout(() => this.abort.abort(), 15000);
    try {
      const r = await fetch(this.sse, {
        headers: { accept: "text/event-stream" },
        signal: this.abort.signal,
        redirect: "error"
      });
      assert(r.ok && r.body, "Affinity SSE unavailable: HTTP " + r.status);
      assert((r.headers.get("content-type") || "").includes("text/event-stream"),
        "Affinity MCP did not return an event stream");
      this.pump(r.body).catch(e => { this.error = e.message; });
      await Promise.race([
        new Promise((resolve, reject) => { this.waiters.push({ resolve, reject }); }),
        new Promise((_, reject) => setTimeout(() => reject(new Error("MCP endpoint event timeout")), 15000))
      ]);
    } finally {
      clearTimeout(timer);
    }
    return this;
  }
  async pump(body) {
    const reader = body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value || new Uint8Array(), { stream: true }).replace(/\r\n/g, "\n");
        assert(buffer.length <= MAX_FRAME, "MCP SSE frame too large");
        let split;
        while ((split = buffer.indexOf("\n\n")) >= 0) {
          const frame = buffer.slice(0, split);
          buffer = buffer.slice(split + 2);
          const { event, data } = parseEvent(frame);
          if (!data) continue;
          if (event === "endpoint" || data.startsWith("/")) {
            const endpoint = onlyLocal(new URL(data, this.sse).toString());
            assert(endpoint.origin === this.sse.origin && endpoint.pathname === "/message",
              "Affinity MCP endpoint escaped loopback message path");
            this.endpoint = endpoint;
            for (const waiter of this.waiters) waiter.resolve(endpoint);
            this.waiters = [];
            continue;
          }
          let result;
          try { result = JSON.parse(data); } catch { continue; }
          const p = this.pending.get(result.id);
          if (!p) continue;
          clearTimeout(p.timer);
          this.pending.delete(result.id);
          if (result.error) p.reject(new Error("MCP RPC " +
            result.error.code + ": " + result.error.message));
          else p.resolve(result.result || {});
        }
      }
    } catch (e) {
      this.error = String(e.message || e);
    } finally {
      this.closed = true;
      for (const p of this.pending.values()) {
        clearTimeout(p.timer);
        p.reject(new Error("MCP stream ended" + (this.error ? ": " + this.error : "")));
      }
      this.pending.clear();
      for (const waiter of this.waiters) waiter.reject(new Error("MCP stream ended"));
      this.waiters = [];
    }
  }
  async post(obj) {
    assert(!this.closed && !!this.endpoint, "MCP session not connected");
    const r = await fetch(this.endpoint, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(obj),
      signal: this.abort.signal,
      redirect: "error"
    });
    await r.text();
    assert(r.ok, "MCP POST HTTP " + r.status);
  }
  async request(method, params = undefined) {
    const id = ++this.next;
    const promise = new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error("MCP_TIMEOUT " + method + ". DO NOT retry mutating actions without state inspection."));
      }, RESP_TIMEOUT_MS);
      this.pending.set(id, { resolve, reject, timer });
    });
    const message = { jsonrpc: "2.0", id, method };
    if (params !== undefined) message.params = params;
    try {
      const [, data] = await Promise.all([this.post(message), promise]);
      return data;
    } finally {
      const item = this.pending.get(id);
      if (item) {
        clearTimeout(item.timer);
        this.pending.delete(id);
      }
    }
  }
  async initialize() {
    const r = await this.request("initialize", {
      protocolVersion: PROTOCOL,
      capabilities: {},
      clientInfo: { name: "agent-affinity-desktop-smoke", version: "0.1.0" }
    });
    await this.post({ jsonrpc: "2.0", method: "notifications/initialized" });
    return r;
  }
  async tools() {
    const r = await this.request("tools/list");
    assert(Array.isArray(r.tools), "Affinity MCP returned no valid tool list");
    this.allowed = new Set(r.tools.map(x => x.name));
    return r.tools;
  }
  async call(name, args = {}) {
    assert(this.allowed.has(name), "MCP tool not advertised: " + name);
    return this.request("tools/call", { name, arguments: args });
  }
  async preamble() {
    const result = await this.call("read_sdk_documentation_topic", { filename: "preamble" });
    const text = flatten(result);
    assert(!result.isError && text.length > 200, "MCP SDK preamble missing: " + text.slice(0, 300));
    return { chars: text.length, preview: text.slice(0, 300) };
  }
  close() {
    this.abort.abort();
    this.closed = true;
  }
}

async function main() {
  const cmd = process.argv[2] || "probe";
  if (cmd === "help" || cmd === "--help") {
    console.log("Affinity local MCP: probe | inspect | docs <topic> [substring] | run <path.js> --allow-write | render <document-uuid> <spread> <existing-parent/output.jpg>");
    return;
  }
  let s = await new Session().start();
  try {
    let init = await s.initialize();
    let names = (await s.tools()).map(x => x.name);
    let preamble;
    try {
      preamble = await s.preamble();
    } catch (first) {
      // Affinity 3.3.x can return "File not found" for the preamble
      // on a newly opened SSE stream. Reconnect once before any script.
      if (!String(first.message).includes("File not found")) throw first;
      s.close();
      s = await new Session().start();
      init = await s.initialize();
      names = (await s.tools()).map(x => x.name);
      preamble = await s.preamble();
    }
    if (cmd === "probe") {
      console.log(JSON.stringify({ status: "connected", protocol: init.protocolVersion,
        server: init.serverInfo, tools: names, preambleLength: preamble.chars }, null, 2));
      return;
    }
    if (cmd === "inspect") {
      const file = inside(ROOT, "scripts/affinity_mcp_inspect.js", true);
      const code = fs.readFileSync(file, "utf8");
      const r = await s.call("execute_script", { script: code });
      assert(!r.isError, "Affinity inspect script failed: " + flatten(r));
      console.log(JSON.stringify({ status: "read_only_inspected",
        console: flatten(r), contentKinds: r.content?.map(x => x.type) }, null, 2));
      return;
    }
    if (cmd === "docs") {
      const topic = process.argv[3];
      assert(topic && !topic.includes(".."), "Provide safe documentation topic");
      const r = await s.call("read_sdk_documentation_topic", { filename: topic });
      assert(!r.isError, "Affinity SDK topic unavailable: " + flatten(r));
      const data = flatten(r);
      assert(data.length && !data.startsWith("File not found"), "SDK topic not available: " + topic);
      const needle = process.argv[4];
      const lines = data.split("\n");
      let excerpt = data.slice(0, 40000);
      if (needle) {
        const matches = [];
        for (let i = 0; i < lines.length; i++) {
          if (!lines[i].toLowerCase().includes(needle.toLowerCase())) continue;
          const from = Math.max(0, i - 4);
          const to = Math.min(lines.length, i + 9);
          matches.push("@@ LINE " + (i + 1) + "\n" + lines.slice(from, to).join("\n"));
        }
        excerpt = matches.join("\n\n").slice(0, 40000);
      }
      console.log(JSON.stringify({ topic, chars: data.length,
        matches: needle ? excerpt.length : null, text: excerpt }, null, 2));
      return;
    }
    if (cmd === "run") {
      const script = process.argv[3];
      assert(process.argv.includes("--allow-write"),
        "Executing arbitrary script requires --allow-write; never run unattended.");
      const target = inside(ROOT, script, true);
      assert(fs.statSync(target).size <= MAX_SCRIPT && target.endsWith(".js"),
        "Script must be a small local .js");
      const code = fs.readFileSync(target, "utf8");
      const hash = createHash("sha256").update(code).digest("hex");
      const r = await s.call("execute_script", { script: code });
      assert(!r.isError && !flatten(r).startsWith("Error:"),
        "Affinity script failed: " + flatten(r).slice(0, 3000));
      console.log(JSON.stringify({ status: "script_returned", file: target, sha256: hash,
        console: flatten(r).slice(0, 10000) }, null, 2));
      return;
    }
    if (cmd === "render") {
      const uuid = process.argv[3];
      const index = Number(process.argv[4]);
      const output = inside(ROOT, process.argv[5] || "");
      assert(uuid && Number.isInteger(index) && index >= 0, "Require UUID and nonnegative spread");
      assert(output.toLowerCase().endsWith(".jpg"), "Use a .jpg output");
      assert(!fs.existsSync(output), "Refusing overwrite of screenshot");
      const r = await s.call("render_spread", { document_session_uuid: uuid, spread_index: index });
      assert(!r.isError, "Affinity render failed: " + flatten(r));
      const im = r.content?.find(x => x.type === "image");
      assert(im?.mimeType === "image/jpeg" && typeof im.data === "string",
        "No JPEG returned by Affinity render_spread");
      const bytes = Buffer.from(im.data, "base64");
      assert(bytes.length < 40_000_000 && bytes[0] === 255 && bytes[1] === 216,
        "Invalid JPEG bytes");
      fs.mkdirSync(path.dirname(output), { recursive: true });
      fs.writeFileSync(output, bytes, { flag: "wx" });
      console.log(JSON.stringify({ status: "rendered", output, bytes: bytes.length,
        sha256: createHash("sha256").update(bytes).digest("hex") }, null, 2));
      return;
    }
    throw new Error("Unknown command: " + cmd);
  } finally {
    s.close();
  }
}

main().catch(e => {
  console.error(JSON.stringify({ status: "blocked", error: String(e.message || e) }));
  process.exitCode = 2;
});
