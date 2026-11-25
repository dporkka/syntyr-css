"""Catalog filters and portable agent discovery stay synchronized to HTML."""
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from scripts.build_component_gallery import OPEN_CARD, build_manifest

ROOT = Path(__file__).resolve().parents[1]
USE_CASES = {"marketing-site", "saas-dashboard", "forms-workflow", "content-docs", "navigation"}


class CatalogUseCaseDiscoveryTests(unittest.TestCase):
    def test_all_examples_have_bounded_curated_use_cases(self):
        page = (ROOT / "docs/catalog.html").read_text(encoding="utf-8")
        cards = list(OPEN_CARD.finditer(page))
        self.assertEqual(len(cards), 49)
        for match in cards:
            tags = re.search(r'data-catalog-use-cases="([^"]+)"', match.group("attrs"))
            self.assertIsNotNone(tags)
            values = tags.group(1).split()
            self.assertGreaterEqual(len(values), 1)
            self.assertEqual(len(values), len(set(values)))
            self.assertTrue(set(values) <= USE_CASES)

    def test_agent_manifest_exposes_discovery_fields_for_all_examples(self):
        manifest = build_manifest()
        self.assertEqual(set(manifest["use_case_definitions"]), USE_CASES)
        self.assertIn("docs/framework-integrations.html", manifest["adoption_guidance"]["framework_guide"])
        self.assertIn("syntyr.core.css", manifest["adoption_guidance"]["required_css_order"][0])
        page = (ROOT / "docs/catalog.html").read_text(encoding="utf-8")
        card_tags = {
            re.search(r'aria-labelledby="([^"]+)"', match.group("attrs"))[1]:
                re.search(r'data-catalog-use-cases="([^"]+)"', match.group("attrs"))[1].split()
            for match in OPEN_CARD.finditer(page)
        }
        for item in manifest["examples"]:
            with self.subTest(item=item["id"]):
                self.assertEqual(item["use_cases"], card_tags[item["id"]])
                self.assertTrue(set(item["use_cases"]) <= USE_CASES)
                self.assertTrue(item["use_cases"])
                self.assertEqual(item["catalog_url"], "docs/catalog.html#" + item["id"])
                self.assertEqual(item["playground_url"], "docs/playground.html#component=" + item["id"])
                self.assertEqual(item["required_stylesheets"][0], "syntyr.core.css")
        by_id = {item["id"]: item for item in manifest["examples"]}
        self.assertIn("saas-dashboard", by_id["catalog-crm-filters-title"]["use_cases"])
        self.assertIn("marketing-site", by_id["catalog-pricing-title"]["use_cases"])
        self.assertIn("forms-workflow", by_id["catalog-forms-title"]["use_cases"])
        self.assertIn("content-docs", by_id["catalog-code-and-keyboard-input-title"]["use_cases"])

    def test_unknown_or_duplicate_tags_are_rejected_before_publishing(self):
        original_read = Path.read_text
        for invalid in ("saas-dashboard saas-dashboard", "unknown-task"):
            with self.subTest(invalid=invalid):
                def bad_catalog(path, *args, **kwargs):
                    value = original_read(path, *args, **kwargs)
                    if path == ROOT / "docs/catalog.html":
                        return value.replace(
                            'data-catalog-use-cases="forms-workflow saas-dashboard"',
                            f'data-catalog-use-cases="{invalid}"', 1,
                        )
                    return value
                with patch.object(Path, "read_text", new=bad_catalog):
                    with self.assertRaisesRegex(ValueError, "Invalid curated use cases"):
                        build_manifest()

    def test_modules_are_reported_from_actual_badges(self):
        manifest = build_manifest()
        examples = manifest["examples"]
        for suffix in ("recipes", "geometry", "viz", "semantic"):
            module = f"syntyr.{suffix}.css"
            self.assertTrue(any(module in item["required_stylesheets"] for item in examples))
        self.assertEqual(sum(item["required_stylesheets"] == ["syntyr.core.css"] for item in examples), 44)

    def test_gallery_filters_are_progressive_and_composable(self):
        page = (ROOT / "docs/catalog.html").read_text(encoding="utf-8")
        script = (ROOT / "docs/catalog.js").read_text(encoding="utf-8")
        for element in ("catalog-module-filter", "catalog-use-case-filter", "catalog-browser-filter"):
            self.assertIn(f'id="{element}"', page)
            self.assertIn(element, script)
        for value in ("core-only", "syntyr.recipes.css", "syntyr.geometry.css",
                      "syntyr.viz.css", "syntyr.semantic.css"):
            self.assertIn(f'value="{value}"', page)
        for value in USE_CASES:
            self.assertIn(f'value="{value}"', page)
        self.assertIn("card.hidden = !match", script)
        self.assertIn('id="catalog-controls" class="catalog-controls" hidden', page)
        self.assertIn("load the required CSS", page)

    def test_agent_and_editor_guides_cover_metadata_contract(self):
        agent = (ROOT / "llms.txt").read_text(encoding="utf-8")
        editor = (ROOT / "docs/editor-integration.md").read_text(encoding="utf-8")
        for value in ("use_cases", "required_stylesheets", "native_feature_requirements"):
            self.assertIn(value, editor)
        self.assertIn("component-gallery.v1.json", agent)
        self.assertIn("use cases", agent.lower())


if __name__ == "__main__":
    unittest.main()
