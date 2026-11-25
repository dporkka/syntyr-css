"""Preflight a declared assembly against real candidate section and interaction inventories."""
import unittest
import json
from pathlib import Path
from agent_mcp.catalog import CANDIDATE, PUBLISHED, CatalogError, SyntyrCatalog


class CompositionPreflightTests(unittest.TestCase):
    def setUp(self):
        self.catalog = SyntyrCatalog()

    def check(self, sections=None, interactions=None, styles=None, policy="scriptless"):
        return self.catalog.validate_composition(
            sections if sections is not None else ["hero-product"],
            interactions if interactions is not None else [],
            styles if styles is not None else ["syntyr.core.css", "syntyr.recipes.css"],
            policy, CANDIDATE)

    def test_real_sections_produce_deterministic_stylesheet_requirements(self):
        result = self.check()
        self.assertTrue(result["valid"])
        self.assertEqual(result["required_stylesheets"], ["syntyr.core.css", "syntyr.recipes.css"])
        self.assertEqual(result, self.check())
        self.assertNotIn("html", result)

    def test_unknown_section_and_missing_required_module(self):
        result = self.check(["hero-product", "invented"], styles=["syntyr.core.css"])
        self.assertFalse(result["valid"])
        self.assertEqual({d["code"] for d in result["diagnostics"]},
                         {"unknown-section", "missing-stylesheet"})

    def test_native_dialog_plan_with_declared_recipe(self):
        result = self.check(interactions=[{"contract": "dialog", "recipe": "native-modal-dialog",
                                         "relationship": "implementation", "intentions": ["open"],
                                         "state_hooks": ["open"]}],
                            styles=["syntyr.core.css", "syntyr.recipes.css", "syntyr.css", "syntyr.motion.css"])
        self.assertTrue(result["valid"], result["diagnostics"])

    def test_host_recipe_requires_opt_in_and_adapter_css(self):
        request = {"contract": "combobox", "recipe": "react-aria-combobox",
                   "relationship": "implementation", "intentions": ["select"],
                   "state_hooks": ["aria-expanded"]}
        result = self.check(interactions=[request])
        self.assertFalse(result["valid"])
        self.assertEqual({d["code"] for d in result["diagnostics"]},
                         {"host-recipe-not-allowed", "missing-stylesheet"})
        self.assertTrue(self.check(interactions=[request], policy="host-enabled",
                                  styles=["syntyr.core.css", "syntyr.recipes.css",
                                          "headless/interactions.css"])["valid"])

    def test_fallback_is_not_a_live_implementation(self):
        request = {"contract": "combobox", "recipe": "native-select",
                   "relationship": "implementation", "intentions": ["filter"]}
        result = self.check(interactions=[request], styles=["syntyr.core.css",
                            "syntyr.recipes.css", "syntyr.semantic-bundle.css"])
        self.assertIn("recipe-relationship-mismatch", {d["code"] for d in result["diagnostics"]})
        request["relationship"] = "fallback"
        result = self.check(interactions=[request], styles=["syntyr.core.css",
                            "syntyr.recipes.css", "syntyr.semantic-bundle.css"])
        self.assertIn("unverified-interaction-claims", {d["code"] for d in result["diagnostics"]})
        request["intentions"] = []
        self.assertTrue(self.check(interactions=[request], styles=["syntyr.core.css",
                        "syntyr.recipes.css", "syntyr.semantic-bundle.css"])["valid"])

    def test_unknown_intention_and_state_hook_fail(self):
        result = self.check(interactions=[{"contract": "dialog", "recipe": "native-modal-dialog",
                            "relationship": "implementation", "intentions": ["delete"],
                            "state_hooks": ["aria-sort"]}],
                            styles=["syntyr.core.css", "syntyr.recipes.css", "syntyr.css", "syntyr.motion.css"])
        self.assertEqual({d["code"] for d in result["diagnostics"]},
                         {"unknown-intention", "unknown-state-hook"})

    def test_all_current_sections_are_recognized(self):
        manifest = json.loads((Path(__file__).resolve().parents[1] /
                               "metadata/section-composer.v1.json").read_text())
        sections = manifest["sections"]
        styles = sorted({css for item in sections for css in item["required_stylesheets"]})
        result = self.check([item["id"] for item in sections], styles=styles)
        self.assertTrue(result["valid"], result["diagnostics"])

    def test_unknown_contract_and_recipe_are_diagnosed_without_execution(self):
        result = self.check(interactions=[{"contract": "invented", "recipe": "untrusted",
                                          "relationship": "implementation"}])
        self.assertEqual({d["code"] for d in result["diagnostics"]},
                         {"unknown-contract", "unknown-recipe"})

    def test_invalid_input_and_unpublished_release_fail_closed(self):
        with self.assertRaises(CatalogError):
            self.catalog.validate_composition([], [], [], "scriptless", PUBLISHED)
        with self.assertRaises(CatalogError):
            self.check(sections="hero-product")
        with self.assertRaises(CatalogError):
            self.check(interactions=[{"contract": "dialog", "recipe": "native-modal-dialog",
                                     "relationship": "implementation", "execute": "anything"}])
        with self.assertRaises(CatalogError):
            self.check(styles=["../../secret.css"])
