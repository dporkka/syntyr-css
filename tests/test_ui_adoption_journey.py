"""Regression coverage for a release-honest, consistent Syntyr adoption journey."""
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "index.html",
    "docs/index.html",
    "docs/catalog.html",
    "docs/blocks.html",
)
PRIMARY_LABELS = ("Get started", "Components", "Blocks", "Free tools", "Docs", "GitHub")


class Navigation(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = None
        self.depth = 0
        self.primary = []
        self.mobile = []
        self._in_link = False
        self._href = ""
        self._label = ""

    def handle_starttag(self, tag, attrs):
        props = dict(attrs)
        if tag == "nav" and props.get("aria-label") in ("Main navigation", "Mobile navigation"):
            self.active = "mobile" if props["aria-label"] == "Mobile navigation" else "primary"
            self.depth = 1
        elif self.active and tag == "nav":
            self.depth += 1
        if self.active and tag == "a":
            self._in_link = True
            self._href = props.get("href", "")
            self._label = ""

    def handle_data(self, data):
        if self._in_link:
            self._label += data

    def handle_endtag(self, tag):
        if tag == "a" and self._in_link:
            (self.mobile if self.active == "mobile" else self.primary).append(
                (unescape(self._label.strip()), self._href)
            )
            self._in_link = False
        if tag == "nav" and self.active:
            self.depth -= 1
            if self.depth == 0:
                self.active = None


class AdoptionJourneyTests(unittest.TestCase):
    def test_all_primary_headers_use_six_clear_destinations(self):
        for page in PAGES:
            with self.subTest(page=page):
                nav = Navigation()
                nav.feed((ROOT / page).read_text(encoding="utf-8"))
                self.assertEqual(tuple(label for label, _ in nav.primary[:6]), PRIMARY_LABELS)
                self.assertEqual(tuple(label for label, _ in nav.mobile[:6]), PRIMARY_LABELS)
                for _, href in nav.primary:
                    self.assertTrue(href and not href.startswith("javascript:"))

    def test_all_long_documentation_galleries_offer_a_native_mobile_menu(self):
        for page in ("docs/catalog.html", "docs/blocks.html"):
            with self.subTest(page=page):
                html = (ROOT / page).read_text(encoding="utf-8")
                self.assertIn('class="syn-header syn-shell docs-header"', html)
                self.assertIn('class="site-mobile-menu"', html)
                self.assertIn('<summary>Menu</summary>', html)

    def test_responsive_docs_navigation_requires_replacement_menu(self):
        css = (ROOT / "docs/docs.css").read_text(encoding="utf-8")
        how_to = (ROOT / "docs/how-to.html").read_text(encoding="utf-8")
        self.assertIn('class="syn-header docs-header"', how_to)
        self.assertNotIn('class="site-mobile-menu"', how_to)
        self.assertNotIn(".docs-header .syn-nav { display: none; }", css)
        self.assertIn(".docs-header:has(> .site-mobile-menu) .syn-nav { display: none; }", css)

    def test_every_catalog_card_is_labeled_as_unreleased(self):
        catalog = (ROOT / "docs/catalog.html").read_text(encoding="utf-8")
        self.assertIn('id="catalog-release-scope"', catalog)
        self.assertIn('href="index.html#install"', catalog)
        self.assertEqual(catalog.count('class="catalog-release-label"'), 49)
        self.assertIn("Unreleased alpha.5", catalog)

    def test_blocks_gallery_and_generator_share_unreleased_label(self):
        for page in ("docs/blocks.html", "scripts/build_blocks.py"):
            with self.subTest(page=page):
                source = (ROOT / page).read_text(encoding="utf-8")
                self.assertIn('id="blocks-release-scope"', source)
                self.assertIn('href="index.html#install"', source)
                self.assertIn("Unreleased alpha.5", source)


if __name__ == "__main__":
    unittest.main()
