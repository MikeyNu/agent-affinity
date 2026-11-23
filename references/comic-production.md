# Manga, manhwa and webtoon page construction in Affinity

## Two coordinate systems plus camera space

Mangaka plans actions with world positions, facing vectors and camera
position/target. Affinity lays out page pixels with (0,0) at top left.
Source crops use their own native image pixels. Keep these distinct.
Never mirror a panel to make the gutter fit if that swaps a facial
scar, handedness, directional light or background landmark.

## Page grammar and hierarchy

Plan before the final art is selected, but only assemble after review.
For every page decide: narrative goal, page entry and exit, focal panel,
dominant contrast, pause/reveal rhythm, dialogue order and protected
art regions. Do not use identical rectangular panels just because
they are easy to batch. Vary framing when the beat earns it. Preserve
sufficient gutters to keep order unmistakable.

Recommended editable native structure, from **bottom to top**:

```text
PAGE_001
  00_BASE                Paper, backdrop and approved gutter color
  10_PANELS
    P001_ART             Accepted art, untouched underlying source
    P001_FRAME_MASK      Non-destructive mask/clip, separate transform
    P001_CORRECTIONS     Local checked paint adjustments when needed
    P002_ART
    P002_FRAME_MASK
    ...
  20_BORDERS             Named vector frames, consistent seam width
  30_BREAKOUTS           Intentional overlap with recorded continuity
  40_EFFECTS             SFX art, sparks, speed marks and tone as layers
  50_BALLOON_TAILS       Exact speaker-anchored tails/dots
  60_BALLOON_BODIES      Vector bodies on their own layers
  70_DIALOGUE            D001 / D002 / exact ledger IDs
  80_CAPTIONS            Narration and scene/time cues
  90_SFX_LETTERING       Hand-drawn or typographic, independent of speech
  99_GUIDES_QA           Safe margins, protected regions, hidden for export
```

The order of tails versus bodies and effects is project-dependent. Use
separate layers but confirm the visual overlap in the native editor.
For an effect bursting across a frame, split the foreground from the
original accepted panel without deleting or recreating the source art.
A breakout must preserve which character stands in front of which.

## Layout and crop decisions

- Preserve source aspect ratio. Apply a single uniform scale, then use
  an editable clip mask. Never distort faces to fit polygons.
- Mark protected face, hand, contact, prop and lettering regions before
  placing overlays. Exclude areas reserved for balloons.
- Validate polygon geometry and overlap with Mangaka compositor and
  Affinity side-by-side view. A mathematically valid mask may still
  cut off the only clue that explains a beat.
- Avoid a foreground asset hiding an earlier panel's protected region
  when overlapping frames. Check borders and shadows at reading size.
- A silent panel should be deliberately silent, not a place where a
  line was dropped. A dramatic reveal may be delayed to the next page,
  spread or scroll viewport.

## Dialogue and balloon decisions

Maintain ledger-based `Dxxx` text plus `speaker_id` and `kind`.
Use the project's visual grammar, including different treatments for
spoken lines, internal thought, screams, remote devices, narration
and sound. A tail must point toward the **actual** speaker, not just
the only visible person. Device speech can point toward a phone or
radio when documented in the ledger.

Do not allow balloons to cross crucial gestures or faces. Compare
the reader's visual path with the literal ledger order. Preserve
Unicode, punctuation, casing, intended pauses, code switching and
font selection. Inspect actual glyphs and shaping. Mixed English
LTR and RTL manga layout are separate systems, and supporting a
right-to-left page flow does not mean reversing the characters of
a dialogue string.

## Continuity checks across a sequence

Before acceptance compare previous/current/next panels against
original reference sheets and environment plans:
- Identity and anatomical sidedness, not only hair color;
- Physical positions, eyelines, interaction axis and camera;
- Clothing state, held props, handoffs, injuries and persistent damage;
- environmental light sources versus cinematic color treatment;
- actual contact target and consequence after motion;
- screen order of speaker and listener and balloon order.

For South African settings, study verified local details and
project-approved demographic references. Avoid substituting unrelated
cultural motifs, landmarks or architecture because generic models
tend to produce them. Do not introduce stereotypes as replacements.

## Print versus vertical scroll

| Dimension | Print/digital pages | Vertical scroll |
|---|---|---|
| Reveal | Page turn and facing spread | Viewport window and gap timing |
| Units | Trim size plus printer bleeds and safe areas | Pixel width and viewport-height preview |
| Text | Physical-size legibility and binding safety | Phone-size legibility and bubble density |
| Export | Ordered PDF and page PNGs | Long master plus tested split strips |
| QA | Single page + facing spread | Moving viewport and segment joins |

Never invent a universal printer size, bleed, DPI or WEBTOON upload limit.
Get current delivery specs from the actual publisher. For scroll strips,
avoid cutting through text, faces, tails, effects and transitions. Check
a few viewport heights, not only a stitched full-height contact sheet.
Record color profile for each output. If for print, verify font-embedding
rights, embedded ICC and overprint/rasterization choices.

## Anti-generic art checks

Use Mangaka's original art-direction and project-specific styling. Do not
replace individual art with stock comic halftone patterns, glossy AI
lighting or identical symmetrical balloon arrangements. The Affinity
stage should enhance readability and maintain the approved hand-drawn
line character without laundering style drift.

## Authoritative reading

See Mangaka `references/pages-and-lettering.md` and
`references/spatial-continuity.md`, plus Affinity's export settings:
https://www.affinity.studio/help/sharing-export-settings/ .
