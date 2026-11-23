# Test and evaluation protocol

## Commands

```sh
python -m unittest discover -s tests -v
python scripts/affinity_contract.py preflight --workspace /authorized/story
python scripts/affinity_contract.py verify --layout /story/layout.json --exports /story/exports/page-001
python scripts/affinity_contract.py handoff --layout /story/layout.json --exports /story/exports/page-001 --out /story/publishing/page-001-affinity-handoff.json
node --check scripts/affinity_selection_audit.js
```

Python 3.10+ is the baseline; unit tests use only the stdlib. The
fixture uses synthetic pixels and synthetic QA attestations, not a
proof of generated-art resemblance, publication success or Affinity
native save functionality.

## Static contract scenario matrix

| Scenario | Expected result |
|---|---|
| Fully valid synthetic Mangaka page | Pass structural gate; write deterministic handoff |
| Source art byte changed after review | Block stale art SHA |
| Layout changed after compositor | Block changed layout SHA |
| Dialogue ledger changed | Block changed ledger SHA |
| Accepted label but missing checks | Block incomplete QA |
| `not_applicable` with no reason | Block |
| Visible subject has identity `not_applicable` | Block |
| Duplicated/missing/changed text | Block |
| Speaker/kind mismatch | Block |
| Text in balloon layout | Block |
| Panel ID mismatch or duplication | Block |
| Crop out of bounds, ratio stretch | Block |
| Missing/bad PNG or wrong dimensions | Block |
| Missing/damaged ORA, reversed order | Block |
| Missing SVG metadata or wrong page | Block |
| Unsafe input path traversal | Block |
| More than one page manifest/foreign page | Block |
| Missing fonts, stale linked sources | Block |
| Handoff overwrite without approval | Block |
| Native file absent | Block native inventory |
| Native file exists | Report file bytes, **not** visual pass |
| No GUI/Desktop route | Produce truthful offline handoff |

## Real application smoke scenarios

For dated, actually executed Windows 3.3.3.5004 results, including
live MCP, verified `userDescription`, native reopens, SVG import, and
an explicit-size export fix, read [the live verification](../VERIFICATION.md)
and [the operator runbook](live-affinity-mcp.md). These do not by
assumption certify a complete Gatsheni chapter.


Run on an authorized desktop after Affinity is fully installed:

1. **Fresh native file:** create shapes, text and pixel art, save, close,
   reopen, verify each layer and text remain editable.
2. **Import SVG:** open output from a real Mangaka compositor, compare
   with PNG pixel oracle, inspect masks, text, clip boundaries, and
   alpha. Record deviations.
3. **Layered fallback:** reconstruct panel groups from verified PNG
   and compare to compositor output.
4. **Read-only script:** run bundled selection audit in Scripting Studio
   and compare reported selection bounds with visible objects.
5. **Native MCP path:** if actually connected, invoke an official
   read-only script and `render_spread`. Record real outputs.
6. **Desktop Commander route:** verify authorized device and terminal
   workflow, launch Affinity through a verified path. Separately
   test UI capability before any claimed click.
7. **Multilingual typography:** exact punctuation, diacritics,
   mixed LTR/RTL and configured East Asian/vertical flow where needed.
8. **Export roundtrip:** verify PNG and PDF settings, size, page order,
   layer editability in native source, and reimported visual appearance.
9. **Adjacent panel test:** reverse camera, persistent light, scarring,
   property handoff and narrative timing.
10. **Failure injection:** missing font, lost linked asset, corrupted
    native file, disabled MCP, retry after unknown timeout.
11. **Scroll delivery:** split long page into strips and inspect joins
    and viewport reveal timing.
12. **Print delivery:** verify trim/bleed/safe area and supplied printer
    color/export profile.

For each record `pass`, `fail` or `not_tested`, app build, device,
screenshot or generated file evidence and any limitations. A disconnected
or still-installing app leaves all live tests `not_tested`.

## What counts as battle tested

There must be evidence at all four levels: synthetic contract tests,
real Mangaka input contract, native Affinity import/edit/save/export
tests and final chapter visual review on the actual intended output.
Do not present the repo as end-to-end battle-tested while any of those
are outstanding. Promote only individual verified capabilities.
