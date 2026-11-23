"""Contract and optional Node runtime tests for the read-only Pages HTMX playground."""
from pathlib import Path
import json
import shutil
import subprocess
import unittest

from scripts.build_cloudflare_site import source_files

ROOT = Path(__file__).resolve().parents[1]
ROUTE = "/api/htmx-demo/*"


class HtmxLivePlaygroundTests(unittest.TestCase):
    def test_pages_routes_include_only_the_read_only_demo_api(self):
        files = source_files()
        routes = json.loads(files["_routes.json"])
        self.assertEqual(routes, {"version": 1, "include": [ROUTE], "exclude": []})
        self.assertIn("docs/htmx-playground.html", files)
        self.assertIn("docs/vendor/htmx-2.0.11.min.js", files)
        self.assertNotIn("functions/api/htmx-demo/customers.js", files)
        self.assertNotIn("lib/htmx-demo.mjs", files)

    def test_no_functions_manifest_on_portable_static_export(self):
        files = source_files(include_cloudflare_headers=False)
        self.assertNotIn("_routes.json", files)
        self.assertIn("docs/htmx-playground.html", files)

    def test_demo_is_discoverable_but_not_a_core_runtime(self):
        html = (ROOT / "docs/htmx-playground.html").read_text()
        self.assertIn("hx-get", html)
        self.assertIn("htmx-2.0.11.min.js", html)
        self.assertIn('method="get"', html)
        self.assertIn("customer-results", html)
        self.assertIn("aria-live", html)
        self.assertIn("htmx-playground.html", (ROOT / "docs/htmx-components.md").read_text())
        self.assertIn("htmx-playground.html", (ROOT / "docs/guides.html").read_text())
        self.assertIn("docs/htmx-playground.html", (ROOT / "llms.txt").read_text())
        self.assertNotIn("htmx-2.0.11", (ROOT / "scripts/build.py").read_text())
        self.assertNotIn("htmx-2.0.11", (ROOT / "package.json").read_text())

    @unittest.skipUnless(shutil.which("node"), "Node is optional; Cloudflare deploys the JS handler")
    def test_function_runtime_with_node_builtin_tests(self):
        proc = subprocess.run(
            ["node", "--test", "tests/htmx_live_playground.test.mjs"],
            cwd=ROOT, text=True, capture_output=True, timeout=25,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
