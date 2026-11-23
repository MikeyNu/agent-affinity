# Working contract with MikeyNu/agent-mangaka

## Source of truth and handoff

Read https://github.com/MikeyNu/agent-mangaka (use the installed current
revision) before building an Affinity page. Keep Mangaka as the authority
for script, canon, character identity, references, scene geography,
camera pose, lighting, layout and acceptance. Affinity is a downstream
editor/publisher and must not change the upstream story unilaterally.

Required Mangaka references:
- `SKILL.md` and `references/intake-and-canon.md`;
- `references/spatial-continuity.md` and `references/art-direction.md`;
- `references/pages-and-lettering.md` and `references/compositing.md`;
- `references/visual-qa.md` and `references/evaluation-protocol.md`.

Canonical input mapping:

| Mangaka item | Affinity responsibility |
|---|---|
| `project.json` | Preserve story format, page direction, cast and environment IDs |
| `panels[].state` and `camera` | Protect geography, eyelines, light and anatomy when cropping |
| `panels[].status` and `qa` | Use accepted art bytes only; verify actual visual evidence |
| `layout.json` | Reproduce final panel mask, crop, border and balloon placement |
| `dialogue.json` | Copy exact line by ID; do not retype from memory |
| `qa/Pxxx.json` | Seven attestation checks from compositor, plus human/agent evidence |
| `render_manifest.json` | Preserve panel hashes, transforms, text and layer order |
| `page.svg` | Candidate editable interchange, needs Affinity import validation |
| `page.ora` | Layered OpenRaster archive for compatible tools, not assumed to import |
| `composite.png` | Pixel parity oracle |
| `lettering.png` | Transparent overlay parity oracle |

## Actual Mangaka CLI

Run from the installed Mangaka root and use the story's own workspace:

```sh
python scripts/mangaka.py validate "STORY/project.json" --files --out "STORY/work/validation.json"
python scripts/mangaka.py map "STORY/project.json" P001 --out "STORY/work/P001-map.svg"
python scripts/mangaka.py packet "STORY/project.json" P001 --files --out "STORY/work/P001-packet.json"
python scripts/compose_page.py "STORY/layout.json" "STORY/exports/page-001"
```

The compositor requires Pillow and a licensed TTF/OTF for lettering.
It writes five files and refuses unreviewed art, mismatched hashes,
missing dialogue, invalid crop/frame, text overflow and missing glyphs.
It may still produce a page that needs actual **visual review**.
Do not alter Mangaka's code to bypass a failed gate; fix the source
layout or art then regenerate under the correct upstream claim.

## Compositor acceptance specifics

Each panel has a `qa/P001.json` with `panel_id`, `status:
accepted`, `art_sha256`, nonempty `reviewed_by` and checks:

`identity`, `narrative`, `continuity`, `emotion`, `anatomy`,
`style`, `composition`.

A string `pass` is valid. For an irrelevant case a dictionary with
`status: not_applicable` and a specific `reason` may be used.
With visible subjects, the identity/emotion/anatomy checks must pass.
This record is a review attestation, not a substitute for original
reference comparisons. Some upstream project-level QA uses different
terminology like "space" or "acting"; do not rename compositor keys.

The render manifest records `ledger_sha256`, `layout_sha256`,
`page_id`, `panels` (ID, art hash, crop, uniform scale and offset),
`dialogue` (ID, kind, source exact text, font hash, tail information)
and `layers_bottom_to_top`. Validate all of them before import.

## Rules when editing

1. Exact dialogue is taken from the ledger, with stable IDs. No rephrasing,
   spell correction, auto-translation or duplicate lines.
2. Original art stays immutable. Local Affinity repairs become new
   derivatives in a named layer, with a new change record and visual QA.
3. Camera coordinates are **world-space**; layout and balloon coordinates
   are **page-space**; pixel crop is **source-image-space**. Never
   substitute one for another.
4. An approved panel is not an approved crop. Recheck actual placed panel
   and neighbor parity. Protected regions stay visible.
5. A changed source script, art file, review hash or layout invalidates
   corresponding native page approvals until recomposed and rechecked.
6. A source manifest text claim does not prove artistic quality or security.
7. Final editor save is tracked with file path and checksum. Include
   source digest in the publishing handoff to enable selective rebuilds.

## Integration readiness criteria

- Real Mangaka compositor five-file output passes the contract verifier.
- Affinity open/save test passes for the **specific chosen import path**.
- Accepted art can be traced to the original canonical reference and QA.
- Speech is attached to its correct character or narration source.
- Editor export matches the source layout or approved marked-up changes.
- The page can be reopened and remains editable.
- A visual reviewer evaluates the page and records evidence.
