"""Repository packaging, instruction safety and documentation link checks."""
from __future__ import annotations

import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_skill_frontmatter_and_trigger(self):
        body = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(body.startswith("---\n"))
        start, meta, _ = body.split("---", 2)
        self.assertIn("name: affinity", meta)
        self.assertIn("description:", meta)
        self.assertIn("Desktop Commander", body)
        self.assertIn("agent-mangaka", body)
        self.assertIn("offline", body.lower())

    def test_referenced_markdown_files_exist(self):
        paths = [ROOT / "README.md", ROOT / "SKILL.md"]
        paths.extend(sorted((ROOT / "references").glob("*.md")))
        self.assertGreaterEqual(len(paths), 8)
        failures = []
        for source in paths:
            text = source.read_text(encoding="utf-8")
            for ref in re.findall(r"\[[^\]]+\]\(([^)\s]+)\)", text):
                if "://" in ref or ref.startswith(("mailto:", "#")):
                    continue
                dest = (source.parent / ref.split("#", 1)[0]).resolve()
                if not dest.exists() or (dest != ROOT and ROOT not in dest.parents):
                    failures.append(f"{source.relative_to(ROOT)} -> {ref}")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_no_em_dash_or_private_artifacts_in_repo(self):
        roots = ("SKILL.md", "README.md", "agents", "references", "scripts", "tests")
        for part in roots:
            path = ROOT / part
            for item in ([path] if path.is_file() else path.rglob("*")):
                if not item.is_file() or item.suffix not in (".md", ".py", ".js", ".ps1", ".yaml", ".yml"):
                    continue
                text = item.read_text(encoding="utf-8")
                self.assertNotIn("\u2014", text, f"No em dashes: {item.relative_to(ROOT)}")
                private_key_marker = "-----BEGIN " + "PRIVATE KEY-----"
                self.assertNotIn(private_key_marker, text)

    def test_required_instruction_topics_exist(self):
        topics = {
            "references/desktop-routing.md": ["Claude", "deviceId", "GUI"],
            "references/affinity-operations.md": ["Layers", "native", "PNG"],
            "references/comic-production.md": ["world", "balloon", "RTL"],
            "references/qa-and-publication.md": ["speaker", "native", "visual"],
            "references/recovery.md": ["retry", "corrupt", "hash"],
            "references/scripting.md": ["JavaScript", "beta", "read-only"],
            "references/mangaka-integration.md": ["compose_page.py", "composite.png", "art_sha256"],
            "references/evaluation.md": ["not_tested", "Affinity", "tests"],
        }
        for path, needles in topics.items():
            text = (ROOT / path).read_text(encoding="utf-8")
            for needle in needles:
                self.assertIn(needle, text, f"{needle} missing in {path}")

    def test_no_untracked_test_image_artifacts(self):
        extensions = {".png", ".jpg", ".jpeg", ".webp", ".psd", ".ora", ".af", ".afpub"}
        unexpected = [str(x.relative_to(ROOT))
                      for x in ROOT.rglob("*") if x.is_file()
                      and ".git" not in x.parts and x.suffix.lower() in extensions]
        self.assertEqual(unexpected, [])


if __name__ == "__main__":
    unittest.main()
