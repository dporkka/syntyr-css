"""Opt-in icon, Unicode, and ASCII composition contract."""
from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build import distributions  # noqa: E402


class SymbolMarkup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class OptionalSymbolsContract(unittest.TestCase):
    def test_symbols_are_separate_from_core_and_recipes(self):
        manifests = distributions()
        self.assertEqual(manifests["syntyr.symbols.css"], ("symbols.css",))
        self.assertIn("symbols.css", manifests["syntyr.all.css"])
        self.assertNotIn("symbols.css", manifests["syntyr.core.css"])
        self.assertNotIn("symbols.css", manifests["syntyr.recipes.css"])
        self.assertNotIn("symbols.css", manifests["syntyr.css"])

    def test_icon_supports_svg_and_contained_svg_without_forcing_stroke_or_fill(self):
        css = (ROOT / "src/symbols.css").read_text(encoding="utf-8")
        self.assertIn("@layer syn.symbols", css)
        self.assertIn(".syn-icon", css)
        self.assertIn(".syn-icon > svg", css)
        self.assertIn("--syn-icon-size", css)
        self.assertNotIn("stroke-width:", css)
        self.assertNotIn("fill: none", css)
        self.assertNotIn("@import", css)
        self.assertNotIn("url(", css)

    def test_opt_in_icon_motion_presets_are_scoped_and_respect_preferences(self):
        css = (ROOT / "src/symbols.css").read_text(encoding="utf-8")
        for preset in ("spin", "pulse", "bounce", "shake", "wiggle", "pop"):
            with self.subTest(preset=preset):
                self.assertIn(".syn-icon--" + preset, css)
                self.assertIn("@keyframes syn-icon-" + preset, css)
        for token in ("--syn-icon-motion-duration", "--syn-icon-motion-iterations",
                      "--syn-icon-motion-easing", ".syn-icon--on-interact",
                      "prefers-reduced-motion: reduce", "animation: none"):
            self.assertIn(token, css)
        self.assertNotIn("@import", css)
        self.assertNotIn("url(", css)
        guide = (ROOT / "docs/symbols.md").read_text(encoding="utf-8")
        self.assertIn("syn-icon--spin", guide)
        self.assertIn("syn-icon--on-interact", guide)
        self.assertIn("prefers-reduced-motion", guide)

    def test_unicode_and_ascii_preserve_text_and_alignment(self):
        css = (ROOT / "src/symbols.css").read_text(encoding="utf-8")
        for fragment in (".syn-symbol", ".syn-symbol--accent",
                         ".syn-symbol--muted", ".syn-ascii",
                         "white-space: pre", "overflow-x: auto",
                         "font-variant-ligatures: none", "var(--syn-mono"):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, css)
        self.assertNotIn("content:", css, "meaningful symbols must be real DOM text")

    def test_documented_examples_are_accessible_and_dependency_free(self):
        example = (ROOT / "examples/symbols.html").read_text(encoding="utf-8")
        guide = (ROOT / "docs/symbols.md").read_text(encoding="utf-8")
        parsed = SymbolMarkup()
        parsed.feed(example)
        self.assertTrue(any(t == "svg" and a.get("aria-hidden") == "true"
                            for t, a in parsed.tags))
        self.assertTrue(any(t == "button" and a.get("aria-label")
                            for t, a in parsed.tags))
        self.assertTrue(any(t == "pre" and a.get("aria-hidden") == "true"
                            for t, a in parsed.tags))
        self.assertIn("syntyr.symbols.css", example)
        self.assertIn("syn-ascii", example)
        self.assertIn("syn-symbol", example)
        self.assertNotIn("<script", example.lower())
        self.assertNotIn("<script", guide.lower())
        self.assertIn("screen reader", guide.lower())
        self.assertIn("Lucide", guide)
        self.assertIn("NO_COLOR", guide)

    def test_every_symbol_rule_is_scoped_to_a_syntyr_root(self):
        css = (ROOT / "src/symbols.css").read_text(encoding="utf-8")
        # Each selector must support both an element inside .syn-root and the
        # root element when it also carries the presentation class.
        for name in ("syn-icon", "syn-icon > svg", "syn-symbol",
                     "syn-symbol--accent", "syn-symbol--muted", "syn-ascii",
                     "syn-ascii--accent", "syn-ascii--muted"):
            with self.subTest(selector=name):
                self.assertIn(".syn-root ." + name, css)
                self.assertIn(".syn-root." + name, css)

    def test_hidden_text_art_has_matching_visible_equivalents(self):
        example = (ROOT / "examples/symbols.html").read_text(encoding="utf-8")
        guide = (ROOT / "docs/symbols.md").read_text(encoding="utf-8")
        self.assertIn("API online and jobs online", example)
        self.assertIn("Gateway healthy and queue connected", example)
        self.assertIn("API online and jobs online", guide)

    def test_docs_and_gallery_discover_new_module(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        gallery = (ROOT / "docs/index.html").read_text(encoding="utf-8")
        self.assertIn("syntyr.symbols.css", readme)
        self.assertIn("docs/symbols.md", readme)
        self.assertIn('../examples/symbols.html', gallery)


if __name__ == "__main__":
    unittest.main()
