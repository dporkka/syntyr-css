"""Regression coverage for standalone gallery adoption and honest browser guidance."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StandaloneActionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = 0
        self.copy_page = 0

    def handle_starttag(self, tag, attrs):
        properties = dict(attrs)
        if tag == "article" and "catalog-card" in properties.get("class", "").split():
            self.cards += 1
        if tag == "button" and "data-catalog-copy-page" in properties:
            self.copy_page += 1


class CatalogAdoptionContract(unittest.TestCase):
    def test_all_cards_have_optional_standalone_copy_and_non_js_source(self):
        page = (ROOT / "docs/catalog.html").read_text()
        parser = StandaloneActionParser()
        parser.feed(page)
        self.assertGreaterEqual(parser.cards, 49)
        self.assertEqual(parser.cards, parser.copy_page)
        self.assertIn("hidden data-catalog-copy-page", page)
        self.assertIn('class="catalog-source"', page)

    def test_standalone_copy_derives_the_required_css_and_scoped_body(self):
        js = (ROOT / "docs/catalog.js").read_text()
        self.assertIn("data-catalog-copy-page", js)
        self.assertIn("catalog-card-top .syn-badge", js)
        self.assertIn("syntyr.core.css", js)
        self.assertIn("new Set", js)
        self.assertIn('class="syn-root"', js)
        self.assertIn("navigator.clipboard.writeText", js)
        self.assertIn("textContent", js)
        self.assertNotIn("innerHTML =", js)

    def test_meter_example_advertises_its_real_semantic_stylesheet(self):
        page = (ROOT / "docs/catalog.html").read_text()
        meter = page.split('aria-labelledby="catalog-interaction-card-4"', 1)[1].split("</article>", 1)[0]
        self.assertIn("syntyr.core.css + syntyr.semantic.css", meter)

    def test_browser_support_and_accessible_fallbacks_are_visible_without_js(self):
        page = (ROOT / "docs/catalog.html").read_text()
        self.assertIn('id="catalog-browser-support"', page)
        for token in ("HTML Popover API", "Invoker Commands", "name grouping",
                      "Older browsers", "developer.mozilla.org"):
            self.assertIn(token, page)
        for heading in ("catalog-interaction-card-0", "catalog-interaction-card-2",
                        "catalog-native-popover-title"):
            self.assertIn(heading, page)

    def test_framework_snippets_and_layout_pathways_are_discoverable(self):
        page = (ROOT / "docs/catalog.html").read_text()
        for anchor in ("#hero-product", "#pricing-trio", "#layout-dashboard"):
            self.assertIn('blocks.html' + anchor, page)
        self.assertIn("framework-integrations.html", page)
        docs = (ROOT / "docs/framework-integrations.md").read_text()
        for feature in ("Copy a catalog example", "className=", "htmlFor=",
                        "<template>", "hx-get=", "syntyr.core.css"):
            self.assertIn(feature, docs)


if __name__ == "__main__":
    unittest.main()
