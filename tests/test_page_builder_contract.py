"""Run Syntyr's optional visual builder model checks from the standard test suite."""
from pathlib import Path
import shutil
import json
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PageBuilderModelTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node.js is optional for the CSS-only core")
    def test_portable_page_schema_and_export_contract(self):
        result = subprocess.run(
            ["node", "--test", "tests/page_builder_model.test.mjs", "tests/page_builder_gallery.test.mjs",
             "tests/page_builder_sections.test.mjs", "tests/page_builder_zip.test.mjs",
             "tests/site_builder_model.test.mjs", "tests/synced_components.test.mjs",
             "tests/page_builder_site_kits.test.mjs", "tests/compose_cli.test.mjs", "tests/compose_intent.test.mjs"],
            cwd=ROOT, text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("node"), "Node.js is optional for the CSS-only core")
    def test_composed_html_round_trips_through_pinned_css_validator(self):
        from agent_mcp.catalog import CANDIDATE, SyntyrCatalog
        request = {"release": CANDIDATE, "title": "Demo", "theme": "studio",
                   "sections": [{"section_id": "hero-product"}, {"section_id": "faq"}]}
        result = subprocess.run(["node", "scripts/compose.mjs"], input=json.dumps(request),
                                cwd=ROOT, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        checked = SyntyrCatalog().validate_markup(output["html"], CANDIDATE, output["stylesheets"])
        self.assertEqual(checked["unknown_classes"], [])
        self.assertEqual(checked["missing_stylesheets"], [])
        self.assertEqual(checked["diagnostics"], [])

    @unittest.skipUnless(shutil.which("node"), "Node.js is optional for the CSS-only core")
    def test_intent_plan_to_html_round_trips_through_css_validator(self):
        from agent_mcp.catalog import CANDIDATE, SyntyrCatalog
        request = {"release": CANDIDATE, "title": "CRM dashboard", "theme": "studio",
                   "requirements": ["pipeline", "metrics", "inventory-search", "account-management"]}
        plan = subprocess.run(["node", "scripts/compose.mjs", "--plan"], input=json.dumps(request),
                              cwd=ROOT, text=True, capture_output=True, timeout=10)
        self.assertEqual(plan.returncode, 0, plan.stderr)
        result = json.loads(plan.stdout)
        self.assertTrue(result["ready"])
        self.assertTrue(all(entry["host_requirements"] for entry in result["coverage"]))
        rendered = subprocess.run(["node", "scripts/compose.mjs"], input=json.dumps(result["composition"]),
                                  cwd=ROOT, text=True, capture_output=True, timeout=10)
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        output = json.loads(rendered.stdout)
        checked = SyntyrCatalog().validate_markup(output["html"], CANDIDATE, output["stylesheets"])
        self.assertEqual(checked["diagnostics"], [])


if __name__ == "__main__":
    unittest.main()
