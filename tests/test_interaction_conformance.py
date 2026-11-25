"""Trace each interaction contract to real browser scenarios, not a self-certification."""
import json
from pathlib import Path
import unittest

from scripts.check_interaction_conformance import plan

ROOT = Path(__file__).resolve().parents[1]


class InteractionConformanceTests(unittest.TestCase):
    def test_every_contract_maps_to_an_existing_browser_suite(self):
        manifest = json.loads((ROOT / "metadata/interaction-contracts.v1.json").read_text())
        ids = {entry["id"] for entry in manifest["contracts"]}
        groups = plan()
        self.assertEqual({item for group in groups for item in group["contracts"]}, ids)
        for group in groups:
            self.assertTrue((ROOT / group["test_file"]).is_file())
            self.assertTrue((ROOT / group["cwd"]).is_dir())

    def test_native_suite_deduplicates_dialog_and_disclosure(self):
        groups = plan(["dialog", "disclosure"])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["contracts"], ["dialog", "disclosure"])

    def test_headless_suite_covers_both_real_host_owned_widgets(self):
        groups = plan(["sortable-table", "combobox"])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["contracts"], ["combobox", "sortable-table"])

    def test_unknown_id_cannot_be_interpreted_as_a_command(self):
        with self.assertRaisesRegex(ValueError, "Unknown interaction"):
            plan(["../../some-script"])

    def test_empty_selection_is_not_a_pass(self):
        with self.assertRaises(ValueError):
            plan([])
