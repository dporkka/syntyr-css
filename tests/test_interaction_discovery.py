"""Candidate-only discovery joins existing contracts and runnable recipe references."""
import unittest

from agent_mcp.catalog import CANDIDATE, PUBLISHED, CatalogError, SyntyrCatalog


class InteractionDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.catalog = SyntyrCatalog()

    def test_all_recipes_are_discoverable_and_deterministic(self):
        result = self.catalog.get_interaction_recipes(release=CANDIDATE)
        self.assertEqual(result["release_status"], "unreleased_candidate")
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(len(result["recipes"]), 8)
        self.assertEqual(result, self.catalog.get_interaction_recipes(release=CANDIDATE))
        self.assertNotIn("actions", result)
        self.assertTrue(all("contract_links" in r for r in result["recipes"]))
        self.assertEqual(next(r for r in result["recipes"] if r["id"] == "radix-toast")["contract_links"], [])

    def test_combobox_distinguishes_native_fallback_from_real_widget(self):
        result = self.catalog.get_interaction_recipes("combobox", CANDIDATE)
        recipes = {r["id"]: r for r in result["recipes"]}
        self.assertEqual(set(recipes), {"native-select", "react-aria-combobox"})
        self.assertIn({"id": "combobox", "relationship": "fallback"}, recipes["native-select"]["contract_links"])
        self.assertIn({"id": "combobox", "relationship": "implementation"}, recipes["react-aria-combobox"]["contract_links"])
        self.assertIn("headless/interactions.css", recipes["react-aria-combobox"]["stylesheets"])

    def test_every_contract_has_a_real_recipe_reference(self):
        for contract in self.catalog.get_interaction_contracts(release=CANDIDATE)["contracts"]:
            with self.subTest(contract=contract["id"]):
                result = self.catalog.get_interaction_recipes(contract["id"], CANDIDATE)
                self.assertTrue(result["recipes"])
                self.assertTrue(all(r["test_file"] and r["source"] for r in result["recipes"]))
                for recipe in result["recipes"]:
                    checked = self.catalog.validate_markup("", CANDIDATE, recipe["stylesheets"])
                    self.assertEqual(checked["missing_stylesheets"], [])

    def test_unknown_contract_and_published_release_fail_closed(self):
        for name, version in (("invented", CANDIDATE), ("", PUBLISHED), ("", "latest")):
            with self.assertRaises(CatalogError):
                self.catalog.get_interaction_recipes(name, version)

    def test_native_table_is_not_claimed_as_live_sorting(self):
        result = self.catalog.get_interaction_recipes("sortable-table", CANDIDATE)
        recipe = next(r for r in result["recipes"] if r["id"] == "native-table")
        self.assertIn({"id": "sortable-table", "relationship": "fallback"}, recipe["contract_links"])
