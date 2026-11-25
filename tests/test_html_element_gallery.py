"""Free HTML element catalog covers common browser-native elements and categories."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_CATEGORIES = {
    "typography", "forms", "layout", "navigation",
    "data", "media", "interactive", "marketing",
}
REQUIRED_TAGS = {
    "h2", "p", "strong", "em", "mark", "small", "code", "pre", "kbd",
    "ul", "ol", "li", "dl", "dt", "dd", "section", "article",
    "header", "footer", "nav", "button", "form", "label", "input",
    "select", "option", "fieldset", "legend", "textarea", "table",
    "thead", "tbody", "tr", "th", "td", "caption", "picture", "source",
    "img", "figure", "figcaption", "details", "summary", "dialog",
    "progress", "meter", "output", "time", "data",
}


class GalleryParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = []
        self.preview_tags = set()

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "article" and "catalog-card" in attrs.get("class", "").split():
            self.cards.append(attrs)


class TagCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = set()

    def handle_starttag(self, tag, attrs):
        self.tags.add(tag)


class HtmlElementGalleryTests(unittest.TestCase):
    def test_native_popover_uses_overlay_class_in_preview_and_source(self):
        html = (ROOT / "docs/catalog.html").read_text(encoding="utf-8")
        self.assertIn('<div id="catalog-help-popover" popover class="syn-popover">', html)
        self.assertIn(
            'id=&quot;catalog-help-popover&quot; popover class=&quot;syn-popover&quot;',
            html,
        )
        self.assertNotIn('id="catalog-help-popover" popover class="syn-panel"', html)

    def test_gallery_exposes_complete_free_categories(self):
        html = (ROOT / "docs/catalog.html").read_text(encoding="utf-8")
        gallery = GalleryParser()
        gallery.feed(html)
        self.assertGreaterEqual(len(gallery.cards), 24)
        self.assertEqual({c.get("data-catalog-category") for c in gallery.cards},
                         REQUIRED_CATEGORIES)
        self.assertTrue(all(c.get("data-catalog-keywords") for c in gallery.cards))
        self.assertIn('id="catalog-category"', html)

    def test_gallery_previews_cover_high_value_native_html(self):
        html = (ROOT / "docs/catalog.html").read_text(encoding="utf-8")
        gallery = GalleryParser()
        gallery.feed(html)
        previews = re.findall(
            r'<div class="catalog-preview">\n(.*?)\n          </div>\n          <details class="catalog-code-details">',
            html, re.S)
        for preview in previews:
            collector = TagCollector()
            collector.feed(preview)
            gallery.preview_tags.update(collector.tags)
        self.assertIn("<main ", html)
        self.assertFalse(REQUIRED_TAGS - gallery.preview_tags,
                         f"Missing native previews: {sorted(REQUIRED_TAGS - gallery.preview_tags)}")

    def test_category_search_is_optional_progressive_enhancement(self):
        html = (ROOT / "docs/catalog.html").read_text(encoding="utf-8")
        script = (ROOT / "docs/catalog.js").read_text(encoding="utf-8")
        self.assertIn('id="catalog-controls" class="catalog-controls" hidden', html)
        self.assertIn("catalog-category", script)
        self.assertIn("data-catalog-category", html)
        self.assertIn("card.hidden =", script)
        self.assertNotIn("innerHTML =", script)


if __name__ == "__main__":
    unittest.main()
