# Agent Affinity

A portable, agent-readable skill for Affinity by Canva comic production and
Manga/Manhwa publishing, designed to work alongside
[agent-mangaka](https://github.com/MikeyNu/agent-mangaka).

## What it does

- Routes Codex, Claude and other AI agents to an **authorized Windows device**
  using real available desktop and MCP tools.
- Explains Affinity UI use, native document structure, editable panel assembly,
  masks, lettering, print/digital export, and safe revisions.
- Checks Mangaka compositor handoffs (source art hashes, 7 acceptance gates,
  panel geometry, source dialogue, ORA/SVG/PNG containers and layer order).
- Creates a deterministic audit/handoff JSON for downstream editors.
- Provides an official-SDK-based **read-only** selection audit example.
- Provides automated contract tests and a manual live Affinity test protocol.

It is an **agent skill**, not an Affinity plugin that silently edits documents.
Every Affinity write requires a connected/authorized device and a supported
execution surface. File and unit-test passes do not imply live UI tests passed.

## Install

Clone this repo and point your agent's skill loader at its `SKILL.md`.
Keep the Mangaka skill installed separately. Do not copy or overwrite Mangaka
source files and do not place the skill inside the active Gatsheni queue.

For a desktop project using Affinity, the agent should read both skill files,
[references/desktop-routing.md](references/desktop-routing.md), and
[references/mcp-connectivity.md](references/mcp-connectivity.md).

## Quick validation

Python 3.10+; no non-stdlib dependencies for the contract checker or tests.

```sh
python -m unittest discover -s tests -v
python scripts/affinity_contract.py verify --layout /path/to/story/layout.json --exports /path/to/story/exports/page-001
python scripts/affinity_contract.py handoff --layout /path/to/story/layout.json --exports /path/to/story/exports/page-001 --out /path/to/story/publishing/page-001-affinity-handoff.json
python scripts/affinity_contract.py native --handoff /path/to/page-001-affinity-handoff.json --native /path/to/page-001.af --deliverable /path/to/final.png
```

The first command tests **synthetic fixtures** only. The second checks
real exported page artifacts. The last checks saved file existence and SHA,
and does not certify that Affinity can reopen or edit the native file.

## Import strategy

Mangaka exports `page.svg`, `composite.png`, `lettering.png`,
`page.ora` and `render_manifest.json`. The SVG is a useful import candidate;
the PNG is the visual oracle; the ORA is retained as a layer archive for
compatible software. **OpenRaster import into Affinity is not assumed**.
After opening the SVG in Affinity, check the layers, masks, text, alignment,
transparency and visual parity. If import loses required editability,
assemble the same source panels in a new Affinity document and preserve
native text and masks.

## Execution paths

- Affinity native MCP, if connected and configured, is the best path for
  scripts and render inspection. Never invent MCP tool availability.
- Codex local desktop access is valid if the agent genuinely has that
  device and necessary UI tools.
- **Desktop Commander MCP is mandatory fallback** when local Codex access
  is absent and an authorized Windows device is connected. It provides
  shell and filesystem access, but it does not by itself grant arbitrary
  screenshot, mouse or keyboard control. Use verified UI automation or
  Affinity's native scripting/MCP surface before claiming an edit.
- If no machine access is possible, produce the validated manifest, layout
  plan and a resumable handoff. No fake click/screenshot/commit claims.

See [VERIFICATION.md](VERIFICATION.md) for the dated test record, the
GitHub Actions billing blocker and native Affinity smoke tests that
still need an application session. On Windows, use `py -3.14` when the
`python` alias points to the Microsoft Store. When the layout uses an
installed Windows font outside its project directory, explicitly pass
`--font-root C:/Windows/Fonts` to the contract commands.

## Live MCP tested on Windows

Affinity 3.3.3.5004 was tested through the authorized Desktop Commander
machine using the built-in Node.js MCP client, with no additional packages.
Once the user's Affinity MCP Server is enabled, agents can run these from
this repo on the Windows desktop:

```powershell
node scripts/affinity_mcp_cli.mjs probe
node scripts/affinity_mcp_cli.mjs inspect
node scripts/affinity_mcp_cli.mjs docs document.js createFromOptions
node scripts/affinity_mcp_cli.mjs render DOCUMENT_UUID 0 work/inspect.jpg
```

See [the live MCP runbook](references/live-affinity-mcp.md) for authorized
script execution, object naming, native save/reopen, Mangaka SVG import and
mandatory explicit pixel dimensions on PNG export.

## Evidence levels

| Level | Claim justified |
|---|---|
| Static docs and Python tests | Contracts and synthetic failure handling |
| Real Mangaka export | Correct bytes/structure for that export |
| Native Affinity smoke test | Specific tested import/save/export operations |
| Visual QA | Observed story, art, typography and layout quality |
| Complete production chapter test | Production-level workflow on that chapter |

See [references/evaluation.md](references/evaluation.md) for scenarios and
[references/qa-and-publication.md](references/qa-and-publication.md) for gates.

## Licensing and safety

This skill contains original instructions and tiny synthetic test assets.
Do not commit client artwork, user project data, fonts without rights, secret
tokens, cached login state or real generated comic panels to this repository.
The user workspace remains the source of truth.

Current Affinity SDK reference: https://sdk.affinity.studio/ .
Scripting is beta and legacy Affinity V2 is not the target.