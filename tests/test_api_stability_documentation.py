"""The public prerelease stability contract must travel with the distributions."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ApiStabilityDocumentation(unittest.TestCase):
    def test_api_contract_is_linked_from_readme_and_architecture(self):
        self.assertTrue((ROOT / 'docs/api-stability.md').is_file())
        self.assertIn('docs/api-stability.md', (ROOT / 'README.md').read_text())
        self.assertIn('docs/api-stability.md', (ROOT / 'ARCHITECTURE.md').read_text())

    def test_proposed_minimum_v1_surface_retains_core_exports(self):
        from scripts.contract_diff import compare_contracts
        baseline = json.loads((ROOT / "tests/fixtures/proposed-v1-contract.json").read_text())
        current = json.loads((ROOT / "metadata/syntyr-contract.json").read_text())
        report = compare_contracts(baseline, current)
        self.assertFalse(report["breaking"], json.dumps(report["changes"], indent=2))
        # No named theme is frozen by this proposal, but the attribute itself
        # must remain discoverable even if its allowed value list is empty.
        for name in baseline["attributes"]:
            self.assertIn(name, current["attributes"])

    def test_proposal_inventory_matches_documented_shortlist(self):
        baseline = json.loads((ROOT / "tests/fixtures/proposed-v1-contract.json").read_text())
        doc = (ROOT / "docs/api-stability.md").read_text()
        table = doc.split("## Proposed minimum v1 contract (not yet approved)", 1)[1]
        table = table.split("The list is deliberately small", 1)[0]
        import re
        first_column = "\n".join(row.split("|")[1] for row in table.splitlines()
                                  if row.startswith("|"))
        names = set(re.findall(r"`([^`]+)`", first_column))
        self.assertEqual({x["name"] for x in baseline["classes"]},
                         {x[1:] for x in names if x.startswith(".syn-")})
        self.assertEqual({x["name"] for x in baseline["tokens"]},
                         {x for x in names if x.startswith("--syn-")})
        self.assertEqual(set(baseline["attributes"]),
                         {x for x in names if x.startswith("data-syn-")})
        self.assertEqual(set(baseline["stylesheets"]),
                         {x for x in names if x.endswith(".css")})
        self.assertEqual(baseline["themes"], [])
        self.assertTrue(all(not v for v in baseline["attributes"].values()))
        for field in ("classes", "tokens"):
            self.assertTrue(all(x["stylesheets"] == ["syntyr.core.css"]
                                for x in baseline[field]))

    def test_api_contract_is_published_and_packaged(self):
        from scripts.package_release import FILES
        from scripts.build_cloudflare_site import source_files
        self.assertIn('docs/api-stability.md', FILES)
        self.assertIn('docs/api-stability.md', source_files())


if __name__ == '__main__':
    unittest.main()
