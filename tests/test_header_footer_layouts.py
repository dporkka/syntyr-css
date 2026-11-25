"""Contract for complementary CSS-first header and footer layouts."""
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADERS = {"header-centered", "header-split", "header-disclosure"}
FOOTERS = {"footer-compact", "footer-sitemap", "footer-newsletter"}
VARIANTS = HEADERS | FOOTERS


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attrs = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attrs.append((tag, dict(attrs)))


class HeaderFooterLayoutTests(unittest.TestCase):
    def test_layouts_are_copy_owned_core_navigation_sections(self):
        items = json.loads((ROOT / "blocks/manifest.json").read_text())["blocks"]
        by_id = {item["id"]: item for item in items}
        self.assertEqual(len(items), len(by_id))
        for ident in VARIANTS:
            with self.subTest(ident=ident):
                self.assertIn(ident, by_id)
                self.assertEqual(by_id[ident]["category"], "Navigation")
                self.assertEqual(by_id[ident]["modules"], ["core"])
                self.assertTrue(by_id[ident]["description"])

    def test_headers_and_footers_have_semantic_accessible_script_free_markup(self):
        for ident in VARIANTS:
            with self.subTest(ident=ident):
                source = (ROOT / "blocks/snippets" / f"{ident}.html").read_text()
                parser = Markup()
                parser.feed(source)
                expected = "header" if ident in HEADERS else "footer"
                self.assertEqual(parser.tags.count(expected), 1)
                self.assertIn("nav", parser.tags)
                self.assertTrue(any(tag == "nav" and attrs.get("aria-label")
                                    for tag, attrs in parser.attrs))
                self.assertTrue(any("syn-root" in attrs.get("class", "").split()
                                    for _, attrs in parser.attrs))
                self.assertNotIn("script", parser.tags)
                self.assertNotIn("iframe", parser.tags)
                self.assertNotIn('href="#"', source)
                self.assertNotIn("javascript:", source.lower())
                for tag, attrs in parser.attrs:
                    if tag == "a":
                        self.assertTrue(attrs.get("href", "").startswith("/"))

    def test_responsive_and_native_interaction_contract(self):
        for ident in HEADERS | FOOTERS:
            source = (ROOT / "blocks/snippets" / f"{ident}.html").read_text()
            self.assertTrue(any(token in source for token in ("syn-inline", "syn-grid", "syn-stack")))
        disclosure = Markup()
        disclosure.feed((ROOT / "blocks/snippets/header-disclosure.html").read_text())
        self.assertEqual(disclosure.tags.count("details"), 1)
        self.assertEqual(disclosure.tags.count("summary"), 1)
        newsletter = Markup()
        newsletter.feed((ROOT / "blocks/snippets/footer-newsletter.html").read_text())
        self.assertIn("form", newsletter.tags)
        self.assertTrue(any(tag == "input" and attrs.get("type") == "email"
                            and "required" in attrs for tag, attrs in newsletter.attrs))
        self.assertTrue(any(tag == "label" and attrs.get("for") == "syn-footer-newsletter-email"
                            for tag, attrs in newsletter.attrs))
        self.assertTrue(any(tag == "form" and attrs.get("method") == "post"
                            for tag, attrs in newsletter.attrs))

    def test_layouts_reach_gallery_registry_and_builder(self):
        gallery = (ROOT / "docs/blocks.html").read_text()
        registry = json.loads((ROOT / "registry/registry.json").read_text())
        sections = json.loads((ROOT / "metadata/section-composer.v1.json").read_text())
        names = {item["name"] for item in registry["items"]}
        section_ids = {section["id"] for section in sections["sections"]}
        for ident in VARIANTS:
            with self.subTest(ident=ident):
                self.assertEqual(gallery.count(f'data-block-id="{ident}"'), 1)
                self.assertIn(ident, names)
                self.assertIn(ident, section_ids)


if __name__ == "__main__":
    unittest.main()
