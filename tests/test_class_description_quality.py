"""Generated editor metadata should explain classes, not just source paths."""
import unittest

from scripts.export_api_metadata import collect, describe_class


class ClassDescriptionQualityTests(unittest.TestCase):
    def test_public_classes_have_useful_non_placeholder_descriptions(self):
        entries = collect()["classes"]
        self.assertGreater(len(entries), 300)
        for entry in entries:
            with self.subTest(name=entry["name"]):
                description = entry["description"]
                self.assertGreater(len(description), 25)
                self.assertNotIn("Syntyr CSS class (", description)
                self.assertNotIn("Syntyr class.", description)

    def test_check_class_metadata_matches_checkbox_label_layout(self):
        from scripts.export_api_metadata import collect
        classes = {item["name"]: item["description"] for item in collect()["classes"]}
        self.assertIn("label", classes["syn-check"].lower())
        self.assertNotIn("checkmark", classes["syn-check"].lower())

    def test_design_tokens_have_intelligible_metadata(self):
        tokens = {item["name"]: item["description"] for item in collect()["tokens"]}
        self.assertGreater(len(tokens), 100)
        for name, description in tokens.items():
            with self.subTest(name=name):
                self.assertGreater(len(description), 20)
                self.assertNotIn("Syntyr CSS property (", description)
        for token, keyword in (
            ("--syn-space-2", "spacing"),
            ("--syn-surface", "surface"),
            ("--syn-focus-ring", "focus"),
            ("--syn-duration-fast", "motion"),
        ):
            self.assertIn(keyword, tokens[token].lower())

    def test_semantic_overrides_for_common_components(self):
        expected = {
            "syn-input": "form",
            "syn-button--danger": "danger",
            "syn-data-grid__cell": "cell",
            "syn-nav-tabs": "navigation",
            "syn-skeleton": "loading",
            "syn-dialog": "dialog",
        }
        classes = {item["name"]: item for item in collect()["classes"]}
        for name, keyword in expected.items():
            with self.subTest(name=name):
                self.assertIn(keyword, classes[name]["description"].lower())

    def test_derivative_descriptions_distinguish_variants_parts_and_utilities(self):
        self.assertIn("variant", describe_class("syn-example--quiet", "recipes.css"))
        self.assertIn("part", describe_class("syn-example__label", "recipes.css"))
        self.assertIn("utility", describe_class("syn-u-nowrap", "utilities.css"))
        self.assertIn("Example", describe_class("syn-example", "recipes.css"))


if __name__ == "__main__":
    unittest.main()
