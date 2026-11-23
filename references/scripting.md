# Affinity scripting and native MCP

## Version and evidence

As of 23 November 2026, the current unified Affinity by Canva supports
in-app **JavaScript scripting**. The public SDK documentation currently
lists version 3.3.3 and explicitly calls the API **beta**. API examples
and runtime behavior may change. Legacy Affinity V2 does not support the
same scripting feature. Confirm the actual local installed version.

Sources:
- https://sdk.affinity.studio/
- https://sdk.affinity.studio/3.3.3/js/
- https://www.affinity.studio/help/scripting-tutorial-crop-marks/
- https://www.affinity.studio/features/scripting
- https://www.affinity.studio/blog/affinity-automation-scripting-claude

## Preferred native programmatic path

If the authenticated AI host exposes **Affinity MCP**, use tool discovery
and prefer `execute_script` for edits and `render_spread` /
`render_selection` for observation. Additional reference tools reported
by Anthropic's official marketplace connector include
`list_sdk_documentation`, `read_sdk_documentation_topic`,
`search_sdk_hints`, `list_library_scripts`, `save_script_to_library`.
These are capabilities of that connector, **not promises that the
current ChatGPT or Codex session contains those exact tools**.

The Affinity MCP is a local service. With Claude Desktop, the documented
connection requires Affinity running, MCP configured in Affinity
Settings, and an authenticated account. Other hosts should inspect
their own connection and never fabricate remote endpoints or auth.

When Affinity MCP is absent, use the Scripting Studio in Affinity
through an authorized GUI route. Desktop Commander alone can write
`.js` files and launch programs, but it cannot click Execute inside
a GUI without an actual tested UI interface. Do not confuse Node
`require` with the Affinity built-in module resolver: Node cannot
execute `require('/document.js')`.

## Supported SDK concepts from official tutorial

The official crop-marks tutorial uses:

```javascript
'use strict';
const { Document } = require('/document.js');
const doc = Document.current;
const selected = doc.selection.nodes.toArray();
const bounds = selected.map(node => node.getSpreadVisibleBox());
```

It also illustrates
`AddChildNodesCommandBuilder`, `ContainerNodeDefinition`,
`PolyCurveNodeDefinition`, `CompoundCommandBuilder`,
`doc.executeCommand(command, preview)` and
`doc.clearPreviews()`. Do not invent undocumented APIs for page export,
image placement, clipboard, native save, filesystem access, or script
execution through Windows CLI. Consult the installed SDK reference
and versioned declarations first.

Bundled `scripts/affinity_selection_audit.js` is a **read-only**
example using the documented selection APIs. It reports selected
object bounds for a simple smoke test; it does not create pages or
change the document. Runtime success requires an actual Affinity run
and recorded result. A `node --check` pass only checks JavaScript
syntax, not Affinity module availability.

## Live Windows SDK compatibility verified

A real Windows 3.3.3.5004 session confirmed `Document.create`,
`doc.saveAs`, `doc.close`, `Document.load`, `doc.save`,
`ShapeNodeDefinition` and `FrameTextNodeDefinition`, and verified
that `node.userDescription` persists as a layer label across native
save/reopen. `node.name` did not label the tested objects and must
not be used for that purpose. `TextNode.setText(str)` is supported.

For exact-size PNG export use `FileExportArea.createForWholeDocument()`
and pass `new Size(width,height)` from `/geometry.js` as the fourth
argument to `doc.export`. Default PNG options doubled the dimensions
of a Mangaka SVG sample; see [the live test](live-affinity-mcp.md).

## Security and idempotency

Treat AI-written scripts as potentially unsafe code. Script permissions
for filesystem/network operations must stay at the minimum scope.
Review scripts before running; disallow unapproved filesystem,
network, process, clipboard and account operations. No open internet
access or external upload is required for basic page composition.

For a modifying script:
1. Read current source manifest revision and native master ID.
2. Check the intended page ID and exclusive writer lease.
3. Use a unique operation ID and a dry-run summary.
4. Confirm target layers by stable names/IDs, not fuzzy selection.
5. Build changes as one logical undo transaction where supported.
6. Commit only to a versioned derivative.
7. Render and compare before/after; perform a source-text audit.
8. Save and reopen; verify exact document/layer state.
9. Write an operation log with actual success/error and timestamps.
10. If any step fails, preserve the earlier master and stop. No blind
    retry of partly applied operations.

New native script functions must be proven against the installed
SDK and live UI before being promoted from experiment to production.
Prefer small, reversible scripts to a single giant automation with
unrecoverable partial edits.

## Upgrade protocol

On any new Affinity build, repeat the read-only script, SVG/font import,
mask/group integrity, native save/reopen and PNG/PDF export smoke tests.
If SDK behavior changes, pin the tested version in the handoff and
keep the old master readable. Avoid automatic migration on user art.

Anthropic connector listing:
https://claude.com/marketplace/connectors/affinity-106b90 .
