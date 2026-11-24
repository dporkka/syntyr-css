"""Contracts for copy-owned, semantic and reusable content section layouts."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = {
    "editorial-intro-split": "Editorial",
    "article-toc": "Editorial",
    "feature-rows": "Marketing",
    "impact-narrative": "Marketing",
    "decision-guide": "Services",
    "faq-sidecar": "Services",
    "resource-index": "Publishing",
    "principles-columns": "Company",
}


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attrs = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attrs.append((tag, dict(attrs)))


class ContentSectionLayoutTests(unittest.TestCase):
    def test_eight_independent_core_blocks(self):
        blocks = json.loads((ROOT / "blocks/manifest.json").read_text())["blocks"]
        names = [block["id"] for block in blocks]
        self.assertEqual(len(names), len(set(names)))
        by_id = {item["id"]: item for item in blocks}
        for ident, category in SECTIONS.items():
            with self.subTest(ident=ident):
                self.assertIn(ident, by_id)
                self.assertEqual(by_id[ident]["category"], category)
                self.assertEqual(by_id[ident]["modules"], ["core"])
                self.assertTrue(by_id[ident]["title"] and by_id[ident]["tags"])

    def test_accessible_heading_hierarchy_and_working_destinations(self):
        ids_seen = set()
        for ident in SECTIONS:
            with self.subTest(ident=ident):
                snippet = (ROOT / "blocks/snippets" / f"{ident}.html").read_text()
                parsed = Elements()
                parsed.feed(snippet)
                self.assertEqual(parsed.tags[0], "section")
                self.assertIn("h2", parsed.tags)
                self.assertNotIn("script", parsed.tags)
                self.assertNotIn("iframe", parsed.tags)
                self.assertNotIn('href="#"', snippet)
                self.assertNotIn("javascript:", snippet.lower())
                self.assertNotIn("https://", snippet)
                self.assertIn("syn-root", parsed.attrs[0][1].get("class", "").split())
                heading = parsed.attrs[0][1].get("aria-labelledby")
                local_ids = {attrs["id"] for _, attrs in parsed.attrs if attrs.get("id")}
                self.assertIn(heading, local_ids)
                self.assertFalse(ids_seen & local_ids, f"duplicate IDs across layouts: {ident}")
                ids_seen |= local_ids
                for tag, attrs in parsed.attrs:
                    if tag == "a":
                        href = attrs.get("href", "")
                        self.assertTrue(href.startswith("/") or href.startswith("#syn-"), href)
                        if href.startswith("#"):
                            self.assertIn(href[1:], local_ids)
                    if tag in {"h3", "h4"}:
                        self.assertIn("h2", parsed.tags)

    def test_distinct_intrinsic_layouts_and_native_disclosures(self):
        for ident in SECTIONS:
            source = (ROOT / "blocks/snippets" / f"{ident}.html").read_text()
            self.assertTrue(any(x in source for x in ("syn-grid", "syn-sidecar", "syn-stack")))
            self.assertNotIn("style=\"display:none\"", source)
        for ident in ("editorial-intro-split", "article-toc", "feature-rows", "impact-narrative", "faq-sidecar"):
            self.assertIn("syn-sidecar", (ROOT / "blocks/snippets" / f"{ident}.html").read_text(), ident)
        toc = Elements()
        toc.feed((ROOT / "blocks/snippets/article-toc.html").read_text())
        self.assertTrue(any(tag == "nav" and attrs.get("aria-label") for tag, attrs in toc.attrs))
        self.assertGreaterEqual(sum(1 for tag, attrs in toc.attrs if tag == "a" and attrs.get("href", "").startswith("#")), 2)
        faq = Elements()
        faq.feed((ROOT / "blocks/snippets/faq-sidecar.html").read_text())
        self.assertGreaterEqual(faq.tags.count("details"), 2)
        self.assertEqual(faq.tags.count("details"), faq.tags.count("summary"))
        index = Elements()
        index.feed((ROOT / "blocks/snippets/resource-index.html").read_text())
        self.assertGreaterEqual(sum(1 for tag in index.tags if tag == "nav"), 2)

    def test_gallery_registry_and_section_composer_have_all_blocks(self):
        gallery = (ROOT / "docs/blocks.html").read_text()
        registry = json.loads((ROOT / "registry/registry.json").read_text())
        composer = json.loads((ROOT / "metadata/section-composer.v1.json").read_text())
        by_name = {item["name"] for item in registry["items"]}
        by_section = {item["id"]: item for item in composer["sections"]}
        for ident in SECTIONS:
            with self.subTest(ident=ident):
                self.assertEqual(gallery.count(f'data-block-id="{ident}"'), 1)
                self.assertIn(ident, by_name)
                self.assertIn(ident, by_section)
                source = (ROOT / "blocks/snippets" / f"{ident}.html").read_text().strip()
                self.assertEqual(by_section[ident]["html"], source)
                self.assertEqual(by_section[ident]["required_stylesheets"], ["syntyr.core.css"])


if __name__ == "__main__":
    unittest.main()
