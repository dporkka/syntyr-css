"""Curated CSS-only recipe contracts are safe for coding-agent composition."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from export_api_metadata import outputs, validate_recipes  # noqa: E402


class RecipeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(outputs()[ROOT / "metadata/syntyr-contract.json"])
        cls.curated = json.loads((ROOT / "metadata/components.json").read_text())

    def test_exported_recipes_have_valid_class_and_stylesheet_coverage(self):
        recipes = self.contract["recipes"]
        self.assertEqual({recipe["id"] for recipe in recipes}, {
            "crm-filter", "resource-table", "app-shell", "validated-form"
        })
        classes = {c["name"]: set(c["stylesheets"]) for c in self.contract["classes"]}
        for recipe in recipes:
            self.assertTrue(recipe["description"])
            self.assertIn("examples/", recipe["example"])
            self.assertTrue((ROOT / recipe["example"]).is_file())
            self.assertTrue(recipe["host_behavior"])
            used = list(recipe["root"]["classes"])
            used += [name for slot in recipe["slots"] for name in slot["classes"]]
            for name in used:
                self.assertIn(name, classes)
                self.assertTrue(classes[name].intersection(recipe["stylesheets"]), name)
            self.assertEqual(len({s["name"] for s in recipe["slots"]}), len(recipe["slots"]))
        self.assertEqual(self.curated["recipes"], recipes)

    def test_rejects_unknown_classes_and_missing_css_module(self):
        original = self.curated["recipes"]
        classes = {c["name"]: set(c["stylesheets"]) for c in self.contract["classes"]}
        broken = copy.deepcopy(original)
        broken[0]["slots"][0]["classes"].append("syn-not-a-class")
        with self.assertRaisesRegex(ValueError, "unknown class"):
            validate_recipes(broken, classes, self.contract["attributes"])
        broken = copy.deepcopy(original)
        broken[0]["stylesheets"] = ["syntyr.core.css"]
        with self.assertRaisesRegex(ValueError, "not loaded"):
            validate_recipes(broken, classes, self.contract["attributes"])

    def test_rejects_incomplete_slot_or_root(self):
        original = self.curated["recipes"]
        classes = {c["name"]: set(c["stylesheets"]) for c in self.contract["classes"]}
        for key in ("name", "optional", "repeatable"):
            broken = copy.deepcopy(original)
            del broken[0]["slots"][0][key]
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "required slot"):
                validate_recipes(broken, classes, self.contract["attributes"])
        broken = copy.deepcopy(original)
        del broken[0]["root"]["tag"]
        with self.assertRaisesRegex(ValueError, "root"):
            validate_recipes(broken, classes, self.contract["attributes"])

    def test_rejects_non_list_stylesheets_with_known_names(self):
        classes = {c["name"]: set(c["stylesheets"]) for c in self.contract["classes"]}
        broken = copy.deepcopy(self.curated["recipes"])
        broken[0]["stylesheets"] = {
            name: False for name in broken[0]["stylesheets"]
        }
        with self.assertRaisesRegex(ValueError, "stylesheets must be a nonempty list"):
            validate_recipes(broken, classes, self.contract["attributes"])

    def test_component_only_recipe_requires_base_and_tokens(self):
        classes = {c["name"]: set(c["stylesheets"]) for c in self.contract["classes"]}
        broken = copy.deepcopy(self.curated["recipes"])
        broken[0].update({
            "stylesheets": ["components/buttons.css"],
            "root": {"tag": "button", "classes": ["syn-button"]},
            "slots": [],
            "variants": {},
        })
        with self.assertRaisesRegex(ValueError, "requires tokens and base"):
            validate_recipes(broken, classes, self.contract["attributes"])
        broken[0]["stylesheets"] += [
            "components/tokens.css", "components/base.css"
        ]
        validate_recipes(broken, classes, self.contract["attributes"])

    def test_agent_docs_index_links_new_recipe_contract(self):
        from build_agent_docs import SOURCES
        self.assertIn("docs/editor-integration.md", SOURCES)
        index = (ROOT / "llms.txt").read_text()
        self.assertIn("https://syntyr-css.pages.dev/docs/editor-integration.md", index)
        full = (ROOT / "llms-full.txt").read_text()
        self.assertIn("## Source: docs/editor-integration.md", full)
        self.assertIn("### Agent-ready composition recipes", full)

    def test_rejects_unknown_distribution_and_duplicate_recipe_id(self):
        original = self.curated["recipes"]
        classes = {c["name"]: set(c["stylesheets"]) for c in self.contract["classes"]}
        broken = copy.deepcopy(original)
        broken[0]["stylesheets"].append("syntyr.missing.css")
        with self.assertRaisesRegex(ValueError, "unknown stylesheet"):
            validate_recipes(broken, classes, self.contract["attributes"])
        broken = copy.deepcopy(original)
        broken[1]["id"] = broken[0]["id"]
        with self.assertRaisesRegex(ValueError, "duplicate recipe id"):
            validate_recipes(broken, classes, self.contract["attributes"])

    def test_rejects_non_array_or_non_string_variant_values(self):
        original = self.curated["recipes"]
        classes = {c["name"]: set(c["stylesheets"]) for c in self.contract["classes"]}
        for bad in ({"compact": True}, [], ["compact", 3], "compact"):
            broken = copy.deepcopy(original)
            broken[0]["variants"]["data-syn-density"] = bad
            with self.subTest(bad=bad), self.assertRaisesRegex(
                ValueError, "nonempty list of strings"
            ):
                validate_recipes(broken, classes, self.contract["attributes"])

    def test_rejects_invalid_variants_and_duplicate_slots(self):
        original = self.curated["recipes"]
        classes = {c["name"]: set(c["stylesheets"]) for c in self.contract["classes"]}
        broken = copy.deepcopy(original)
        broken[0]["variants"]["data-syn-density"] = ["impossible"]
        with self.assertRaisesRegex(ValueError, "unsupported variant"):
            validate_recipes(broken, classes, self.contract["attributes"])
        broken = copy.deepcopy(original)
        broken[0]["slots"].append(copy.deepcopy(broken[0]["slots"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate slot"):
            validate_recipes(broken, classes, self.contract["attributes"])

    def test_checked_in_contract_matches_exporter(self):
        content = outputs()[ROOT / "metadata/syntyr-contract.json"]
        self.assertEqual(content, (ROOT / "metadata/syntyr-contract.json").read_text())


if __name__ == "__main__":
    unittest.main()
