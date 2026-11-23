"""Optional real integration tests against an installed agent-mangaka compositor.

Set MANGAKA_REPO to a checked-out MikeyNu/agent-mangaka repository.
Set MANGAKA_TEST_FONT to an approved installed single-file .ttf/.otf.
No font is copied, uploaded, bundled, committed, or returned to the user.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("affinity_contract", HERE / "scripts" / "affinity_contract.py")
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)

REPO = Path(os.environ.get("MANGAKA_REPO", "")).resolve() if os.environ.get("MANGAKA_REPO") else None
COMPOSITOR = REPO / "scripts" / "compose_page.py" if REPO else None


def find_font():
    custom = os.environ.get("MANGAKA_TEST_FONT", "")
    candidates = ([custom] if custom else []) + [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    return next((Path(x).resolve() for x in candidates if x and Path(x).is_file()), None)


try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None

FONT = find_font()


@unittest.skipUnless(COMPOSITOR is not None and COMPOSITOR.is_file() and FONT is not None and Image is not None,
                     "Requires real agent-mangaka repo, Pillow, and an installed legal test font")
class RealMangakaRoundtrip(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="affinity-mangaka-integration-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.export = self.root / "exports"
        (self.root / "approved").mkdir()
        (self.root / "qa").mkdir()
        self.layout_path = self.root / "layout.json"
        self.ledger_path = self.root / "dialogue.json"
        self.create_case()

    def create_case(self, silent=False):
        for i, color in enumerate(("#748ba0", "#d1aa6d"), 1):
            image = Image.new("RGBA", (800, 550), color)
            draw = ImageDraw.Draw(image)
            draw.rectangle([150, 80, 670, 500], outline="#203040", width=8)
            draw.ellipse([280, 110, 490, 340], fill="#e4d7c9", outline="#242424", width=8)
            draw.line([270, 390, 515, 390], fill="#202020", width=12)
            art = self.root / "approved" / f"P{i}.png"
            image.save(art)
            qa = {"panel_id": f"P{i}", "status": "accepted", "art_sha256": ac.digest(art),
                  "reviewed_by": "synthetic-integration-test",
                  "checks": {key: "pass" for key in ac.CHECKS},
                  "notes": "This attestation belongs to synthetic geometry, not canonical art"}
            (self.root / "qa" / f"P{i}.json").write_text(json.dumps(qa), encoding="utf-8")
        layout = {
            "version": 1,
            "page": {"id": "PAGE1", "width": 800, "height": 550,
                     "background": "#ffffff", "min_font_size": 18},
            "ledger": "dialogue.json",
            "font_path": str(FONT),
            "styles": {"speech": {
                "shape": "ellipse", "allowed_kinds": ["speech"],
                "tail_policy": "required", "fill": "#ffffff", "stroke": "#111111",
                "stroke_width": 3, "font_size": 26, "text_color": "#111111",
                "padding": [12, 16, 12, 16], "line_spacing": 1.15,
                "text_align": "center", "direction": "ltr", "tail_width": 15
            }},
            "panels": [
                {"id": "P1", "art": "approved/P1.png", "acceptance": "qa/P1.json",
                 "frame": {"rect": [20, 20, 370, 510]}, "fit": "contain",
                 "align": [0.5, 0.5], "border": {"color": "#111111", "width": 3},
                 "subjects": [{"character_id": "C1", "mouth": [205, 337],
                               "thought_anchor": [200, 280]}]},
                {"id": "P2", "art": "approved/P2.png", "acceptance": "qa/P2.json",
                 "frame": {"rect": [410, 20, 370, 510]}, "fit": "contain",
                 "align": [0.5, 0.5], "border": {"color": "#111111", "width": 3},
                 "subjects": []}
            ],
            "balloons": [] if silent else [{
                "id": "B1", "dialogue_id": "D1", "panel_id": "P1", "style": "speech",
                "box": [47, 43, 308, 145],
                "tail": {"kind": "on_panel", "character_id": "C1", "target": [205, 337]}
            }]
        }
        ledger = {"dialogue": [] if silent else [
            {"dialogue_id": "D1", "page_id": "PAGE1", "panel_id": "P1",
             "speaker_id": "C1", "kind": "speech", "reading_order": 1,
             "text": "We move at sunrise."}
        ]}
        self.layout_path.write_text(json.dumps(layout), encoding="utf-8")
        self.ledger_path.write_text(json.dumps(ledger), encoding="utf-8")

    def compose(self):
        cmd = [sys.executable, str(COMPOSITOR), str(self.layout_path), str(self.export)]
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr or done.stdout)
        self.assertEqual(len([name for name in ac.EXPORTS if (self.export / name).is_file()]), 5)

    def test_real_compositor_two_panel_exact_text(self):
        self.compose()
        report = ac.verify(self.layout_path, self.export,
                           workspace=self.root, font_roots=[FONT.parent])
        self.assertEqual(report["page_id"], "PAGE1")
        self.assertEqual(len(report["panels"]), 2)
        self.assertEqual(report["dialogue_ids"], ["D1"])
        self.assertEqual(report["affinity_import"]["native"], "pending_affinity_test")

    def test_real_compositor_detects_post_export_art_mutation(self):
        self.compose()
        source = self.root / "approved" / "P2.png"
        source.write_bytes(source.read_bytes() + b"mutated")
        with self.assertRaises(ac.ContractError) as exc:
            ac.verify(self.layout_path, self.export, self.root, [FONT.parent])
        self.assertIn("STALE_ART", str(exc.exception))

    def test_real_compositor_silent_page(self):
        self.create_case(silent=True)
        self.compose()
        report = ac.verify(self.layout_path, self.export,
                           workspace=self.root, font_roots=[FONT.parent])
        self.assertEqual(report["dialogue_ids"], [])


if __name__ == "__main__":
    unittest.main()
