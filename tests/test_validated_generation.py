"""End-to-end offline generation uses the real planner, preflight and renderer."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

from agent_mcp.catalog import CANDIDATE, CatalogError
from scripts.generate_ui import generate

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "Optional Node authoring tool")
class ValidatedGenerationTests(unittest.TestCase):
    def request(self, **changes):
        return {"release": CANDIDATE, "title": "CRM", "theme": "noir",
                "requirements": ["pipeline", "metrics", "inventory-search", "account-management"],
                **changes}

    def test_crm_pipeline_is_deterministic_and_validated(self):
        result = generate(self.request())
        self.assertEqual(result["status"], "generated")
        self.assertTrue(result["preflight"]["valid"])
        self.assertEqual(result["validation"]["diagnostics"], [])
        self.assertEqual(result["output"]["stylesheets"], ["syntyr.all.css"])
        self.assertEqual(len(result["output"]["project"]["blocks"]), 4)
        self.assertTrue(all(i["host_requirements"] for i in result["plan"]["coverage"]))
        self.assertEqual(result, generate(self.request()))

    def test_unresolved_intents_block_without_partial_html(self):
        result = generate(self.request(requirements=["pipeline", "live-map"]))
        self.assertEqual(result["stage"], "planning")
        self.assertEqual(result["plan"]["unresolved"], ["live-map"])
        self.assertNotIn("output", result)

    def test_incompatible_interaction_is_rejected_at_preflight(self):
        result = generate(self.request(interactions=[{"contract": "combobox",
            "recipe": "react-aria-combobox", "relationship": "implementation"}]))
        self.assertEqual(result["stage"], "preflight")
        self.assertIn("host-recipe-not-allowed", {d["code"] for d in result["preflight"]["diagnostics"]})
        self.assertNotIn("output", result)

    def test_valid_but_unimplemented_interaction_never_gets_claimed_as_generated(self):
        result = generate(self.request(interactions=[{"contract": "dialog",
            "recipe": "native-modal-dialog", "relationship": "implementation"}]))
        self.assertTrue(result["preflight"]["valid"])
        self.assertEqual(result["stage"], "interaction-rendering")
        self.assertNotIn("output", result)

    def test_large_composition_never_skips_markup_validation(self):
        listing = subprocess.check_output(["node", "scripts/compose.mjs", "--list-intents", CANDIDATE],
                                          cwd=ROOT, text=True)
        ids = [entry["id"] for entry in json.loads(listing)["intents"]]
        result = generate(self.request(requirements=ids))
        self.assertEqual(result["stage"], "markup-validation")
        self.assertNotIn("output", result)

    def test_invalid_inputs_fail_closed(self):
        for request in (self.request(release="0.3.0-alpha.4"),
                        self.request(html="<script>"), self.request(theme="unknown")):
            with self.assertRaises(CatalogError):
                generate(request)

    def test_cli_status_codes_and_json_output(self):
        def run(request):
            return subprocess.run([sys.executable, "scripts/generate_ui.py"],
                                  input=json.dumps(request), text=True, capture_output=True,
                                  cwd=ROOT, timeout=30)
        ok = run(self.request(requirements=["faq"]))
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertEqual(json.loads(ok.stdout)["status"], "generated")
        blocked = run(self.request(requirements=["live-map"]))
        self.assertEqual(blocked.returncode, 2, blocked.stderr)
        self.assertNotIn("output", json.loads(blocked.stdout))
        bad = run(self.request(html="unsafe"))
        self.assertEqual(bad.returncode, 1)
        self.assertEqual(bad.stdout, "")
