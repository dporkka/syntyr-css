"""Keep README screenshot paths, capture definitions and publication in sync."""
import re
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReadmeShowcaseTests(unittest.TestCase):
    def test_capture_manifest_matches_readme_and_publication(self):
        from scripts.capture_readme import CAPTURES

        readme = (ROOT / "README.md").read_text()
        site = (ROOT / "scripts/build_cloudflare_site.py").read_text()
        images = set(re.findall(r"assets/readme/([\w-]+\.png)", readme))
        self.assertEqual(images, {capture.filename for capture in CAPTURES})
        for capture in CAPTURES:
            with self.subTest(capture=capture.filename):
                self.assertTrue((ROOT / capture.source).is_file())
                self.assertIn(f'"assets/readme/{capture.filename}"', site)
                data = (ROOT / "assets/readme" / capture.filename).read_bytes()
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                width, height = struct.unpack(">II", data[16:24])
                self.assertEqual(width, capture.width)
                if capture.full_page:
                    self.assertGreaterEqual(height, capture.height)
                else:
                    self.assertEqual(height, capture.height)
        self.assertTrue(any(c.width == 390 for c in CAPTURES))
        self.assertTrue(any(c.source == "examples/themes.html" and c.full_page
                            for c in CAPTURES))

    def test_published_size_comparison_matches_immutable_assets(self):
        import gzip

        readme = (ROOT / "README.md").read_text()
        release = ROOT / "site-releases/0.3.0-alpha.4"
        for label, filename in (("Core (default)", "syntyr.core.css"),
                                ("Core + effects", "syntyr.css"),
                                ("All modules", "syntyr.all.css")):
            size = len(gzip.compress((release / filename).read_bytes(), mtime=0))
            self.assertRegex(readme, rf"\| {re.escape(label)} \|[^\n]+\| {size:,} \|")
