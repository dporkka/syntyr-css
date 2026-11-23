"""Optional ASCII effects are independently distributable and script-free."""
import json
from pathlib import Path
import unittest
from scripts.build import distributions

ROOT = Path(__file__).resolve().parents[1]


class AsciiEffectsContract(unittest.TestCase):
    def test_optional_distribution(self):
        modules = distributions()
        self.assertEqual(modules["syntyr.ascii.css"], ("ascii.css",))
        self.assertIn("ascii.css", modules["syntyr.all.css"])
        for name in ("syntyr.core.css", "syntyr.css", "syntyr.symbols.css"):
            self.assertNotIn("ascii.css", modules[name])
        self.assertEqual(json.loads((ROOT / "package.json").read_text())["exports"]["./ascii.css"],
                         "./dist/syntyr.ascii.css")

    def test_scoped_effects_and_accessibility_guards(self):
        css = (ROOT / "src/ascii.css").read_text()
        for name in ("gradient", "dither", "phosphor", "scan", "typewriter", "wave", "rain", "decode", "cursor", "loader"):
            self.assertIn(".syn-ascii--" + name, css)
        self.assertIn(":where(.syn-root, .syn-root *)", css)
        for preference in ("prefers-reduced-motion: reduce", "forced-colors: active", "prefers-contrast: more", "@media print"):
            self.assertIn(preference, css)
        self.assertNotIn("infinite", css)
        self.assertNotIn("url(", css)
        self.assertNotIn("@import", css)

    def test_gallery_is_static_and_discoverable(self):
        gallery = (ROOT / "examples/ascii.html").read_text()
        self.assertNotIn("<script", gallery.lower())
        self.assertGreaterEqual(gallery.count("<article"), 15)
        self.assertIn("syntyr.ascii.css", gallery)
        self.assertIn("aria-hidden=\"true\"", gallery)
        self.assertIn("../examples/ascii.html", (ROOT / "docs/index.html").read_text())

    def test_hero_gallery_copyable_and_script_free(self):
        from html.parser import HTMLParser
        class Inspect(HTMLParser):
            def __init__(self):
                super().__init__()
                self.snippets = []
                self.inside = False
            def handle_starttag(self, tag, attrs):
                if tag == "textarea":
                    self.inside = True
                    self.snippets.append("")
            def handle_endtag(self, tag):
                if tag == "textarea":
                    self.inside = False
            def handle_data(self, data):
                if self.inside:
                    self.snippets[-1] += data
        html = (ROOT / "examples/ascii-heroes.html").read_text()
        parser = Inspect()
        parser.feed(html)
        self.assertEqual(len(parser.snippets), 3)
        self.assertNotIn("<script", html)
        for snippet in parser.snippets:
            self.assertIn('class="syn-root syn-region"', snippet)
            self.assertIn('aria-hidden="true"', snippet)
            self.assertIn('href="/start"', snippet)
            self.assertIn("<h2", snippet)
