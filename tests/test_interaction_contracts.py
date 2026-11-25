"""Machine-readable interaction guidance must match candidate CSS and stay read-only."""
import json
from pathlib import Path
import re
import unittest

from agent_mcp.catalog import CANDIDATE, PUBLISHED, CatalogError, SyntyrCatalog

ROOT = Path(__file__).resolve().parents[1]


class InteractionContractTests(unittest.TestCase):
    def setUp(self):
        self.catalog = SyntyrCatalog()

    def test_discovery_is_version_pinned_and_deterministic(self):
        result = self.catalog.get_interaction_contracts(release=CANDIDATE)
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["release_status"], "unreleased_candidate")
        self.assertEqual([c["id"] for c in result["contracts"]],
                         ["combobox", "dialog", "disclosure", "dropdown", "sortable-table"])
        self.assertEqual(result, self.catalog.get_interaction_contracts(release=CANDIDATE))

    def test_lookup_and_unknown_contract(self):
        result = self.catalog.get_interaction_contracts("combobox", CANDIDATE)
        contract, = result["contracts"]
        self.assertEqual(contract["behavior_owner"], "host")
        self.assertIn("headless/interactions.css", contract["stylesheets"])
        with self.assertRaisesRegex(CatalogError, "Unknown"):
            self.catalog.get_interaction_contracts("not-a-widget", CANDIDATE)

    def test_unpublished_contracts_fail_closed(self):
        for version in (PUBLISHED, "latest"):
            with self.assertRaises(CatalogError):
                self.catalog.get_interaction_contracts(release=version)

    def test_manifest_references_real_css_and_documentation(self):
        data = self.catalog.get_interaction_contracts(release=CANDIDATE)
        for contract in data["contracts"]:
            with self.subTest(contract=contract["id"]):
                css = "\n".join((ROOT / ("integrations/" if p.startswith("headless/") else "dist/") / p).read_text() for p in contract["stylesheets"])
                for part in contract["parts"]:
                    for cls in part["classes"]:
                        self.assertRegex(css, r"\." + re.escape(cls) + r"(?![\w-])")
                self.assertTrue((ROOT / contract["reference"]).is_file())
                self.assertTrue(contract["accessibility"])
                self.assertTrue(contract["fallback"])
                self.assertTrue(contract["intentions"])
                self.assertNotIn("actions", contract)
                self.assertEqual(len({p["id"] for p in contract["parts"]}), len(contract["parts"]))

    def test_contract_stylesheets_round_trip_through_validator(self):
        for contract in self.catalog.get_interaction_contracts(release=CANDIDATE)["contracts"]:
            with self.subTest(contract=contract["id"]):
                html = "".join('<div class="' + " ".join(part["classes"]) + '"></div>'
                               for part in contract["parts"] if part["classes"])
                result = self.catalog.validate_markup(html, CANDIDATE, contract["stylesheets"])
                self.assertEqual(result["unknown_classes"], [])
                self.assertEqual(result["missing_stylesheets"], [])

    def test_headless_adapter_is_candidate_only_and_required(self):
        html = '<div class="syn-combobox"></div>'
        result = self.catalog.validate_markup(html, CANDIDATE, ["syntyr.core.css"])
        self.assertEqual(result["unknown_classes"], [])
        self.assertIn("headless/interactions.css", result["missing_stylesheets"])
        with self.assertRaises(CatalogError):
            self.catalog.validate_markup(html, PUBLISHED, ["headless/interactions.css"])
        self.assertIn("syn-combobox", self.catalog.validate_markup(html, PUBLISHED)["unknown_classes"])

    def test_metadata_tracks_candidate_version(self):
        manifest = json.loads((ROOT / "metadata/interaction-contracts.v1.json").read_text())
        self.assertEqual(manifest["source_version"], (ROOT / "VERSION").read_text().strip())
        self.assertEqual(manifest["schema_version"], 1)
