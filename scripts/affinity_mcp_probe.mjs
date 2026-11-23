#!/usr/bin/env node
// Read-only local IPv6 loopback check for Affinity's MCP listening socket.
// Success means a TCP socket is reachable, not that MCP or scripting works.
import net from "node:net";

const socket = net.createConnection({ host: "::1", port: 6767 });
let finished = false;
function end(status, detail, exitCode) {
  if (finished) return;
  finished = true;
  console.log(JSON.stringify({
    status, detail, host: "::1", port: 6767,
    mcpHandshakeVerified: false,
    scriptingVerified: false
  }));
  process.exitCode = exitCode;
  socket.destroy();
}
socket.setTimeout(2000);
socket.once("connect", () => end("socket_reachable",
  "Check actual Affinity MCP session, SDK preamble and tool list separately", 0));
socket.once("timeout", () => end("socket_unavailable",
  "No timely local MCP socket response", 2));
socket.once("error", error => end("socket_unavailable",
  String(error.code || error.message), 2));
