"""Contract tests for the portable SaaS and business block collection."""
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MARKETING = {
    "scrollable-card-rail", "bento-feature-grid", "hero-product-preview",
    "feature-spotlight-detail", "customer-case-study", "pricing-comparison",
}
APPLICATIONS = {
    "auth-sign-up", "resource-crud", "organization-members",
    "billing-usage", "integration-connection", "developer-api-settings",
}

class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attrs = []
        self.ids = []
        self.labels = []
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        self.tags.append(tag)
        self.attrs.append((tag, data))
        if data.get("id"):
            self.ids.append(data["id"])
        if data.get("aria-labelledby"):
            self.labels.extend(data["aria-labelledby"].split())

class SaaSBusinessCollectionTests(unittest.TestCase):
    def test_manifest_has_twelve_new_blocks_without_losing_prior_library(self):
        blocks = json.loads((ROOT / "blocks/manifest.json").read_text())["blocks"]
        by_id = {b["id"]: b for b in blocks}
        self.assertEqual(len(blocks), 102)
        self.assertEqual(len(by_id), len(blocks))
        for ident in MARKETING:
            self.assertEqual(by_id[ident]["category"], "Marketing")
        for ident in APPLICATIONS:
            self.assertEqual(by_id[ident]["category"], "Applications")
        self.assertTrue(all("core" in by_id[i]["modules"] for i in MARKETING | APPLICATIONS))

    def test_every_new_block_is_semantically_independent_and_has_real_destinations(self):
        for ident in MARKETING | APPLICATIONS:
            with self.subTest(block=ident):
                html = (ROOT / "blocks/snippets" / f"{ident}.html").read_text()
                parsed = Elements()
                parsed.feed(html)
                self.assertIn("h2", parsed.tags)
                self.assertIn("syn-root", html)
                self.assertEqual(len(parsed.ids), len(set(parsed.ids)))
                self.assertTrue(parsed.labels)
                self.assertTrue(set(parsed.labels) <= set(parsed.ids))
                self.assertNotIn("<script", html)
                self.assertNotIn("javascript:", html)
                self.assertNotIn('href="#"', html)
                self.assertNotIn('action="#"', html)
                for tag, attrs in parsed.attrs:
                    if tag == "a":
                        self.assertTrue(attrs.get("href", "").startswith("/"), (ident, attrs))
                    if tag == "form":
                        self.assertIn(attrs.get("method"), {"get", "post"})
                        self.assertTrue(attrs.get("action", "").startswith("/"))
                self.assertFalse(any(tag == "iframe" for tag, _ in parsed.attrs))

    def test_primitives_are_optional_responsive_and_keyboard_accessible(self):
        css = (ROOT / "src/recipes.css").read_text()
        core = (ROOT / "src/components/layout.css").read_text()
        for selector in ("syn-scroll-rail", "syn-bento-grid", "syn-bento-card--wide"):
            self.assertIn(selector, css)
            self.assertNotIn(selector, core)
        self.assertIn("scroll-snap-type: inline proximity", css)
        self.assertIn("scroll-snap-align: start", css)
        self.assertIn("syn-scroll-rail:focus-visible", css)
        self.assertIn("overscroll-behavior-inline", css)
        self.assertIn("@container", css)
        rail = (ROOT / "blocks/snippets/scrollable-card-rail.html").read_text()
        self.assertIn('class="syn-scroll-rail"', rail)
        self.assertIn('tabindex="0"', rail)
        self.assertIn('role="region"', rail)
        self.assertIn('aria-label=', rail)
        bento = (ROOT / "blocks/snippets/bento-feature-grid.html").read_text()
        self.assertIn("syn-bento-card--wide", bento)

    def test_copyable_gallery_and_registry_include_each_new_block(self):
        gallery = (ROOT / "docs/blocks.html").read_text()
        registry = json.loads((ROOT / "registry/registry.json").read_text())
        for ident in MARKETING | APPLICATIONS:
            with self.subTest(block=ident):
                self.assertEqual(gallery.count(f'data-block-id="{ident}"'), 1)
                self.assertIn(f"block-title-{ident}", gallery)
                self.assertIn(ident, json.dumps(registry))

    def test_workflows_present_real_forms_tables_and_native_usage(self):
        for ident in ("auth-sign-up", "resource-crud", "organization-members", "integration-connection"):
            with self.subTest(block=ident):
                html = (ROOT / "blocks/snippets" / f"{ident}.html").read_text()
                self.assertIn("<form ", html)
                self.assertIn('method="post"', html)
        for ident in ("resource-crud", "organization-members", "billing-usage"):
            html = (ROOT / "blocks/snippets" / f"{ident}.html").read_text()
            self.assertIn("<table", html)
            self.assertIn("syn-table-wrap", html)
            self.assertIn('tabindex="0"', html)
        usage = (ROOT / "blocks/snippets/billing-usage.html").read_text()
        self.assertIn("<meter ", usage)
        self.assertIn("value=", usage)
        self.assertIn("max=", usage)

    def test_contextual_panels_do_not_create_nested_complementary_landmarks(self):
        for ident in (
            "auth-sign-up", "resource-crud", "organization-members",
            "developer-api-settings",
        ):
            with self.subTest(block=ident):
                source = (ROOT / "blocks/snippets" / f"{ident}.html").read_text()
                self.assertNotIn('<aside class="syn-detail-aside', source)
                self.assertIn('<section class="syn-detail-aside syn-panel"', source)

    def test_dense_tables_have_scrollable_readable_minimum_width(self):
        css = (ROOT / "src/recipes.css").read_text()
        self.assertIn("&.syn-table--readable", css)
        self.assertIn("min-inline-size: var(--syn-table-readable-min", css)
        for ident in (
            "hero-product-preview", "pricing-comparison", "resource-crud",
            "organization-members", "billing-usage", "developer-api-settings",
        ):
            with self.subTest(block=ident):
                markup = (ROOT / "blocks/snippets" / f"{ident}.html").read_text()
                self.assertIn('class="syn-table syn-table--readable"', markup)
                self.assertIn('class="syn-table-wrap"', markup)
                self.assertIn('tabindex="0"', markup)

    def test_spotlight_section_heading_precedes_illustration_heading(self):
        source = (ROOT / "blocks/snippets/feature-spotlight-detail.html").read_text()
        self.assertLess(
            source.index('id="syn-feature-spotlight-title"'),
            source.index("<h3>Project detail</h3>"),
            "The section h2 must precede the illustrative h3 in reading order",
        )

    def test_signup_password_help_has_programmatic_association(self):
        source = (ROOT / "blocks/snippets/auth-sign-up.html").read_text()
        parsed = Elements()
        parsed.feed(source)
        field = next(
            attrs for tag, attrs in parsed.attrs
            if tag == "input" and attrs.get("id") == "syn-signup-password"
        )
        description = field.get("aria-describedby")
        self.assertEqual(description, "syn-signup-password-help")
        self.assertIn(description, parsed.ids)
        self.assertIn("Use at least 12 characters.", source)

if __name__ == "__main__":
    unittest.main()
