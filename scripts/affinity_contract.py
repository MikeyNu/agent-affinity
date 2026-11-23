#!/usr/bin/env python3
"""Read-only Mangaka-to-Affinity composition contract and handoff verifier.

No Affinity UI or network access is used. This checks source coherence and
output containers, not visual correctness, native editability or story canon.
Python 3.10+. Synthetic tests live in ../tests/test_affinity_contract.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import struct
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
import zlib

EXPORTS = ("composite.png", "lettering.png", "page.svg", "page.ora", "render_manifest.json")
CHECKS = ("identity", "narrative", "continuity", "emotion", "anatomy", "style", "composition")
NATIVE_SUFFIXES = (".af", ".afpub", ".afdesign", ".afphoto")
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_PAGE_PIXELS = 40_000_000
MAX_ZIP_BYTES = 1_200_000_000
MAX_MEMBER_BYTES = 300_000_000


class ContractError(Exception):
    """Safety or coherence failure with stable diagnostic code."""


def check(condition: bool, code: str, explanation: str) -> None:
    if not condition:
        raise ContractError(f"{code}: {explanation}")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def json_file(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise ContractError(f"BAD_JSON: {path}: {exc}") from exc
    check(isinstance(value, dict), "BAD_JSON", f"Expected object in {path}")
    return value


def safe_path(root: Path, value: str | os.PathLike, label: str, *, must_exist=True) -> Path:
    check(isinstance(value, (str, os.PathLike)) and bool(str(value)),
          "BAD_PATH", f"{label} has no path")
    result = Path(value)
    if not result.is_absolute():
        result = root / result
    result = result.resolve()
    root = root.resolve()
    check(result == root or root in result.parents,
          "OUTSIDE_WORKSPACE", f"{label} escapes {root}: {result}")
    if must_exist:
        check(result.is_file(), "MISSING_FILE", f"{label}: {result}")
    return result


def file_hash(path: Path) -> dict:
    return {"path": str(path), "sha256": digest(path), "bytes": path.stat().st_size}


def unique(rows: object, key: str, label: str) -> dict:
    check(isinstance(rows, list), "BAD_STRUCTURE", f"{label} must be an array")
    values = {}
    for item in rows:
        check(isinstance(item, dict) and isinstance(item.get(key), str) and bool(item[key]),
              "BAD_STRUCTURE", f"{label} entry needs nonempty {key}")
        check(item[key] not in values, "DUPLICATE_ID", f"{label}: {item[key]}")
        values[item[key]] = item
    return values


def png_info(path: Path) -> tuple[int, int, int]:
    """Verify PNG signature, critical chunks and CRCs, returning W,H,color-type."""
    check(path.is_file() and path.stat().st_size >= 45,
          "BAD_PNG", f"Empty/truncated PNG: {path}")
    try:
        with path.open("rb") as f:
            check(f.read(8) == PNG_MAGIC, "BAD_PNG", f"Not PNG: {path}")
            size = None
            rgba = None
            saw_idat = False
            saw_end = False
            index = 0
            while True:
                header = f.read(8)
                check(len(header) == 8, "BAD_PNG", f"Truncated PNG chunk: {path}")
                length, kind = struct.unpack(">I4s", header)
                check(length <= MAX_MEMBER_BYTES, "BAD_PNG", f"Oversized PNG chunk: {path}")
                payload = f.read(length)
                crcbuf = f.read(4)
                check(len(payload) == length and len(crcbuf) == 4,
                      "BAD_PNG", f"Truncated PNG payload: {path}")
                got = struct.unpack(">I", crcbuf)[0]
                expected = zlib.crc32(payload, zlib.crc32(kind)) & 0xFFFFFFFF
                check(got == expected, "BAD_PNG", f"Invalid chunk CRC: {path}")
                if index == 0:
                    check(kind == b"IHDR" and length == 13,
                          "BAD_PNG", f"Missing initial IHDR: {path}")
                    w, h, depth, ctype, compression, filter_type, interlace = struct.unpack(">IIBBBBB", payload)
                    check(0 < w * h <= MAX_PAGE_PIXELS and w > 0 and h > 0,
                          "BAD_PNG", f"Invalid image dimensions: {path}")
                    check(compression == 0 and filter_type == 0 and interlace in (0, 1),
                          "BAD_PNG", f"Invalid PNG header: {path}")
                    size, rgba = (w, h), ctype
                if kind == b"IDAT":
                    saw_idat = True
                if kind == b"IEND":
                    check(length == 0, "BAD_PNG", f"Malformed IEND: {path}")
                    check(not f.read(1), "BAD_PNG", f"Trailing bytes after IEND: {path}")
                    saw_end = True
                    break
                index += 1
            check(saw_idat and saw_end, "BAD_PNG", f"Missing IDAT or IEND: {path}")
            return size[0], size[1], rgba
    except OSError as exc:
        raise ContractError(f"BAD_PNG: {path}: {exc}") from exc


def art_dimensions(path: Path) -> tuple[int, int]:
    if path.suffix.lower() == ".png":
        w, h, _ = png_info(path)
        return w, h
    # Mangaka already depends on Pillow for its compositor. Use it for
    # non-PNG inputs, fail closed if not present instead of guessing geometry.
    try:
        from PIL import Image
    except ImportError as exc:
        raise ContractError(
            f"UNVERIFIED_GEOMETRY: Install Pillow to validate non-PNG source art: {path}"
        ) from exc
    try:
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            w, h = im.size
        check(0 < w * h <= MAX_PAGE_PIXELS, "BAD_ART", f"Art size invalid: {path}")
        return w, h
    except (OSError, ValueError) as exc:
        raise ContractError(f"BAD_ART: Cannot decode {path}: {exc}") from exc


def frame_bounds(frame: object, width: int, height: int, label: str) -> tuple[float, float, float, float]:
    check(isinstance(frame, dict), "BAD_FRAME", f"{label}: missing frame")
    check(("rect" in frame) != ("polygon" in frame), "BAD_FRAME",
          f"{label}: use rect OR polygon")
    if "rect" in frame:
        box = frame["rect"]
        check(isinstance(box, list) and len(box) == 4, "BAD_FRAME", f"{label} rect")
        x, y, w, h = box
    else:
        pts = frame["polygon"]
        check(isinstance(pts, list) and len(pts) >= 3, "BAD_FRAME", f"{label} polygon")
        check(all(isinstance(p, list) and len(p) == 2 for p in pts),
              "BAD_FRAME", f"{label} polygon points")
        xx, yy = [p[0] for p in pts], [p[1] for p in pts]
        x, y, w, h = min(xx), min(yy), max(xx) - min(xx), max(yy) - min(yy)
    nums = (x, y, w, h)
    check(all(isinstance(n, (float, int)) and not isinstance(n, bool) and math.isfinite(n)
              for n in nums), "BAD_FRAME", f"{label}: invalid numbers")
    check(x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= width and y + h <= height,
          "BAD_FRAME", f"{label}: frame out of page")
    return float(x), float(y), float(w), float(h)


def verify_ora(path: Path, size: tuple[int, int], expected_bottom_top: list[str]) -> None:
    try:
        with zipfile.ZipFile(path) as z:
            infos = z.infolist()
            check(len(infos) <= 1000 and sum(i.file_size for i in infos) <= MAX_ZIP_BYTES,
                  "BAD_ORA", "Archive uncompressed size too large")
            for i in infos:
                check(i.file_size <= MAX_MEMBER_BYTES and not i.filename.startswith("/")
                      and ".." not in Path(i.filename).parts,
                      "BAD_ORA", f"Unsafe archive member: {i.filename}")
            check(z.testzip() is None, "BAD_ORA", "Archive CRC failure")
            check(z.read("mimetype") == b"image/openraster", "BAD_ORA", "Wrong mimetype")
            check("mergedimage.png" in z.namelist(), "BAD_ORA", "Missing merged preview")
            stack = ET.fromstring(z.read("stack.xml"))
            check(stack.tag == "image", "BAD_ORA", "Wrong root")
            check((int(stack.attrib.get("w", -1)), int(stack.attrib.get("h", -1))) == size,
                  "BAD_ORA", "Archive size mismatch")
            branch = stack.find("stack")
            check(branch is not None, "BAD_ORA", "Missing stack")
            layer_nodes = branch.findall("layer")
            names = [node.attrib.get("name") for node in layer_nodes]
            check(names == list(reversed(expected_bottom_top)),
                  "BAD_ORA", "OpenRaster layer sequence differs from render manifest")
            for layer in layer_nodes:
                member = layer.attrib.get("src")
                check(isinstance(member, str) and member.startswith("data/") and member in z.namelist(),
                      "BAD_ORA", f"Missing member for layer: {member}")
            if len(z.read("mergedimage.png")) < 40:
                check(False, "BAD_ORA", "Truncated merged preview")
    except (OSError, ValueError, KeyError, ET.ParseError, zipfile.BadZipFile,
            RuntimeError, OverflowError) as exc:
        raise ContractError(f"BAD_ORA: {path}: {exc}") from exc


def verify_svg(path: Path, size: tuple[int, int], source_manifest: dict, panel_count: int) -> None:
    try:
        root = ET.parse(path).getroot()
        ns = "{http://www.w3.org/2000/svg}"
        check(root.tag == ns + "svg", "BAD_SVG", "Not an SVG root")
        check(root.attrib.get("viewBox") == f"0 0 {size[0]} {size[1]}",
              "BAD_SVG", "SVG viewBox does not match page")
        check(root.attrib.get("width") == str(size[0]) and
              root.attrib.get("height") == str(size[1]),
              "BAD_SVG", "SVG dimensions do not match page")
        nodes = root.findall(".//" + ns + "g")
        art_group = next((g for g in nodes if g.attrib.get("id") == "panel-art"), None)
        check(art_group is not None, "BAD_SVG", "Missing panel-art group")
        check(len(art_group.findall(".//" + ns + "image")) == panel_count,
              "BAD_SVG", "SVG panel-image count mismatch")
        meta = root.find(ns + "metadata")
        check(meta is not None and bool(meta.text), "BAD_SVG", "Missing embedded manifest")
        payload = json.loads(meta.text)
        for name in ("page_id", "layout_sha256", "ledger_sha256", "panels", "dialogue"):
            check(payload.get(name) == source_manifest.get(name), "BAD_SVG",
                  f"SVG metadata differs on {name}")
    except (OSError, ET.ParseError, ValueError, TypeError) as exc:
        raise ContractError(f"BAD_SVG: {path}: {exc}") from exc


def verify(layout_path: Path, exports_path: Path, workspace: Path | None = None,
           font_roots: list[Path] | None = None) -> dict:
    layout_path = layout_path.resolve()
    exports_path = exports_path.resolve()
    base = workspace.resolve() if workspace is not None else layout_path.parent
    check(base.is_dir(), "BAD_WORKSPACE", f"Workspace does not exist: {base}")
    check(layout_path.is_file() and (layout_path == base or base in layout_path.parents),
          "BAD_WORKSPACE", f"Layout outside workspace or missing: {layout_path}")
    check(exports_path == base or base in exports_path.parents,
          "BAD_WORKSPACE", f"Exports outside workspace: {exports_path}")
    layout = json_file(layout_path)
    check(layout.get("version") == 1, "BAD_LAYOUT", "Unsupported layout.version")
    page = layout.get("page")
    check(isinstance(page, dict), "BAD_LAYOUT", "Missing page")
    pid = page.get("id")
    width, height = page.get("width"), page.get("height")
    check(isinstance(pid, str) and bool(pid), "BAD_LAYOUT", "Missing page.id")
    check(all(isinstance(v, int) and not isinstance(v, bool) and v > 0 for v in (width, height))
          and width * height <= MAX_PAGE_PIXELS, "BAD_LAYOUT", "Page dimensions invalid")
    size = (width, height)
    ledger_path = safe_path(base, layout.get("ledger"), "ledger")
    ledger = json_file(ledger_path)
    all_dialogue = unique(ledger.get("dialogue"), "dialogue_id", "ledger")
    page_dialogue = [row for row in all_dialogue.values() if row.get("page_id") == pid]
    orders = [row.get("reading_order") for row in page_dialogue]
    if any(v is not None for v in orders):
        check(all(isinstance(v, int) and v > 0 and not isinstance(v, bool) for v in orders)
              and len(set(orders)) == len(orders), "BAD_LEDGER", "Invalid reading order")
        page_dialogue.sort(key=lambda row: row["reading_order"])
    panels = unique(layout.get("panels"), "id", "panels")
    check(bool(panels), "BAD_LAYOUT", "No panels")
    balloons = unique(layout.get("balloons", []), "id", "balloons")
    assignments = [row.get("dialogue_id") for row in balloons.values()]
    check(assignments == [row["dialogue_id"] for row in page_dialogue],
          "DIALOGUE_ORDER", "Balloon IDs do not reproduce the ledger order")
    check(all("text" not in row for row in balloons.values()), "DIALOGUE_OVERRIDE",
          "Balloon carries unauthorized text")

    export_paths = {name: safe_path(base, str(exports_path / name), name) for name in EXPORTS}
    manifest = json_file(export_paths["render_manifest.json"])
    check(manifest.get("version") == 1 and manifest.get("page_id") == pid,
          "STALE_RENDER", "Wrong compositor version or page")
    check(manifest.get("layout_sha256") == digest(layout_path), "STALE_LAYOUT",
          "Layout was modified after composition")
    check(manifest.get("ledger_sha256") == digest(ledger_path), "STALE_LEDGER",
          "Dialogue ledger was modified after composition")
    manifest_panels = unique(manifest.get("panels"), "panel_id", "render manifest panels")
    check(list(manifest_panels) == list(panels), "PANEL_ORDER", "Render panel order differs")

    sources = {"layout": file_hash(layout_path), "ledger": file_hash(ledger_path)}
    panel_sources = []
    for panel_id, panel in panels.items():
        art = safe_path(base, panel.get("art"), f"{panel_id}.art") if Path(str(panel.get("art"))).is_absolute() else safe_path(layout_path.parent, panel.get("art"), f"{panel_id}.art")
        approval = safe_path(base, panel.get("acceptance"), f"{panel_id}.acceptance") if Path(str(panel.get("acceptance"))).is_absolute() else safe_path(layout_path.parent, panel.get("acceptance"), f"{panel_id}.acceptance")
        # Enforce the global workspace even for paths relative to layout folder.
        check(art == base or base in art.parents, "OUTSIDE_WORKSPACE", "Art outside workspace")
        check(approval == base or base in approval.parents, "OUTSIDE_WORKSPACE", "QA outside workspace")
        qa = json_file(approval)
        check(qa.get("status") == "accepted" and qa.get("panel_id") == panel_id,
              "BAD_ACCEPTANCE", f"Panel {panel_id} not accepted or wrong ID")
        art_hash = digest(art)
        check(qa.get("art_sha256") == art_hash,
              "STALE_ART", f"Panel {panel_id} hash differs from approval")
        check(isinstance(qa.get("reviewed_by"), str) and qa["reviewed_by"].strip(),
              "BAD_ACCEPTANCE", f"Panel {panel_id} lacks reviewer")
        checks = qa.get("checks")
        check(isinstance(checks, dict) and set(CHECKS) <= set(checks),
              "BAD_ACCEPTANCE", f"Panel {panel_id} missing hard gates")
        for name in CHECKS:
            decision = checks[name]
            if isinstance(decision, str):
                check(decision == "pass", "BAD_ACCEPTANCE", f"{panel_id}.{name} not passed")
            else:
                check(isinstance(decision, dict) and decision.get("status") in ("pass", "not_applicable")
                      and isinstance(decision.get("reason"), str) and decision["reason"].strip(),
                      "BAD_ACCEPTANCE", f"{panel_id}.{name} missing reason/status")
                if name in ("identity", "emotion", "anatomy") and panel.get("subjects"):
                    check(decision["status"] == "pass", "BAD_ACCEPTANCE",
                          f"{panel_id}.{name} requires pass for visible subject")
        reported = manifest_panels[panel_id]
        check(reported.get("art_sha256") == art_hash and
              reported.get("reviewed_by") == qa.get("reviewed_by"),
              "STALE_ART", f"Panel {panel_id} render record differs")
        dims = art_dimensions(art)
        crop = reported.get("crop")
        expected_crop = panel.get("crop", [0, 0, dims[0], dims[1]])
        check(isinstance(crop, list) and len(crop) == 4 and
              all(isinstance(n, (int, float)) and not isinstance(n, bool)
                  and math.isfinite(n) and float(n).is_integer() for n in crop) and
              crop == expected_crop, "BAD_CROP", f"Panel {panel_id} source crop differs")
        cx, cy, cw, ch = crop
        check(cx >= 0 and cy >= 0 and cw > 0 and ch > 0 and cx + cw <= dims[0] and cy + ch <= dims[1],
              "BAD_CROP", f"Panel {panel_id} crop outside original art")
        fx, fy, fw, fh = frame_bounds(panel.get("frame"), width, height, panel_id)
        fit = panel.get("fit", "cover")
        check(fit in ("cover", "contain"), "BAD_SCALE", "Unknown fit or stretch")
        align = panel.get("align", [0.5, 0.5])
        check(isinstance(align, list) and len(align) == 2 and all(
              isinstance(a, (int, float)) and not isinstance(a, bool) and 0 <= a <= 1
              for a in align), "BAD_SCALE", f"{panel_id} invalid align")
        scale = (max if fit == "cover" else min)(fw / cw, fh / ch)
        ox = fx + (fw - cw * scale) * align[0]
        oy = fy + (fh - ch * scale) * align[1]
        offset = reported.get("offset")
        check(isinstance(offset, list) and len(offset) == 2 and
              all(isinstance(v, (float, int)) and math.isfinite(v) for v in offset) and
              math.isclose(reported.get("scale", -1), scale, abs_tol=1e-7, rel_tol=1e-7) and
              math.isclose(offset[0], ox, abs_tol=1e-5, rel_tol=1e-7) and
              math.isclose(offset[1], oy, abs_tol=1e-5, rel_tol=1e-7),
              "BAD_SCALE", f"{panel_id} changed uniform crop transform")
        for region in panel.get("critical_regions", []):
            check(isinstance(region, dict) and isinstance(region.get("rect"), list)
                  and len(region["rect"]) == 4, "BAD_REGION", f"{panel_id} malformed critical region")
            rx, ry, rw, rh = region["rect"]
            check(all(isinstance(v, (int, float)) and math.isfinite(v)
                      for v in (rx, ry, rw, rh)) and rx >= cx and ry >= cy and rw > 0 and rh > 0
                  and rx + rw <= cx + cw and ry + rh <= cy + ch,
                  "BAD_REGION", f"{panel_id} region outside crop")
        panel_sources.append({
            "panel_id": panel_id,
            "art": file_hash(art),
            "acceptance": file_hash(approval),
            "reviewer": qa["reviewed_by"],
            "crop": crop,
            "scale": scale,
            "offset": [ox, oy]
        })

    manifest_lines = manifest.get("dialogue")
    check(isinstance(manifest_lines, list), "BAD_RENDER", "Manifest dialogue missing")
    check([row.get("dialogue_id") for row in manifest_lines] ==
          [row["dialogue_id"] for row in page_dialogue],
          "DIALOGUE_ORDER", "Render dialogue order changed")
    styles = layout.get("styles", {})
    check(isinstance(styles, dict), "BAD_FONT", "styles must be an object")
    source_fonts = {}
    for rendered, row, balloon in zip(manifest_lines, page_dialogue, balloons.values()):
        for key in ("dialogue_id", "text", "speaker_id", "kind"):
            check(rendered.get(key) == row.get(key), "STALE_DIALOGUE",
                  f"{row['dialogue_id']}: changed {key}")
        style_id = balloon.get("style")
        style = styles.get(style_id)
        check(isinstance(style, dict), "BAD_FONT",
              f"{row['dialogue_id']}: missing defined balloon style {style_id}")
        font_value = style.get("font_path", layout.get("font_path"))
        check(isinstance(font_value, str) and bool(font_value),
              "BAD_FONT", f"{row['dialogue_id']}: missing approved font path")
        font_path = Path(font_value)
        if not font_path.is_absolute():
            font_path = layout_path.parent / font_path
        font_path = font_path.resolve()
        allowed = [base] + [root.resolve() for root in (font_roots or [])]
        check(any(font_path == root or root in font_path.parents for root in allowed),
              "OUTSIDE_WORKSPACE", f"Font outside authorized font roots: {font_path}")
        check(font_path.is_file() and font_path.suffix.lower() in (".ttf", ".otf"),
              "BAD_FONT", f"Missing or unsupported font file: {font_path}")
        font_sha = digest(font_path)
        check(rendered.get("font_sha256") == font_sha,
              "STALE_FONT", f"{row['dialogue_id']}: font differs from render")
        source_fonts[str(font_path)] = file_hash(font_path)
    for name in ("composite.png", "lettering.png"):
        w, h, ctype = png_info(export_paths[name])
        check((w, h) == size and ctype == 6, "BAD_PNG",
              f"{name} dimensions or RGBA format incorrect")
    layers = manifest.get("layers_bottom_to_top")
    check(isinstance(layers, list) and len(layers) == len(set(layers)) and
          all(isinstance(name, str) and name for name in layers),
          "BAD_LAYERS", "No valid layer order")
    check(all(f"Panel {name}" in layers for name in panels), "BAD_LAYERS",
          "Not all accepted panels have layers")
    verify_ora(export_paths["page.ora"], size, layers)
    verify_svg(export_paths["page.svg"], size, manifest, len(panels))

    return {
        "schema_version": 1,
        "tool": "agent-affinity/affinity_contract.py",
        "status": "contract_validated_not_visual_qa",
        "page_id": pid, "size": list(size),
        "layout": sources["layout"], "ledger": sources["ledger"],
        "fonts": list(source_fonts.values()),
        "panels": panel_sources,
        "dialogue_ids": [row["dialogue_id"] for row in page_dialogue],
        "layers_bottom_to_top": layers,
        "exports": {name: file_hash(path) for name, path in export_paths.items()},
        "affinity_import": {
            "svg": "import_candidate_live_parity_required",
            "ora": "not_assumed_supported",
            "native": "pending_affinity_test"
        },
        "visual_status": "not_verified",
        "claims": {
            "source_bytes": True,
            "structural_contract": True,
            "affinity_native_editability": False,
            "artistic_accuracy": False
        }
    }


def write_handoff(report: dict, destination: Path, overwrite: bool) -> None:
    destination = destination.resolve()
    check(destination.parent.is_dir(), "BAD_OUTPUT", "Output parent does not exist")
    check(overwrite or not destination.exists(), "EXISTS", f"Refusing overwrite: {destination}")
    # No source assets are touched. Use a same-directory temporary file then
    # os.replace only after JSON serialization and full flush.
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(prefix=".affinity-handoff-", suffix=".tmp", dir=destination.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as out:
            out.write(payload)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, destination)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def native_check(handoff_path: Path, native_path: Path, deliverables: list[str]) -> dict:
    handoff = json_file(handoff_path)
    check(handoff.get("status") == "contract_validated_not_visual_qa" and handoff.get("schema_version") == 1,
          "BAD_HANDOFF", "Not an Affinity handoff")
    for section in ("layout", "ledger"):
        obj = handoff.get(section, {})
        p = Path(obj.get("path", ""))
        check(p.is_file() and digest(p) == obj.get("sha256"),
              "STALE_INPUT", f"{section} changed since handoff")
    for item in handoff.get("fonts", []):
        p = Path(item.get("path", ""))
        check(p.is_file() and digest(p) == item.get("sha256"),
              "STALE_INPUT", "Font changed since handoff")
    for item in handoff.get("panels", []):
        for key in ("art", "acceptance"):
            obj = item.get(key, {})
            p = Path(obj.get("path", ""))
            check(p.is_file() and digest(p) == obj.get("sha256"),
                  "STALE_INPUT", f"{item.get('panel_id')}.{key} changed since handoff")
    for name, obj in handoff.get("exports", {}).items():
        p = Path(obj.get("path", ""))
        check(p.is_file() and digest(p) == obj.get("sha256"),
              "STALE_INPUT", f"{name} changed since handoff")
    native_path = native_path.resolve()
    check(native_path.is_file() and native_path.stat().st_size > 0 and
          native_path.suffix.lower() in NATIVE_SUFFIXES,
          "BAD_NATIVE", "Missing, empty or unsupported native master")
    exported = []
    for value in deliverables:
        p = Path(value).resolve()
        check(p.is_file() and p.stat().st_size > 0, "BAD_DELIVERABLE", f"Missing: {p}")
        if p.suffix.lower() == ".png":
            png_info(p)
        exported.append(file_hash(p))
    return {
        "status": "files_exist_not_visual_qa",
        "page_id": handoff["page_id"],
        "native": file_hash(native_path),
        "deliverables": exported,
        "native_reopen_test": "not_tested",
        "layer_editability_test": "not_tested",
        "visual_status": "not_verified"
    }


def preflight(workspace: Path) -> dict:
    p = workspace.resolve()
    return {
        "status": "filesystem_preflight_only",
        "platform": platform.platform(), "python": sys.version.split()[0],
        "workspace": str(p), "workspace_exists": p.is_dir(),
        "affinity_install": "not_checked_use_os_app_discovery",
        "desktop_commander_mcp": "not_detectable_from_python",
        "affinity_mcp": "not_detectable_from_python",
        "gui_capability": "not_detectable_from_python",
        "visual_status": "not_verified"
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for cmd in ("verify", "handoff"):
        p = sub.add_parser(cmd)
        p.add_argument("--layout", required=True, type=Path)
        p.add_argument("--exports", required=True, type=Path)
        p.add_argument("--workspace", type=Path, help="Authorized workspace root, default layout parent")
        p.add_argument("--font-root", type=Path, action="append", default=[],
                       help="Explicitly authorize a separate read-only installed font directory")
        if cmd == "handoff":
            p.add_argument("--out", required=True, type=Path)
            p.add_argument("--overwrite", action="store_true")
    p = sub.add_parser("native")
    p.add_argument("--handoff", required=True, type=Path)
    p.add_argument("--native", required=True, type=Path)
    p.add_argument("--deliverable", action="append", default=[])
    p = sub.add_parser("preflight")
    p.add_argument("--workspace", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "preflight":
            result = preflight(args.workspace)
        elif args.command == "native":
            result = native_check(args.handoff, args.native, args.deliverable)
        else:
            result = verify(args.layout, args.exports, args.workspace, args.font_root)
            if args.command == "handoff":
                # Handoffs remain in the authorized workspace.
                base = (args.workspace or args.layout.parent).resolve()
                target = args.out.resolve()
                check(target == base or base in target.parents, "OUTSIDE_WORKSPACE",
                      f"Handoff destination outside workspace: {target}")
                write_handoff(result, target, args.overwrite)
                result["handoff_path"] = str(target)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (ContractError, OSError, KeyError, TypeError, ValueError, OverflowError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
