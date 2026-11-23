"""Regression contracts for six reusable, script-free Core website sections."""
from html.parser import HTMLParser
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "company-story": ("Company", {"ol", "li"}),
    "customer-reviews": ("Marketing", {"figure", "blockquote", "figcaption"}),
    "use-case-showcase": ("Marketing", {"article", "a"}),
    "locations-hours": ("Services", {"address", "dl", "dt", "dd"}),
    "careers-listings": ("Company", {"ul", "li", "a"}),
    "feature-disclosures": ("Marketing", {"details", "summary"}),
}

class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.seen = set()
        self.attributes = []

    def handle_starttag(self, tag, attrs):
        self.seen.add(tag)
        self.attributes.append((tag, dict(attrs)))

class CoreSectionExpansionTests(unittest.TestCase):
    def test_sections_are_available_as_independent_copyable_blocks(self):
        blocks = json.loads((ROOT / "blocks/manifest.json").read_text())["blocks"]
        by_id = {block["id"]: block for block in blocks}
        self.assertEqual(len(blocks), 99)
        for name, (category, required) in EXPECTED.items():
            with self.subTest(section=name):
                self.assertIn(name, by_id)
                self.assertEqual(by_id[name]["category"], category)
                self.assertEqual(by_id[name]["modules"], ["core"])
                source = (ROOT / "blocks/snippets" / f"{name}.html").read_text()
                parsed = Tags()
                parsed.feed(source)
                self.assertTrue(required <= parsed.seen, required - parsed.seen)
                self.assertIn("h2", parsed.seen)
                self.assertTrue(any("syn-root" in a.get("class", "").split() for _, a in parsed.attributes))
                self.assertTrue(any(a.get("aria-labelledby") for _, a in parsed.attributes))
                self.assertNotIn("script", parsed.seen)
                self.assertNotIn("iframe", parsed.seen)
                self.assertNotIn('href="#"', source)
                self.assertNotIn("javascript:", source.lower())
                self.assertNotIn("https://", source)

    def test_reviews_clearly_label_example_quotes(self):
        source = (ROOT / "blocks/snippets/customer-reviews.html").read_text().lower()
        self.assertIn("illustrative", source)
        self.assertNotIn('itemprop="ratingvalue"', source)

    def test_feature_switcher_does_not_pretend_to_be_aria_tabs(self):
        source = (ROOT / "blocks/snippets/feature-disclosures.html").read_text()
        parsed = Tags()
        parsed.feed(source)
        details = [a for t, a in parsed.attributes if t == "details"]
        self.assertGreaterEqual(len(details), 3)
        self.assertEqual(len({a.get("name") for a in details}), 1)
        self.assertTrue(details[0].get("name"))
        self.assertNotIn('role="tab"', source)
        self.assertNotIn('role="tabpanel"', source)

    def test_career_and_use_case_destinations_are_real_navigation(self):
        for name in ("careers-listings", "use-case-showcase"):
            source = (ROOT / "blocks/snippets" / f"{name}.html").read_text()
            parsed = Tags()
            parsed.feed(source)
            links = [a.get("href") for t, a in parsed.attributes if t == "a"]
            self.assertTrue(links)
            self.assertTrue(all(link and link.startswith("/") and link != "/" for link in links))

if __name__ == "__main__":
    unittest.main()
