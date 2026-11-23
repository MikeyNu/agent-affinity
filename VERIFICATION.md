# Verification record

## 2026-11-23, Windows workstation

This is an evidence-bound report for the first published commit of
agent-affinity. It is not a claim that finished comic artwork has passed
native Affinity visual QA.

| Check | Evidence | Status |
|---|---|---|
| GitHub source read | Mangaka main repository, actual scripts and reference docs | PASS |
| App package | Windows AppX reports Canva.Affinity 3.3.3.5004 | PASS |
| Device route | Authorized Remote Desktop Commander Windows shell/filesystem access | PASS |
| Core contract tests | 35 Python synthetic validation and failure scenarios | PASS |
| Real Mangaka integration | 3 scenarios using the actual Mangaka compositor on synthetic panel geometry | PASS |
| Package/docs tests | 5 source structure, links, safety and instruction tests | PASS |
| Total Python suite | 43 tests, 0 failures, Python 3.14 | PASS |
| JavaScript syntax | 3 bundled scripts checked by Node.js | PASS |
| App process and MCP | No running Affinity process; IPv6 loopback 6767 refused the connection | NOT AVAILABLE |
| Native scripting inside Affinity | No live session to run code | NOT TESTED |
| Native SVG import, text and mask editability | Needs actual Affinity opening and visual inspection | NOT TESTED |
| Affinity native master save/reopen | Needs app access and a disposable test document | NOT TESTED |
| Final PDF/PNG export and visual parity | Needs app access, export and source comparison | NOT TESTED |
| GitHub Actions | Four jobs rejected before any runner started due to an account billing lock | BLOCKED |

### Exact test commands on the Windows workstation

From the local repository directory:

```powershell
$env:MANGAKA_REPO = "C:\Users\USER\AppData\Local\Temp\agent-affinity-mangaka-integration"
py -3.14 -m unittest discover -s tests -v
node --check scripts/affinity_selection_audit.js
node --check scripts/affinity_mcp_inspect.js
node --check scripts/affinity_mcp_probe.mjs
node scripts/affinity_mcp_probe.mjs
```

The Mangaka integration clone is a temporary read-only test fixture,
not a permanent dependency or modification of the active Gatsheni
workspace. Tests created small synthetic colored panel graphics in
temporary directories and removed them after completion. No
generated comic artwork was embedded in a chat.

### GitHub Actions blocker

The run was started by the initial push:

https://github.com/MikeyNu/agent-affinity/actions/runs/45240245821

All four matrix jobs terminated before runner allocation and reported:

> The job was not started because your account is locked due to a billing issue.

This is not an indication of failed source or compositor tests. Hosted
CI cannot turn green until the GitHub account billing/Actions restriction
is resolved. Run the local commands above in the meantime, and do not
claim a hosted CI pass that did not occur.

### Remaining live Affinity acceptance steps

1. Launch the actual Affinity by Canva application on the authorized PC.
2. Enable its MCP Server in Settings > Model Context Protocol, if the
   user authorizes local scripting access, and verify the local endpoint.
3. Connect an actual host MCP client, read SDK preamble in the same
   session and execute the bundled read-only inspection script.
4. Create a disposable two-panel document with separate text, border,
   clip and artwork layers. Save and reopen its native master.
5. Import a verified real Mangaka `page.svg`; inspect SVG clip paths,
   font mapping, nested groups, and independent editability against
   `composite.png`. Reconstruct natively if needed.
6. Export PNG and PDF from Affinity; reopen and inspect dimensions,
   color, lettering, transparency, layering and source parity.
7. Test script failures, lost connections, missing links and resume
   checkpoints without touching active story assets.
8. Review one authorized Gatsheni page against canonical character
   sheets, scene maps, dialogue and neighboring panels at reading
   size and high-detail crops. Record actual evidence in the project.

Until these have evidence, **the published skill is structurally and
integration tested, but native Affinity operations are not yet
end-to-end validated**. Use the skill with this explicit boundary.


## 2026-11-23, later live Affinity MCP verification

**The user enabled Affinity's MCP server after the first record above.**
The earlier `NOT AVAILABLE` connectivity result is now superseded for
this Windows device, without changing the truth of the earlier run.

| Live check | Actual result | Status |
|---|---|---|
| Windows process | Running `Canva.Affinity 3.3.3.5004` | PASS |
| Local SSE | `http://[::1]:6767/sse`, protocol `2025-11-25` | PASS |
| SDK preamble | Read 6,010 characters in the same session | PASS |
| MCP tool discovery | 11 tools, including `execute_script` and `render_spread` | PASS |
| Read-only document inspection | Reported no document before test | PASS |
| Native document creation | Disposable 640 x 960 pixel master saved to `.af` | PASS |
| Editing and labels | Two vector rectangles, one native text frame; persisted `userDescription` IDs | PASS |
| Native file round trip | Closed and reopened; three objects editable and unlocked with exact text | PASS |
| App renderer | `render_spread` returned a local JPEG; no image sent to chat | PASS |
| Plain native export | 640 x 960 PNG, one-page PDF; text `Hello from Affinity.` was extractable | PASS |
| Real Mangaka compositor | Created 5-file export from two synthetic approved panel graphics | PASS |
| Compositor validation | Contract passed, source hashes and dialogue `D1` matched | PASS |
| SVG import into Affinity | 20 separate editable objects, including panel images, borders and text | PASS |
| SVG import native round trip | All 20 nodes remained editable with identical hierarchy and descriptions | PASS |
| Imported dialogue | `We move at ` + `sunrise.` reconstructed the exact source utterance | PASS |
| Default PNG preset | Produced 1600 x 1100 from an 800 x 550 source | DEFECT FOUND |
| Explicit `Size` export | PNG returned 800 x 550 after passing `new Size(800,550)` | DEFECT FIXED |
| Exported PDF | One page, extracted text reconstructs `We move at sunrise.` | PASS |
| Geometric parity | Source vs exact-size Affinity PNG RGB MAE approximately 3.4997/255 | MEASURED |
| Significant differences | 3.96% of pixels had a channel difference greater than 12 | MEASURED |
| Full user chapter quality | No Gatsheni production assets or chapter used in this smoke test | NOT TESTED |
| Full hosted CI | GitHub account billing issue prevented runner startup | BLOCKED |

### Important SDK conclusions

- Native labels require `node.userDescription`. The attempted
  `node.name` assignment did not work in this installed SDK.
- The Affinity `FrameTextNode` supports `node.setText(...)`. The
  full text bounding box must be inspected to catch overflow.
- `doc.saveAs`, `doc.save`, `doc.close` and `Document.load`
  completed on **disposable** documents and preserved editability.
- An imported SVG sentence can be split into separate `ArtTextNode`s.
  The original Mangaka dialogue ledger is authoritative.
- Use `FileExportOptions.createWithPresetName('PNG')`,
  `FileExportArea.createForWholeDocument()` and the fourth
  `new Size(width,height)` parameter in `doc.export`. Reopen the
  actual output to verify pixel dimensions.
- The repo now provides `scripts/affinity_mcp_cli.mjs`, a
  zero-dependency local MCP client, with live-tested handshake,
  preamble recovery, read-only inspection, script execution,
  SDK documentation access and render-to-local-file.
- This tests the transport and source interchange, **not** complete
  application-level masking, complex lettering, human visual review,
  printer profiles, or chapter-length production on Gatsheni.

### Smoke artifacts

All synthetic outputs and scripts live in the **ignored** folder
`C:\Users\USER\Desktop\agent-affinity\work\affinity-live-smoke`.
They include `affinity-smoke-001.af`,
`mangaka-svg-import.af`, `mangaka-affinity-export-exact.png`,
`mangaka-affinity-export.pdf` and the synthetic source fixture.
Do not commit these screenshots, images, PDFs, document masters, or
system fonts. The test did not modify the active Gatsheni workspace.

The skill's full operation sequence and the non-default export fix are
documented in [references/live-affinity-mcp.md](references/live-affinity-mcp.md).


### Disposable-session cleanup recovery

The first cleanup script successfully closed one owned disposable document,
then raised `Error: DISPOSED` because it tried to read
`doc.sessionUuid` **after** `doc.close()`. The agent did not blindly
rerun the write. It inspected the live `Document.all` list, confirmed
only the second owned test document remained with no unsaved changes,
corrected the script to cache the UUID before closing, and then closed
that document successfully. No other documents remained open and
no user-owned document was changed. The regression is documented in
`references/recovery.md` and `references/live-affinity-mcp.md`.
