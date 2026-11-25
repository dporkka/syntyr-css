"""Contract for canonical, no-runtime-JS website sections in the editor."""
from pathlib import Path
from html.parser import HTMLParser
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
NEW = {
    "hero-photo": "Marketing",
    "before-after": "Portfolio",
    "resource-downloads": "Publishing",
    "press-highlights": "Marketing",
    "social-links": "Navigation",
    "product-specifications": "Commerce",
}


class Outline(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attrs = []
    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attrs.append(dict(attrs))


class SectionComposerTests(unittest.TestCase):
    def test_manifest_includes_every_copy_owned_section(self):
        manifest = json.loads((ROOT / "metadata/section-composer.v1.json").read_text())
        blocks = json.loads((ROOT / "blocks/manifest.json").read_text())["blocks"]
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual({item["id"] for item in manifest["sections"]},
                         {block["id"] for block in blocks})
        for item in manifest["sections"]:
            source = (ROOT / "blocks/snippets" / (item["id"] + ".html")).read_text().strip()
            self.assertEqual(item["html"], source)
            self.assertTrue(item["title"] and item["category"])
            self.assertEqual(item["required_stylesheets"][0], "syntyr.core.css")

    def test_six_new_sections_are_semantic_and_scriptless(self):
        blocks = json.loads((ROOT / "blocks/manifest.json").read_text())["blocks"]
        by_id = {block["id"]: block for block in blocks}
        for ident, category in NEW.items():
            with self.subTest(ident=ident):
                self.assertEqual(by_id[ident]["category"], category)
                source = (ROOT / "blocks/snippets" / (ident + ".html")).read_text()
                parsed = Outline()
                parsed.feed(source)
                self.assertIn("h2", parsed.tags)
                self.assertTrue(any("syn-root" in a.get("class", "").split() for a in parsed.attrs))
                self.assertNotIn("script", parsed.tags)
                self.assertNotIn("iframe", parsed.tags)
                self.assertNotIn('href="#"', source)
                self.assertNotIn("javascript:", source.lower())
        for name, required in {
            "hero-photo": {"figure", "img", "figcaption"},
            "before-after": {"figure", "img", "figcaption"},
            "resource-downloads": {"ul", "li", "a"},
            "press-highlights": {"article", "time"},
            "social-links": {"nav", "ul", "a"},
            "product-specifications": {"table", "caption", "th", "td"},
        }.items():
            parsed = Outline()
            parsed.feed((ROOT / "blocks/snippets" / (name + ".html")).read_text())
            self.assertTrue(required <= set(parsed.tags), name)

    def test_manifest_generation_is_repeatable(self):
        proc = subprocess.run([sys.executable, "scripts/build_section_composer.py", "--check"],
                              cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_public_builder_has_canonical_library_and_static_zip_controls(self):
        from scripts.build_cloudflare_site import source_files
        files = source_files()
        for path in ("metadata/section-composer.v1.json", "docs/page-builder-zip.mjs"):
            self.assertIn(path, files)
        html = (ROOT / "docs/page-builder.html").read_text()
        self.assertIn('id="builder-section-search"', html)
        self.assertIn('id="builder-section-category"', html)
        self.assertIn('id="builder-export-zip"', html)


if __name__ == "__main__":
    unittest.main()
