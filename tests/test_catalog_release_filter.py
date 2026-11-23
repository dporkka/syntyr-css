"""Pinned-release catalog discovery is conservative, reproducible, and opt-in."""
from pathlib import Path
import json
import unittest
from scripts.build_catalog_release import build_release_matrix, verify_catalog_annotations, render_release_matrix

ROOT = Path(__file__).resolve().parents[1]


class PublishedReleaseCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = build_release_matrix()
        cls.catalog = (ROOT / "docs/catalog.html").read_text(encoding="utf-8")
        cls.script = (ROOT / "docs/catalog.js").read_text(encoding="utf-8")

    def test_frozen_stylesheet_contract_is_source_of_truth(self):
        self.assertEqual(self.matrix["published_release"], "0.3.0-alpha.4")
        self.assertEqual(len(self.matrix["examples"]), 49)
        self.assertIn("selector coverage", self.matrix["method"].lower())
        self.assertTrue(verify_catalog_annotations(self.matrix))
        path = ROOT / "metadata/catalog-release-compatibility.v1.json"
        self.assertEqual(path.read_text(encoding="utf-8"), render_release_matrix(self.matrix))

    def test_unknown_classes_or_unpublished_modules_are_not_marked_published(self):
        by_id = {x["id"]: x for x in self.matrix["examples"]}
        self.assertTrue(by_id["catalog-buttons-title"]["published_css_covered"])
        self.assertFalse(by_id["catalog-breadcrumbs-title"]["published_css_covered"])
        self.assertIn("syn-breadcrumbs", by_id["catalog-breadcrumbs-title"]["missing_classes"])
        self.assertFalse(by_id["catalog-viz-bars-title"]["published_css_covered"])
        self.assertIn("syntyr.viz.css", by_id["catalog-viz-bars-title"]["missing_stylesheets"])
        for example in self.matrix["examples"]:
            if example["published_css_covered"]:
                self.assertFalse(example["missing_stylesheets"])
                self.assertFalse(example["missing_classes"])

    def test_release_filter_is_clear_and_progressively_enhanced(self):
        self.assertIn('id="catalog-release-filter"', self.catalog)
        self.assertIn('value="published-alpha4"', self.catalog)
        self.assertIn('value="source-alpha5"', self.catalog)
        self.assertIn('id="catalog-release-note"', self.catalog)
        self.assertIn('id="catalog-framework-stylesheet"', self.catalog)
        self.assertEqual(self.catalog.count('data-catalog-alpha4="'), 49)
        self.assertIn("published-alpha4", self.script)
        self.assertIn("site-releases/0.3.0-alpha.4/syntyr.all.css", self.script)
        self.assertIn("/v/0.3.0-alpha.4/syntyr.all.css", self.script)
        self.assertIn("card.dataset.catalogAlpha4", self.script)
        self.assertIn("releaseFilter", self.script)

    def test_static_cloudflare_build_checks_and_publishes_the_matrix(self):
        build = (ROOT / "scripts/build_cloudflare_site.py").read_text(encoding="utf-8")
        self.assertIn("build_release_matrix()", build)
        self.assertIn("verify_catalog_annotations(release_matrix)", build)
        self.assertIn('ROOT / "metadata/catalog-release-compatibility.v1.json"', build)

    def test_copy_full_page_uses_the_selected_release_css(self):
        self.assertIn("/v/0.3.0-alpha.4/", self.script)
        self.assertIn("/dist/", self.script)
        self.assertIn("Copy full page", self.catalog)
        self.assertIn("Self-host", self.script)


if __name__ == "__main__":
    unittest.main()
