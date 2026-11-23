# Page acceptance, visual QA and publication

## Four evidence tiers

**Static**: manifests, file structure and hashes are valid.
**Application**: the actual Affinity app performed import, edits,
native save/reopen and exports.
**Visual**: a reviewer inspected the relevant page at intended reading
size plus native crops against originals.
**Production**: cross-page/cross-chapter reading and repeatability
are verified on a real manuscript.

Never merge these into one "passed" badge. A checker cannot know whether
a character actually looks correct; a screenshot cannot prove a linked
resource will survive transfer; a saved file alone cannot prove editability.

## Gate matrix

| Gate | Must demonstrate | Failure example |
|---|---|---|
| Identity | Canonical sheet parity, scars, faces, costumes, side | Two unrelated characters become the same face |
| Narrative | Story beat and correct owner of action/speech | Wrong character speaks or a reveal is early |
| Continuity | World position, axis, lighting and prop persistence | Reverse shot teleports the background |
| Emotion | Intended inner/outer acting | Unmotivated smiling response |
| Anatomy | Correct hands, limbs, overlap, contact | Extra finger or moved injury |
| Style | Approved strokes, color, material and tone | Glossy generic image replaces approved ink |
| Composition | Clear subject, crop, panel order and spacing | Hand/action cropped by clipping mask |
| Lettering | Exact ledger text, font, tail, legibility | Wrong speaker, dropped line, overflow |
| Native/editable | Open/reopen, live objects, non-destructive layers | Flattened page masquerades as a master |
| Publication | Correct page count, resolution, ICC and files | Printed trim cuts a caption |

Each applicable gate is `pass`, `repair` or `blocked` with observations
and evidence path. A `not_applicable` decision needs a specific reason.
The upstream Mangaka attestation keys match its compositor contract;
the last three gates are downstream additions.

## Procedure

1. **Source check:** verify compositor output and original Mangaka
   `project.json`, art IDs, references, source plot and dialogue IDs.
2. **Native inspection:** open the exact versioned master. Show layer
   tree, hidden groups, masks, symbols, independent text and links.
3. **Full-page reading:** read without text (flow, acting, reveal),
   then text only (exact words and speaker), then combined page.
4. **Micro-inspection:** zoom to faces, hands, critical props, gutters,
   joins, lettering halos and tails. Compare to reference originals
   and neighboring accepted panels.
5. **Sequence inspection:** verify scene geography and persistent
   changes before and after each edited page. A crop-only change can
   still affect pacing and speaker attribution.
6. **Export audit:** reopen output PNG/PDF or segmented scroll. Inspect
   profile, dimensions, alpha, page order, text and segment boundaries.
7. **Reopen audit:** close and reopen native file after save. Confirm
   editable masks, native text and external resources still work.
8. **Sign-off:** include reviewer type (AI, human), evidence files,
   target build, source hash and any limitations. AI review is never
   mislabeled as human approval.

## Evidence template

Save page-local `qa/page-001-affinity-review.json`:

```json
{
  "schema_version": 1,
  "page_id": "PAGE1",
  "source_handoff_sha256": "<real sha>",
  "affinity_version": "<observed version or unknown>",
  "route": "affinity-mcp|codex-desktop|desktop-commander|offline",
  "native_file": "<path if actually saved>",
  "reviewer": "<agent id or person>",
  "review_type": "agent",
  "inspection": {
    "page_at_reading_size": "<evidence reference>",
    "face_and_hand_crops": ["<path>"],
    "neighbors": ["<page id>"],
    "native_reopen": "<observed pass/fail/not_tested>",
    "dialogue_audit": "<actual evidence>",
    "export_reopen": "<observed pass/fail/not_tested>"
  },
  "gates": {
    "identity": "pass", "narrative": "pass",
    "continuity": "pass", "emotion": "pass",
    "anatomy": "pass", "style": "pass",
    "composition": "pass", "lettering": "pass",
    "native_editable": "pass", "publication": "pass"
  },
  "defects": [],
  "status": "accepted"
}
```

This example is a **schema illustration**, not evidence of a real pass.
Never paste placeholder approvals into actual production files.
Status can be `accepted` only if every applicable gate has real
evidence. Never automatically fill these passes from CLI checks.

## Publishing safety

- Keep source panel art, source compositor exports and native masters
  separate. Export to a staging directory, compare, then promote
  atomically if the target is unchanged.
- Never overwrite a current approved chapter without matching its
  revision and without a recovery copy.
- Reverify printer/digital platform specs at publication time. Export
  requested single pages, spreads or scrolling segments intentionally.
- Inspect all chapter pages at least once in final reading order.
- Update `HANDOFF.md` with last approved page, next action,
  outstanding QA, reference hashes and native file path.
