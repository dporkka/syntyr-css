"""Regression tests for release-to-release public CSS contract comparison."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from contract_diff import compare_contracts  # noqa: E402


def contract():
    return {
        "schema_version": 1,
        "source_version": "0.3.0-alpha.4",
        "stylesheets": ["syntyr.core.css", "syntyr.recipes.css"],
        "classes": [{"name": "syn-button", "module": "buttons.css", "stylesheets": ["syntyr.core.css"]}],
        "tokens": [{"name": "--syn-accent", "module": "tokens.css", "stylesheets": ["syntyr.core.css"]}],
        "themes": ["studio", "noir"],
        "attributes": {"data-syn-theme": ["studio", "noir"], "data-syn-density": ["compact"]},
    }


class ContractDiffTests(unittest.TestCase):
    def test_unchanged_contract_is_not_breaking(self):
        result = compare_contracts(contract(), contract())
        self.assertFalse(result["breaking"])
        self.assertEqual(result["changes"]["classes"], {"added": [], "removed": []})
        self.assertEqual(result["changes"]["class_stylesheet_removals"], [])

    def test_added_class_token_theme_attribute_value_are_additive(self):
        before, after = contract(), contract()
        after["source_version"] = "0.3.0-alpha.5"
        after["classes"].append({"name": "syn-card", "module": "cards.css", "stylesheets": ["syntyr.core.css"]})
        after["tokens"].append({"name": "--syn-space", "module": "tokens.css", "stylesheets": ["syntyr.core.css"]})
        after["themes"].append("grid")
        after["attributes"]["data-syn-theme"].append("grid")
        after["attributes"]["data-syn-intensity"] = ["quiet"]
        diff = compare_contracts(before, after)
        self.assertFalse(diff["breaking"])
        self.assertEqual(diff["changes"]["classes"]["added"], ["syn-card"])
        self.assertEqual(diff["changes"]["tokens"]["added"], ["--syn-space"])
        self.assertEqual(diff["changes"]["attributes"]["data-syn-theme"]["added"], ["grid"])
        self.assertEqual(diff["changes"]["attributes"]["data-syn-intensity"]["added"], ["quiet"])

    def test_removed_names_and_values_are_flagged(self):
        before, after = contract(), contract()
        after["classes"] = []
        after["tokens"] = []
        after["themes"].remove("noir")
        after["attributes"]["data-syn-theme"].remove("noir")
        after["attributes"].pop("data-syn-density")
        diff = compare_contracts(before, after)
        self.assertTrue(diff["breaking"])
        self.assertEqual(diff["changes"]["classes"]["removed"], ["syn-button"])
        self.assertEqual(diff["changes"]["tokens"]["removed"], ["--syn-accent"])
        self.assertEqual(diff["changes"]["attributes"]["data-syn-density"]["removed"], ["compact"])

    def test_removing_a_class_from_one_distribution_is_breaking_even_if_name_survives(self):
        before, after = contract(), contract()
        before["classes"][0]["stylesheets"].append("syntyr.recipes.css")
        after["classes"][0]["stylesheets"] = ["syntyr.core.css"]
        result = compare_contracts(before, after)
        self.assertTrue(result["breaking"])
        self.assertEqual(result["changes"]["class_stylesheet_removals"], [
            {"name": "syn-button", "stylesheets": ["syntyr.recipes.css"]}
        ])

    def test_reordering_entries_and_description_changes_are_nonbreaking(self):
        before, after = contract(), contract()
        after["classes"][0]["description"] = "Updated wording"
        after["attributes"] = dict(reversed(list(after["attributes"].items())))
        self.assertFalse(compare_contracts(before, after)["breaking"])

    def test_rejects_malformed_or_duplicate_contracts_without_inventing_results(self):
        bad = contract()
        bad["classes"].append(copy.deepcopy(bad["classes"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            compare_contracts(bad, contract())
        bad = contract()
        bad["schema_version"] = 2
        with self.assertRaisesRegex(ValueError, "schema_version"):
            compare_contracts(bad, contract())
        bad = contract()
        del bad["tokens"]
        with self.assertRaisesRegex(ValueError, "tokens"):
            compare_contracts(bad, contract())

    def test_cli_emits_json_and_exits_1_only_for_breaking_in_gate_mode(self):
        with tempfile.TemporaryDirectory() as folder:
            old_path, new_path = Path(folder) / "old.json", Path(folder) / "new.json"
            old, new = contract(), contract()
            new["classes"] = []
            old_path.write_text(json.dumps(old))
            new_path.write_text(json.dumps(new))
            args = [sys.executable, str(ROOT / "scripts" / "contract_diff.py"), str(old_path), str(new_path), "--json"]
            result = subprocess.run(args + ["--fail-on-breaking"], text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertTrue(json.loads(result.stdout)["breaking"])
            self.assertEqual(subprocess.run(args, text=True, capture_output=True).returncode, 0)
            new_path.write_text("{invalid")
            self.assertEqual(subprocess.run(args, text=True, capture_output=True).returncode, 2)

    def test_cli_rejects_duplicate_json_object_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            old_path, new_path = Path(folder) / "old.json", Path(folder) / "new.json"
            original = json.dumps(contract())
            new_path.write_text(original)
            cases = [
                original.replace('"schema_version": 1', '"schema_version": 2, "schema_version": 1', 1),
                original.replace('"data-syn-theme":', '"data-syn-theme": ["injected"], "data-syn-theme":', 1),
                original.replace('"name": "syn-button"', '"name": "bad", "name": "syn-button"', 1),
            ]
            for bad_json in cases:
                old_path.write_text(bad_json)
                result = subprocess.run(
                    [sys.executable, str(ROOT / "scripts" / "contract_diff.py"),
                     str(old_path), str(new_path), "--json"],
                    text=True, capture_output=True,
                )
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn("duplicate", result.stderr.lower())

    def test_live_manifest_is_well_formed_and_comparable(self):
        live = json.loads((ROOT / "metadata" / "syntyr-contract.json").read_text())
        diff = compare_contracts(live, live)
        self.assertFalse(diff["breaking"])
        self.assertEqual(diff["source_versions"]["old"], live["source_version"])


if __name__ == "__main__":
    unittest.main()
