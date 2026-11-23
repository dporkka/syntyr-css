"""Native browser feature requirements are derived from actual catalog HTML."""
import unittest
from pathlib import Path
from scripts.build_component_gallery import ExampleHTML, build_manifest

ROOT = Path(__file__).resolve().parents[1]


class CatalogNativeFeatureIndexTests(unittest.TestCase):
    def test_feature_classifier_only_flags_real_native_capabilities(self):
        examples = {
            "plain": ("<details><summary>More</summary>Text</details>", []),
            "exclusive": ('<details name="faq"><summary>Question</summary>Answer</details>', ["details-name"]),
            "popover": ('<button popovertarget="help">Open</button><div id="help" popover>Help</div>', ["popover"]),
            "invoker": ('<button commandfor="modal" command="show-modal">Open</button><dialog id="modal"></dialog>', ["invoker-commands"]),
        }
        for label, (html, expected) in examples.items():
            with self.subTest(label=label):
                parser = ExampleHTML()
                parser.feed(html)
                self.assertEqual(sorted(parser.native_features), expected)

    def test_manifest_has_complete_bounded_feature_annotations(self):
        manifest = build_manifest()
        features = manifest["native_browser_features"]
        self.assertEqual(set(features), {"popover", "invoker-commands", "details-name"})
        for code, item in features.items():
            self.assertTrue(item["name"])
            self.assertIn("https://developer.mozilla.org/", item["documentation_url"])
            self.assertTrue(item["fallback"])
        annotated = {item["id"]: item["native_feature_requirements"]
                     for item in manifest["examples"] if item["native_feature_requirements"]}
        self.assertEqual(annotated, {
            "catalog-interaction-card-0": ["details-name"],
            "catalog-interaction-card-2": ["invoker-commands"],
            "catalog-native-popover-title": ["popover"],
        })
        for example in manifest["examples"]:
            parser = ExampleHTML()
            parser.feed(example["html"])
            self.assertEqual(example["native_feature_requirements"], sorted(parser.native_features))
            self.assertTrue(set(example["native_feature_requirements"]) <= set(features))

    def test_catalog_filter_is_optional_and_keeps_unfiltered_source(self):
        html = (ROOT / "docs/catalog.html").read_text()
        js = (ROOT / "docs/catalog.js").read_text()
        self.assertIn('id="catalog-browser-filter"', html)
        self.assertIn('option value="native-advanced"', html)
        self.assertIn('option value="without-advanced"', html)
        self.assertIn("catalog-browser-filter", js)
        self.assertIn("popover", js)
        self.assertIn("commandfor", js)
        self.assertIn("details[name]", js)
        self.assertIn("card.hidden = !match", js)
        self.assertIn('id="catalog-controls" class="catalog-controls" hidden', html)
        self.assertEqual(html.count('<article class="catalog-card syn-panel"'), 49)


if __name__ == "__main__":
    unittest.main()
