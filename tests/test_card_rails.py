"""Cross-theme, zero-JavaScript scrollable card rail contract."""

from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []

    def handle_starttag(self, tag, attrs):
        self.items.append((tag, dict(attrs)))


class CardRailContractTests(unittest.TestCase):
    def test_rail_layout_is_opt_in_native_and_composable(self):
        css = (ROOT / "src/recipes.css").read_text(encoding="utf-8")
        for required in (
            "&.syn-card-rail", "&.syn-card-rail__heading",
            "&.syn-card-rail__track", "scroll-snap-type: inline proximity",
            "overflow-x: auto", "scroll-snap-align: start",
            "overscroll-behavior-inline: contain", "--syn-card-rail-width",
            ":focus-visible", "prefers-reduced-motion: reduce",
            "forced-colors: active",
        ):
            with self.subTest(required=required):
                self.assertIn(required, css)
        from sys import path as sys_path
        sys_path.insert(0, str(ROOT / "scripts"))
        from build import distributions
        self.assertIn("recipes.css", distributions()["syntyr.recipes.css"])
        self.assertNotIn("recipes.css", distributions()["syntyr.core.css"])

    def test_gallery_rails_are_accessible_and_zero_js(self):
        html = (ROOT / "examples/card-rails.html").read_text(encoding="utf-8")
        elements = Elements()
        elements.feed(html)
        self.assertNotIn("script", [name for name, _ in elements.items])
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)
        self.assertIn("../dist/syntyr.recipes.css", html)
        self.assertIn("syn-card-rail__track", html)
        headings = {attrs.get("id") for _, attrs in elements.items if attrs.get("id")}
        tracks = [attrs for _, attrs in elements.items
                  if "syn-card-rail__track" in attrs.get("class", "").split()]
        self.assertGreaterEqual(len(tracks), 2)
        for attrs in tracks:
            self.assertEqual(attrs.get("tabindex"), "0")
            self.assertEqual(attrs.get("role"), "list")
            self.assertIn(attrs.get("aria-labelledby"), headings)
        self.assertTrue(all(attrs.get("href") for tag, attrs in elements.items if tag == "a"))

    def test_recipe_and_public_example_are_discoverable(self):
        self.assertIn("syn-card-rail", (ROOT / "docs/recipes.md").read_text())
        self.assertIn('"card-rails.html"', (ROOT / "scripts/build_cloudflare_site.py").read_text())
        self.assertIn("card-rails.html", (ROOT / "docs/index.html").read_text())


if __name__ == "__main__":
    unittest.main()
