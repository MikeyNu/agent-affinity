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
