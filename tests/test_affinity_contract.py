"""Synthetic regression tests for the Mangaka-to-Affinity file contract.

These exercise structural failures and byte integrity, not actual Affinity
interactions or the artistic fidelity of any generated comic art.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
import zlib

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "affinity_contract.py"
spec = importlib.util.spec_from_file_location("affinity_contract", SCRIPT)
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)


def png(width=16, height=16, *, alpha=True) -> bytes:
    def chunk(name, data):
        return struct.pack(">I", len(data)) + name + data + struct.pack(
            ">I", zlib.crc32(data, zlib.crc32(name)) & 0xFFFFFFFF
        )
    ctype = 6 if alpha else 2
    pixel = b"\x55\x88\xaa\xff" if alpha else b"\x55\x88\xaa"
    lines = b"".join(b"\x00" + pixel * width for _ in range(height))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, ctype, 0, 0, 0)
    return ac.PNG_MAGIC + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(lines)) + chunk(b"IEND", b"")


def put_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class Fixture:
    def __init__(self, base):
        self.base = Path(base)
        self.exports = self.base / "exports" / "PAGE1"
        self.exports.mkdir(parents=True, exist_ok=True)
        (self.base / "approved").mkdir(exist_ok=True)
        (self.base / "qa").mkdir(exist_ok=True)
        (self.base / "fonts").mkdir(exist_ok=True)
        self.font = self.base / "fonts" / "test.ttf"
        # Synthetic bytes suffice for a hash contract test. No font is rendered.
        self.font.write_bytes(b"synthetic font fixture: not valid for publishing")
        self.art = self.base / "approved" / "P1.png"
        self.art.write_bytes(png())
        self.approval = self.base / "qa" / "P1.json"
        self.layout_path = self.base / "layout.json"
        self.ledger_path = self.base / "dialogue.json"
        self.layout = {
            "version": 1,
            "page": {"id": "PAGE1", "width": 16, "height": 16, "min_font_size": 8},
            "ledger": "dialogue.json", "font_path": "fonts/test.ttf",
            "styles": {"speech": {"shape": "ellipse", "allowed_kinds": ["speech"],
                                  "tail_policy": "optional", "font_size": 9}},
            "panels": [{"id": "P1", "art": "approved/P1.png", "acceptance": "qa/P1.json",
                        "frame": {"rect": [0, 0, 16, 16]}, "fit": "contain", "align": [0.5, 0.5],
                        "subjects": []}],
            "balloons": [{"id": "B1", "dialogue_id": "D1", "panel_id": "P1", "style": "speech",
                          "box": [1, 1, 10, 8]}]
        }
        self.ledger = {"dialogue": [{
            "dialogue_id": "D1", "page_id": "PAGE1", "panel_id": "P1",
            "speaker_id": "C1", "kind": "speech", "reading_order": 1, "text": "I am here."
        }]}
        self.qa = {
            "panel_id": "P1", "status": "accepted",
            "art_sha256": ac.digest(self.art), "reviewed_by": "synthetic-test",
            "checks": {name: "pass" for name in ac.CHECKS}
        }
        self.manifest = {}
        self.rebuild()

    def rebuild(self):
        put_json(self.layout_path, self.layout)
        put_json(self.ledger_path, self.ledger)
        put_json(self.approval, self.qa)
        self.manifest = {
            "version": 1, "page_id": "PAGE1",
            "layout_sha256": ac.digest(self.layout_path),
            "ledger_sha256": ac.digest(self.ledger_path),
            "panels": [{
                "panel_id": "P1", "art_sha256": ac.digest(self.art),
                "reviewed_by": "synthetic-test", "crop": [0, 0, 16, 16],
                "scale": 1.0, "offset": [0.0, 0.0]
            }],
            "dialogue": [{
                "dialogue_id": "D1", "speaker_id": "C1", "kind": "speech",
                "text": "I am here.", "font_sha256": ac.digest(self.font)
            }],
            "layers_bottom_to_top": [
                "Page", "Panel P1", "Panel borders", "Balloon tails",
                "Balloon bodies", "Dialogue text", "Sound effects"
            ]
        }
        self.write_outputs()

    def write_outputs(self, *, write_manifest=True, write_svg=True, write_ora=True):
        if write_manifest:
            put_json(self.exports / "render_manifest.json", self.manifest)
        width, height = self.layout["page"]["width"], self.layout["page"]["height"]
        (self.exports / "composite.png").write_bytes(png(width, height))
        (self.exports / "lettering.png").write_bytes(png(width, height))
        ns = "http://www.w3.org/2000/svg"
        if write_svg:
            root = ET.Element("{%s}svg" % ns, {
                "width": str(width), "height": str(height),
                "viewBox": f"0 0 {width} {height}"
            })
            art_group = ET.SubElement(root, "{%s}g" % ns, {"id": "panel-art"})
            for panel in self.manifest["panels"]:
                ET.SubElement(art_group, "{%s}image" % ns, {"data-panel-id": panel["panel_id"]})
            ET.SubElement(root, "{%s}metadata" % ns).text = json.dumps(self.manifest)
            (self.exports / "page.svg").write_bytes(ET.tostring(root, encoding="utf-8"))
        if write_ora:
            ora_root = ET.Element("image", {"w": str(width), "h": str(height),
                                            "name": "PAGE1", "version": "0.0.3"})
            stack = ET.SubElement(ora_root, "stack")
            with zipfile.ZipFile(self.exports / "page.ora", "w") as z:
                z.writestr("mimetype", "image/openraster", compress_type=zipfile.ZIP_STORED)
                for idx, name in enumerate(reversed(self.manifest["layers_bottom_to_top"])):
                    member = f"data/layer{idx:03d}.png"
                    z.writestr(member, png(width, height))
                    ET.SubElement(stack, "layer", {"name": name, "src": member, "x": "0",
                                                  "y": "0", "opacity": "1.0", "visibility": "visible"})
                z.writestr("stack.xml", ET.tostring(ora_root, encoding="utf-8"))
                z.writestr("mergedimage.png", png(width, height))

    def run(self):
        return ac.verify(self.layout_path, self.exports)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.fx = Fixture(self.tmp.name)

    def assert_fails(self, code):
        with self.assertRaises(ac.ContractError) as caught:
            self.fx.run()
        self.assertIn(code, str(caught.exception))

    def test_valid_one_panel_and_deterministic_handoff(self):
        first = self.fx.run()
        second = self.fx.run()
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "contract_validated_not_visual_qa")
        self.assertEqual(first["dialogue_ids"], ["D1"])
        self.assertFalse(first["claims"]["artistic_accuracy"])

    def test_handoff_write_refuses_overwrite(self):
        data = self.fx.run()
        target = self.fx.base / "handoff.json"
        ac.write_handoff(data, target, False)
        self.assertEqual(json.loads(target.read_text())["page_id"], "PAGE1")
        with self.assertRaises(ac.ContractError):
            ac.write_handoff(data, target, False)
        ac.write_handoff(data, target, True)

    def test_native_inventory_is_not_qa(self):
        handoff = self.fx.base / "handoff.json"
        ac.write_handoff(self.fx.run(), handoff, False)
        master = self.fx.base / "sample.af"
        with self.assertRaises(ac.ContractError):
            ac.native_check(handoff, master, [])
        master.write_bytes(b"synthetic native file placeholder")
        result = ac.native_check(handoff, master, [str(self.fx.exports / "composite.png")])
        self.assertEqual(result["native_reopen_test"], "not_tested")
        self.assertEqual(result["visual_status"], "not_verified")

    def test_source_art_mutated_after_review(self):
        self.fx.art.write_bytes(png(8, 8))
        self.assert_fails("STALE_ART")

    def test_missing_art_file(self):
        self.fx.art.unlink()
        self.assert_fails("MISSING_FILE")

    def test_layout_mutated(self):
        self.fx.layout["page"]["min_font_size"] = 12
        put_json(self.fx.layout_path, self.fx.layout)
        self.assert_fails("STALE_LAYOUT")

    def test_ledger_mutated(self):
        self.fx.ledger["dialogue"][0]["text"] = "A different line"
        put_json(self.fx.ledger_path, self.fx.ledger)
        self.assert_fails("STALE_LEDGER")

    def test_missing_qa_gate(self):
        del self.fx.qa["checks"]["identity"]
        put_json(self.fx.approval, self.fx.qa)
        self.assert_fails("BAD_ACCEPTANCE")

    def test_not_applicable_must_have_reason(self):
        self.fx.qa["checks"]["emotion"] = {"status": "not_applicable"}
        put_json(self.fx.approval, self.fx.qa)
        self.assert_fails("BAD_ACCEPTANCE")

    def test_visible_subject_requires_identity_pass(self):
        self.fx.layout["panels"][0]["subjects"] = [{"character_id": "C1", "mouth": [8, 8]}]
        self.fx.qa["checks"]["identity"] = {
            "status": "not_applicable", "reason": "incorrectly exempted"
        }
        self.fx.rebuild()
        self.assert_fails("BAD_ACCEPTANCE")

    def test_no_subject_allows_reasoned_na(self):
        self.fx.qa["checks"]["identity"] = {
            "status": "not_applicable", "reason": "The panel depicts scenery only"
        }
        put_json(self.fx.approval, self.fx.qa)
        self.assertEqual(self.fx.run()["page_id"], "PAGE1")

    def test_wrong_panel_id_attestation(self):
        self.fx.qa["panel_id"] = "P999"
        put_json(self.fx.approval, self.fx.qa)
        self.assert_fails("BAD_ACCEPTANCE")

    def test_missing_reviewer(self):
        self.fx.qa["reviewed_by"] = ""
        put_json(self.fx.approval, self.fx.qa)
        self.assert_fails("BAD_ACCEPTANCE")

    def test_missing_dialogue_assignment(self):
        self.fx.layout["balloons"] = []
        put_json(self.fx.layout_path, self.fx.layout)
        self.assert_fails("DIALOGUE_ORDER")

    def test_duplicated_balloon_id(self):
        self.fx.layout["balloons"].append(copy.deepcopy(self.fx.layout["balloons"][0]))
        put_json(self.fx.layout_path, self.fx.layout)
        self.assert_fails("DUPLICATE_ID")

    def test_balloon_must_not_carry_text(self):
        self.fx.layout["balloons"][0]["text"] = "hallucinated words"
        put_json(self.fx.layout_path, self.fx.layout)
        self.assert_fails("DIALOGUE_OVERRIDE")

    def test_rendered_dialogue_rewritten(self):
        self.fx.manifest["dialogue"][0]["text"] = "I was here."
        put_json(self.fx.exports / "render_manifest.json", self.fx.manifest)
        self.assert_fails("STALE_DIALOGUE")

    def test_rendered_wrong_speaker(self):
        self.fx.manifest["dialogue"][0]["speaker_id"] = "C2"
        put_json(self.fx.exports / "render_manifest.json", self.fx.manifest)
        self.assert_fails("STALE_DIALOGUE")

    def test_missing_font(self):
        self.fx.font.unlink()
        self.assert_fails("BAD_FONT")

    def test_changed_font(self):
        self.fx.font.write_bytes(b"new synthetic font bytes")
        self.assert_fails("STALE_FONT")

    def test_wrong_crop(self):
        self.fx.manifest["panels"][0]["crop"] = [12, 0, 8, 16]
        put_json(self.fx.exports / "render_manifest.json", self.fx.manifest)
        self.assert_fails("BAD_CROP")

    def test_stretched_panel(self):
        self.fx.manifest["panels"][0]["scale"] = 1.25
        put_json(self.fx.exports / "render_manifest.json", self.fx.manifest)
        self.assert_fails("BAD_SCALE")

    def test_invalid_page_frame(self):
        self.fx.layout["panels"][0]["frame"] = {"rect": [0, 0, 40, 10]}
        put_json(self.fx.layout_path, self.fx.layout)
        self.assert_fails("STALE_LAYOUT")

    def test_wrong_png_dimensions(self):
        (self.fx.exports / "composite.png").write_bytes(png(5, 5))
        self.assert_fails("BAD_PNG")

    def test_missing_png_alpha_channel(self):
        (self.fx.exports / "lettering.png").write_bytes(png(alpha=False))
        self.assert_fails("BAD_PNG")

    def test_corrupt_png_crc(self):
        p = self.fx.exports / "lettering.png"
        data = bytearray(p.read_bytes())
        data[32] ^= 1
        p.write_bytes(data)
        self.assert_fails("BAD_PNG")

    def test_corrupt_ora_archive(self):
        (self.fx.exports / "page.ora").write_bytes(b"not a zip")
        self.assert_fails("BAD_ORA")

    def test_ora_reversed_order(self):
        with zipfile.ZipFile(self.fx.exports / "page.ora", "w") as z:
            z.writestr("mimetype", "image/openraster")
            stack = ET.Element("image", {"w": "16", "h": "16"})
            node = ET.SubElement(stack, "stack")
            ET.SubElement(node, "layer", {"name": "Wrong", "src": "data/layer.png"})
            z.writestr("stack.xml", ET.tostring(stack))
            z.writestr("mergedimage.png", png())
            z.writestr("data/layer.png", png())
        self.assert_fails("BAD_ORA")

    def test_svg_missing_metadata(self):
        (self.fx.exports / "page.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><g id="panel-art"><image/></g></svg>'
        )
        self.assert_fails("BAD_SVG")

    def test_svg_stale_dialogue_metadata(self):
        svg = self.fx.exports / "page.svg"
        root = ET.fromstring(svg.read_bytes())
        meta = root.find("{http://www.w3.org/2000/svg}metadata")
        forged = copy.deepcopy(self.fx.manifest)
        forged["dialogue"][0]["text"] = "fabricated"
        meta.text = json.dumps(forged)
        svg.write_bytes(ET.tostring(root))
        self.assert_fails("BAD_SVG")

    def test_path_traversal_rejected(self):
        self.fx.layout["panels"][0]["art"] = "../unsafe.png"
        put_json(self.fx.layout_path, self.fx.layout)
        # Even though the layout hash becomes stale, art is checked after that.
        self.fx.manifest["layout_sha256"] = ac.digest(self.fx.layout_path)
        put_json(self.fx.exports / "render_manifest.json", self.fx.manifest)
        self.assert_fails("OUTSIDE_WORKSPACE")

    def test_handoff_detects_later_source_change(self):
        handoff = self.fx.base / "handoff.json"
        ac.write_handoff(self.fx.run(), handoff, False)
        self.fx.art.write_bytes(png(4, 4))
        master = self.fx.base / "sample.af"
        master.write_bytes(b"synthetic placeholder")
        with self.assertRaises(ac.ContractError) as caught:
            ac.native_check(handoff, master, [])
        self.assertIn("STALE_INPUT", str(caught.exception))

    def test_cli_good_and_bad_exit_codes(self):
        args = [sys.executable, str(SCRIPT), "verify", "--layout",
                str(self.fx.layout_path), "--exports", str(self.fx.exports)]
        passed = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(passed.returncode, 0, passed.stderr)
        self.assertEqual(json.loads(passed.stdout)["status"], "contract_validated_not_visual_qa")
        self.fx.font.unlink()
        failed = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(failed.returncode, 2)
        self.assertEqual(json.loads(failed.stderr)["status"], "blocked")

    def test_no_pillow_required_for_png_contract(self):
        self.assertEqual(ac.png_info(self.fx.art), (16, 16, 6))

    def test_preflight_is_honest_about_gui(self):
        info = ac.preflight(self.fx.base)
        self.assertEqual(info["gui_capability"], "not_detectable_from_python")


if __name__ == "__main__":
    unittest.main()
