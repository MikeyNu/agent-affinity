# Live Affinity MCP runbook for multi-agent comic production

This runbook was tested on Windows with **Affinity by Canva 3.3.3.5004**
and the installed MCP server. Read it together with `SKILL.md` and the
current `agent-mangaka` skill. It describes a tested integration route,
not permission to edit arbitrary open documents.

## Access when Codex is unavailable

An agent with direct Affinity MCP tools should use those first. Otherwise,
including Claude agents without direct app tools, use the **authorized**
Windows workstation through Desktop Commander MCP:

1. Discover `list_devices` and choose the authorized online Windows device.
   Never reuse a remembered device ID without discovery.
2. Use `get_config` to verify Windows, PowerShell and allowed project paths.
3. Locate the agent-affinity checkout on that device.
4. Run the bundled local MCP client through `start_process`. It needs
   Node.js 22+, an already-running Affinity 3 app, and MCP Server enabled.
5. If the MCP bridge cannot connect, leave a checkpoint; do not claim
   GUI work from shell access or install other software without approval.

From the installed agent-affinity repo root on the Windows machine:

```powershell
node scripts/affinity_mcp_cli.mjs help
node scripts/affinity_mcp_cli.mjs probe
node scripts/affinity_mcp_cli.mjs inspect
node scripts/affinity_mcp_cli.mjs docs document.js createFromOptions
node scripts/affinity_mcp_cli.mjs render DOCUMENT_UUID 0 work/check.jpg
node scripts/affinity_mcp_cli.mjs run work/approved-script.js --allow-write
```

The renderer writes JPEG files locally, not in chat. The destination's
parent directory must exist; existing outputs are never overwritten.

The `probe` command performs an actual MCP handshake, reads the SDK
preamble, and lists current tools. A raw socket probe alone is insufficient.
The client binds to local loopback, currently `http://[::1]:6767/sse`,
uses protocol `2025-11-25` and keeps one SSE session alive per operation.
If a fresh session returns `File not found` for the SDK preamble, it
reconnects **once before executing scripts**. Never blindly retry a
write after an unknown timeout; read app state first.

The `run` command accepts only a local JavaScript file within the
skill checkout and requires `--allow-write`. Inspect and authorize
the script before execution. It can modify the current Affinity
document. Do not use it on user-owned masters without the project's
single-writer claim. Use `inspect` for routine read-only state.

**The client does not automatically attach an MCP server to Claude or
Codex.** Desktop Commander runs the client on the authorized Windows
machine and returns the script result through the terminal. Agents
cannot pretend their host exposes Affinity's native tool namespace.

## Tested SDK patterns

The APIs below were verified in the actual running Affinity 3.3.3.5004
application and cross-checked against its SDK documentation:

- `const { Document, NewDocumentOptions } = require('/document.js')`;
  configure `NewDocumentOptions.createDefault()` with pixel units and
  create via `Document.create(opts)`.
- `Document.current`, `doc.sessionUuid`, `doc.currentSpread.children.toArray()`
  and `node[Symbol.toStringTag]` expose the real document and node types.
- Use `node.userDescription = 'P001_ART'` for editable, persistent layer
  names. **Do not use `node.name`**, which did not name the tested nodes.
- Add vector shapes with `AddChildNodesCommandBuilder` and
  `ShapeNodeDefinition`. Always `setInsertionTarget(doc.currentSpread)`.
- Set solid fill via `node.brushFillDescriptor =
  Colour.createRGBA8({r:57,g:79,b:105,alpha:255})`, not an undocumented
  `brushFill` property.
- Add independent lettering using `StoryBuilder` and
  `FrameTextNodeDefinition.createFromStoryBuilder`. Verify overflow
  against the full actual text visible box, then call `node.setText(...)`
  if the approved text changes. Read the exact upstream ledger.
- Save via `doc.saveAs(path)` or `doc.save()`. For disposable test
  documents with no unsaved changes, `doc.close()` and
  `Document.load(path)` confirmed editable shapes, layer names and text
  survive the native round trip.
- For read-only visual evidence, `render_spread` returns a JPEG of up to
  approximately 1024 pixels on the longest edge. Keep high-resolution
  export checks independent of this inspection render.

## Mandatory PNG export size control

The SDK returns available presets with
`FileExportOptions.allPresetNames`. The tested names include `PNG`
and `PDF (digital - high quality)`.

**Do not rely on the PNG preset's default dimensions.** When a Mangaka
`800 x 550` SVG page was imported into Affinity and exported with
default PNG options, Affinity produced `1600 x 1100`. This was found
and repaired in the live regression test.

The following tested pattern requests exact pixel dimensions:

```javascript
const { Document, FileExportOptions, FileExportArea } =
  require('/document.js');
const { Size } = require('/geometry.js');
const doc = Document.current;
const preset = FileExportOptions.createWithPresetName('PNG');
const area = FileExportArea.createForWholeDocument();
doc.export(
  'C:/AUTHORIZED/WORKSPACE/publishing/page-001.png',
  preset,
  area,
  new Size(800, 550)
);
```

Replace the example destination with an approved page-local path
and the dimensions from the validated Mangaka layout manifest.
`Document.export(...)` returning a result is not sufficient:
reopen the output with an independent decoder, inspect dimensions,
alpha/profile, actual lettering, mask boundaries and reading size.
For print PDF, use the publisher's required *physical page size*
and bleed. PDF presets are not interchangeable with digital PNG
pixel dimensions.

## Mangaka compositor SVG result

The Mangaka `compose_page.py` output bundle contains:
`composite.png`, `lettering.png`, `page.svg`, `page.ora` and
`render_manifest.json`. Check the source SHA-256 and review records
before starting Affinity. `page.svg` is the preferred tested import
candidate; `page.ora` remains a separate archive, not an assumed
Affinity input.

The synthetic, two-panel actual compositor page imported to Affinity
with 20 nodes: two `ImageNode`s, two `ArtTextNode`s, three
`PolyCurveNode`s, two `ShapeNode`s and 11 group/container nodes.
All 20 survived native `.af` save/reopen and reported editable.

One speech line was imported as two separate native text objects:
`"We move at "` and `"sunrise."`. Their concatenation preserved
the exact original ledger text `"We move at sunrise."`. In a real
chapter, **do not infer that every utterance is one text object**.
Reconstruct against the immutable source dialogue ledger, check
reading order and whitespace, and re-verify every scripted utterance.

The exact-size PNG export measured 800 x 550 pixels with mean absolute
RGB difference of approximately 3.50/255 from the compositor source,
and 3.96% of pixels having a channel difference greater than 12.
These are observations for one synthetic test, **not global acceptance
thresholds**. Rendering differences are not proof that a page is
narratively or artistically correct. Compare actual high-resolution
crops and styled lettering before approving production art.

## Recovery and safety

- Never operate on active Gatsheni artwork simply to prove the skill.
  Use a disposable document under `work/`, excluded from Git.
- Before every write, verify document `sessionUuid`, source hashes,
  exclusive page claim and output target. Save numbered native revisions.
- Never force a GUI window to close. Only close test documents created
  by the current session, after confirming `needsSaving` is false.
  Capture `doc.sessionUuid` **before** `doc.close()`; afterward the
  SDK handle is disposed and reading its properties throws `DISPOSED`.
  This was discovered and repaired in the disposable cleanup test.
- A failed SDK call can partially change the native document. Inspect
  actual node state before any retry.
- Never publish rendered images in chat. Save local paths and checksums.
- Keep the project's original style, camera geometry, identity, masks,
  panel traversal and exact speech under Mangaka's existing QA gates.
- Report the Affinity build, source revision, code and exports tested,
  actual evidence tier, unresolved faults and resumable next action.

Evidence for this exact live run is in [VERIFICATION.md](../VERIFICATION.md).
