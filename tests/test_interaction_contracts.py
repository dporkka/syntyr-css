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
        self.assertIn("integrations/headless/interactions.css", contract["stylesheets"])
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
                css = "\n".join((ROOT / p).read_text() for p in contract["stylesheets"])
                for part in contract["parts"]:
                    for cls in part["classes"]:
                        self.assertRegex(css, r"\." + re.escape(cls) + r"(?![\w-])")
                self.assertTrue((ROOT / contract["reference"]).is_file())
                self.assertTrue(contract["accessibility"])
                self.assertTrue(contract["fallback"])
                self.assertTrue(contract["intentions"])
                self.assertNotIn("actions", contract)
                self.assertEqual(len({p["id"] for p in contract["parts"]}), len(contract["parts"]))

    def test_metadata_tracks_candidate_version(self):
        manifest = json.loads((ROOT / "metadata/interaction-contracts.v1.json").read_text())
        self.assertEqual(manifest["source_version"], (ROOT / "VERSION").read_text().strip())
        self.assertEqual(manifest["schema_version"], 1)
