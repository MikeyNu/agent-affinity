# Affinity by Canva: operator playbook

## App identity and documentation

Target **Affinity by Canva**, the free unified vector, pixel and layout
application. Its JavaScript SDK was released with scripting in 2026 and is
marked beta. Legacy Affinity V2 is a different product and has no current
scripting support. Determine the installed version on the user's machine.
Official documentation:
- https://www.affinity.studio/help/panels-layers-panel/
- https://www.affinity.studio/help/sharing-export-settings/
- https://www.affinity.studio/features/scripting
- https://sdk.affinity.studio/

## Navigation without brittle coordinates

Menu labels and studio workspaces can change with updates or customization.
Use live visual evidence and menus. In the current official help, the
**Layers** panel is found under **Window > General > Layers**. Pixel,
Vector, Layout, and Scripting capabilities may be surfaced as studios.
Check their visible labels before following an instruction. Do not use
hard-coded screen coordinates copied from another agent or screenshot.

Before changing the document, capture:
- opened filename and modified/unsaved state;
- document units, dimensions, DPI, color profile, page count;
- Layers panel tree and intended target layer;
- source page PNG and handoff revision.

## New document and multipage setup

1. Choose **File > New** in the actual application and select a document
   suited to the current project. For print, use the publisher's trim,
   bleed, color profile and binding requirements. For webtoons, use target
   pixel dimensions, not an assumed paper DPI.
2. Set reading order from Mangaka `project.reading_direction`. LTR and RTL
   page traversal does not set the language's text direction automatically.
3. Set spread mode/facing pages only when required by the print plan.
   Review page turning, gutter/binding safety and page-pair reveals.
4. Save immediately under `publishing/masters/<chapter>/<page-id>-v001.af`
   or the actual native suffix shown by this version. Native master is
   the editable source, not a proof-of-layout PNG.

## Import candidate and parity test

1. Open the approved `page.svg` on a **copy** or place it in a new document.
   Verify page size, each independent group, image crop, exact balloon text,
   outline, transparency and any embedded fonts. Do not assume SVG import
   preserves every edit operation or embedded font.
2. Keep `composite.png` as a pixel reference and `lettering.png` as a
   transparent overlay for comparison, not as flattened page ownership.
3. Import the original accepted panel images separately if SVG does not
   preserve required editable masks/layers. Each panel gets its own named
   group and frame. Anchor transforms to the source compositor's
   recorded `crop`, `scale` and `offset` values.
4. Use linked placement where actual Affinity supports it and resource
   management is configured. Use embedded placement if external links
   cannot be reliably carried into the final package. Missing links block
   acceptance. See the Resource Manager.
5. **ORA is not the Affinity interchange contract.** Preserve `page.ora`
   for GIMP/Krita/OpenRaster consumers. Do not rename an ORA to PSD.
   If an ORA-to-PSD conversion is needed, use a verified converter, retain
   original layers and test PSD import visually and structurally.
6. Use the Affinity **Layers** panel to inspect names, nesting, mask
   attachments, locked states, hidden layers and top-to-bottom stacking.
   Changes in visibility must be intentional and reversible.

## Masking and retouching

For each frame, place the approved raster panel at uniform scale, then
mask/clip with an independently editable shape. Do **not** free-transform
unequally to fit the panel polygon. Maintain a protected list of source
rectangles for faces, hand contacts, identifying marks, readable props and
reveal clues.

Separate:
- temporary selection masks for corrections;
- final reusable panel clipping geometry;
- vector frame borders;
- isolated foreground breakouts beyond a frame;
- shadows, halftones, ink and light as separately reviewable effects.

Make corrections as named, local, reversible layers. Recheck whole-image
identity, anatomy, lighting and adjacent shots. A mask in generated art
is not a guarantee of pixel preservation, so compare unchanged regions.

## Text and balloons

Create balloon bodies as reusable vector shapes and tails as separately
editable vectors. Add separate text objects bound to Mangaka dialogue IDs
and named native layers. Do not bake in generated glyphs or trace text when
the brief requires editable/localized words.

Check font license, actual glyph availability, leading, tracking, line
breaks, padding, tails and ordering at final size. RTL script shaping
requires actual text engine tests. Japanese vertical text must be tested
in that arrangement; never rotate characters blindly. For a crowded
speech scene, revise framing or panel count instead of shrinking text
into illegibility. Preserve exact punctuation, Unicode and original
speaker. For a custom hand-lettered SFX, keep it independent from speech.

## Export

Use the actual **Export** interface and document `Area` selector.
The official Affinity export panel supports page/spread selections, PDF
compatibility, ICC embedding, DPI/downsampling options, include bleed
and per-format settings. Named top-level layers can be included in PDF
depending on export selections; never infer they were exported without
reopening the PDF.

Always record export settings: target pages, pixel dimensions, profile,
flattening/rasterization choices, font handling, bleed, output path.
When exporting vector PDFs, test the final rasterization of complex
strokes, transparency and text. For screen PNG, check the dimensions and
color and alpha visually. For print, printer rules outrank generic presets.

## Operational UI smoke test

On a clean disposable copy, not a Gatsheni master:

1. Open Affinity and verify version and an unsaved blank document.
2. Add two vector shapes, a pixel image, a text object and a clipping
   shape; name the layers distinctively.
3. Save native. Close and reopen. Verify all five object types and text
   remain editable, object order and alpha are unchanged.
4. Import a representative Mangaka `page.svg`; compare to the associated
   `composite.png` at the same pixel size and inspect all layer types.
5. Export a PNG and PDF, reopen them and inspect crop, edge, typography,
   ICC and page selection. Repeat with an SVG import with nested clip
   paths and embedded fonts.
6. If using scripting, run the supplied read-only
   `scripts/affinity_selection_audit.js` in the native Scripting Studio.
   Do not claim this was executed until the app confirms the result.
7. Record whether each step is `pass`, `fail` or `not_tested`, with
   actual screenshots or source outputs as evidence.

A file's presence does not prove the editor reopened it or that text
remained editable.
