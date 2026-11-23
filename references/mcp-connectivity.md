# Affinity MCP connectivity for Codex, Claude and Desktop Commander

## Why the transport matters

Affinity 3.3.x includes an optional local MCP server with tools such as
`execute_script`, `render_spread`, `render_selection` and the SDK
documentation methods. Claude Desktop can use Affinity's published
connector directly. An agent host must actually expose those tools before
the skill claims to run scripts.

The local MCP server requires **Affinity running** and the
**MCP Server** toggle enabled in the application's Settings under
**Model Context Protocol**. It is not enabled merely because
Canva.Affinity appears as an installed Windows app.

Important: the local server may use the legacy HTTP+SSE transport and
requires a preamble documentation read in the same MCP session before
`execute_script` is accepted. Repeated one-off HTTP requests with a new
session per call are not sufficient. A bridge must keep the session alive,
initialize it, read the preamble, and then run the script. Do not bypass
this authorization/protocol gate.

## Path A: first-party connector

For Claude Desktop, prefer the Affinity connector from Canva:
https://claude.com/marketplace/connectors/affinity-106b90 .

After the user enables the MCP server in the app, discover the exact
tool names in the current client. For a script:

1. Discover `read_sdk_documentation_topic` and `execute_script`.
2. Read documentation topic `preamble` through the same tool session.
3. Inspect current document and its session UUID with a read-only script
   using `Document.current` and `Document.all`.
4. Read only the specific SDK modules needed for the action.
5. Execute one small verified edit. No blind retry after timeout.
6. Render with `render_spread` or `render_selection` and inspect.
7. Save to a new versioned native master and reopen to test editability.

For read-only inspection use `scripts/affinity_mcp_inspect.js`. It prints
a JSON description through `console.log`. The SDK is beta, so confirm
the installed build before trusting a code example.

## Path B: via Desktop Commander on the authorized Windows PC

If Codex is unavailable, Claude lacks direct Affinity tools, or the
agent runs on another machine, use Remote Desktop Commander MCP to
select the authorized **online device**. Use that device's terminal
for the next checks, not the model's sandbox:

```powershell
node --version
node scripts/affinity_mcp_probe.mjs
```

This only checks the IPv6 loopback TCP socket at port 6767. Exit 0
proves that *a socket* answered, not that it was Affinity or that an MCP
handshake succeeded. Exit 2 means the socket was not available.
It does not enable the MCP server or change the user's settings.

If the user's host can connect to Affinity's legacy SSE MCP directly,
do so and run the same preamble, script and render sequence described
above. If the MCP protocol is not supported, use a separately reviewed
local bridge on the Windows machine. One available open-source option is
https://github.com/AOS-AgenticOS/pi-affinity-mcp . It advertises
support for Affinity's SSE transport and the preamble gate.

**Optional, only with explicit approval to install third-party code:**

```powershell
npm install -g github:AOS-AgenticOS/pi-affinity-mcp
pi-affinity-mcp --selftest
```

That external project is not vendored by this skill. Review its license,
source and current maintenance before installation. Its self-test
executes a read-only script in Affinity; verify its result, not simply
the executable's existence.

A separate MCP-capable client must actually call the bridge's tools.
Starting a server process through Desktop Commander does **not** by
itself connect that server to a ChatGPT or Claude conversation. The
agent must either have the bridge registered as an MCP connector in its
own host or use an authorized, tested local MCP client through the
Windows terminal. Verify this before asserting that it edited Affinity.

Do not expose an unauthenticated bridge on `0.0.0.0` or to the public
internet. Bind to local loopback by default and use explicit
authentication, firewall restrictions and reviewed configuration if
remote network access is genuinely required. Never paste credentials
into the chat transcript, repo or logs.

## Tool contracts

| Tool | Use | Required evidence |
|---|---|---|
| `list_sdk_documentation` | Discover SDK module names | Actual topic list |
| `read_sdk_documentation_topic` | Read `preamble`, signatures | Session-specific result |
| `execute_script` | Run reviewed JS in Affinity | Actual log/result and changed document |
| `render_spread` | Inspect current spread | Actual returned image with page ID |
| `render_selection` | Inspect selected object | Actual returned image and selection context |
| `list_library_scripts` | Find reusable scripts | Actual titles |
| `save_script_to_library` | Save tested script if requested | Explicit request plus successful app result |

Save actual image outputs to authorized local project paths when using
a host that supports that workflow. Keep the original generated artwork
out of conversation messages per the user's preference.

## Common faults

| Error | Diagnosis |
|---|---|
| `ECONNREFUSED ::1:6767` | App not running, server disabled, or different version |
| SDK preamble not read | Read `preamble` in this exact MCP session |
| Script timed out | It may have changed the document; inspect before retry |
| `NOT_ALLOWED` on a file path | Affinity's script filesystem permission or scope |
| Tool absent in host | Configure/connect actual MCP client or use supported GUI route |
| Shell works but no GUI | A shell is not a screenshot or mouse tool |
| Installed legacy Affinity 2 | Wrong app generation, no Affinity 3 scripting |
| Rendered art differs | Visual parity fails even if script returned success |

## References

- Affinity SDK 3.3.3, beta: https://sdk.affinity.studio/
- Official scripting: https://www.affinity.studio/features/scripting
- Official crop marks script: https://www.affinity.studio/help/scripting-tutorial-crop-marks/
- Canva's Claude connector: https://claude.com/marketplace/connectors/affinity-106b90
- Optional community bridge: https://github.com/AOS-AgenticOS/pi-affinity-mcp
