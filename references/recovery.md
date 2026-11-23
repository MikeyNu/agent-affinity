# Recovery and non-destructive repair

## General rules

A failure is a state to investigate, not a reason to skip QA. Use a
bounded retry with a changed diagnosis. Never delete prior accepted
assets, zero-out stale manifests or overwrite active agent files.

| Incident | Investigate | Recovery |
|---|---|---|
| Affinity unavailable | Installed package, app version, permissions, device | Offline handoff or use authorized app route |
| Codex cannot see Windows | Tool catalog, devices | Discover Desktop Commander MCP |
| Desktop Commander terminal only | Actual GUI/MCP availability | Structural checks; hand off native editing |
| Affinity native MCP missing | In-app MCP settings, host tool list | Scripting Studio via verified UI or handoff |
| Scripting API changed | Installed SDK, tutorial, logs | Pin version and revise script on copy |
| Missing font/glyph | Font path, rights, shaping | Fix font or composition upstream and rerun |
| SVG imported flat | Layer types, clip paths, fonts | Rebuild from approved PNG and native shapes |
| ORA cannot open | Import support | Retain ORA for other editors; use SVG/PNGs |
| Wrong balloon speaker | Ledger IDs and tails | Correct lettering only, verify entire page |
| Mask hides face | Source critical region, crop | Reframe clip or choose approved art variation |
| Native file corrupted | Version history, source digest | Reopen earlier version, rebuild derivative |
| Linked art missing | Resource Manager paths, project move | Relink same SHA-verified source file |
| Export altered appearance | Output profile, font, rasterization | Change export options, compare new output |
| App hangs | Running process, unsaved changes | Check status before terminating; recovery copy |
| Hash drift | Source revision, concurrent agent | Invalidate downstream approval, recompose |
| Timed-out remote tool | PID or call_id | Poll tool result, no duplicate execution |

## No-blind-retry policy

When any mutating action is uncertain, check the app/native state and
operation log first. Before retrying a new edit, compare source and
target hashes. Retry only if the last action is confirmed not applied,
or create a new idempotent derivative plan. A partial native save can
have a newer timestamp while being corrupt; reopen verification is
required, not just a file-exists check.

## When to escalate

A critical story/identity error requires upstream Mangaka review.
A legitimate but unsupported vector text or custom balloon requires
a capable editor or verified workaround; do not replace with an
unapproved generic form. A connection/access gap requires the operator
to restore authorization, not an unsafe alternate login route.

## Required interrupted-work handoff

Capture: project, chapter, page, active source hashes, current master
path and byte hash, last confirmed operation, last uncertain action,
running PID or job ID, open issues, next safe test, and owner lease.
Never claim completed production without actual exported and
reopened files.
