"""Additional free components and sections with honest Premium navigation."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = {
    "catalog-skip-link-title": "Skip navigation link",
    "catalog-status-list-title": "Status indicator list",
    "catalog-activity-entry-title": "Activity timeline",
    "catalog-property-list-title": "Key-value details",
    "catalog-link-card-title": "Linked resource card",
    "catalog-section-actions-title": "Section header with actions",
}
SECTIONS = {
    "feature-spotlight": "Marketing",
    "trust-assurance": "Marketing",
    "event-registration": "Marketing",
    "help-center": "Applications",
    "notification-center": "Applications",
    "api-endpoint-reference": "Technical",
}
DESTINATIONS = {
    "blocks.html": "Free sections",
    "premium-compositions.html": "Premium-inspired",
    "console-kit.html": "Console Kit",
    "products.html": "Products",
}


class ComponentAndPremiumPathTests(unittest.TestCase):
    def test_component_examples_are_copyable_and_indexed(self):
        source = (ROOT / "docs/catalog.html").read_text()
        for heading_id, title in COMPONENTS.items():
            with self.subTest(heading_id=heading_id):
                self.assertIn(f'<h2 class="syn-heading" id="{heading_id}">{title}</h2>', source)
                self.assertIn(f'class="catalog-index-link" href="#{heading_id}"', source)
                self.assertIn(f'href="#{heading_id}-preview"', source)
                self.assertIn(f'href="playground.html#component={heading_id}"', source)
        self.assertIn("49 examples available.", source)

    def test_six_additional_free_sections_are_source_owned(self):
        manifest = json.loads((ROOT / "blocks/manifest.json").read_text())["blocks"]
        by_id = {item["id"]: item for item in manifest}
        self.assertEqual(len(manifest), 56)
        self.assertEqual(len(by_id), 56)
        for ident, category in SECTIONS.items():
            with self.subTest(ident=ident):
                self.assertIn(ident, by_id)
                self.assertEqual(by_id[ident]["category"], category)
                self.assertIn("core", by_id[ident]["modules"])
                snippet = (ROOT / "blocks/snippets" / (ident + ".html")).read_text()
                self.assertIn('class="syn-root', snippet)
                self.assertRegex(snippet, r"<h2\b")
                self.assertNotIn("<script", snippet)
                self.assertNotIn('href="#"', snippet)
                gallery = (ROOT / "docs/blocks.html").read_text()
                self.assertIn(f'data-block-id="{ident}"', gallery)
                self.assertIn(f'block-title-{ident}', gallery)
                self.assertIn("56 blocks available.", gallery)

    def test_crosslinks_have_real_destinations_and_distinguish_availability(self):
        catalog = (ROOT / "docs/catalog.html").read_text()
        blocks = (ROOT / "docs/blocks.html").read_text()
        for name, label in DESTINATIONS.items():
            with self.subTest(name=name):
                self.assertTrue((ROOT / "docs" / name).is_file())
                self.assertIn(f'href="{name}"', catalog)
                self.assertIn(f'href="{name}"', blocks)
                self.assertIn(label, catalog)
                self.assertIn(label, blocks)
        self.assertIn("not available for purchase", catalog.lower())
        self.assertIn("not available for purchase", blocks.lower())
        self.assertIn('href="../examples/premium-compositions.html"', catalog)
        self.assertIn('href="../examples/premium-compositions.html"', blocks)

    def test_registry_and_playground_reflect_real_inventory(self):
        index = json.loads((ROOT / "registry/registry.json").read_text())
        names = {item["name"] for item in index["items"]}
        self.assertTrue(set(SECTIONS) <= names)
        playground = (ROOT / "docs/playground-catalog.js").read_text()
        for ident in SECTIONS:
            self.assertIn('"id": "block-' + ident + '"', playground)
        for ident in COMPONENTS:
            self.assertIn('"id": "' + ident + '"', playground)


if __name__ == "__main__":
    unittest.main()
