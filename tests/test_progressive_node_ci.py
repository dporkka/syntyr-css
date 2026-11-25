"""The progressive browser gate must not require PyPI to be reachable at runtime."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ProgressiveNodeCI(unittest.TestCase):
    def test_uses_known_working_playwright_node_image_and_locked_npm_dependencies(self):
        pipeline = (ROOT / ".woodpecker/progressive.yaml").read_text()
        lit = (ROOT / ".woodpecker/lit.yaml").read_text()
        marker = "mcr.microsoft.com/playwright:v1.65.0-noble@sha256:"
        self.assertIn(marker, pipeline)
        self.assertIn(marker, lit)
        self.assertIn("npm ci --prefix examples/lit", pipeline)
        self.assertIn("npm run test:progressive --prefix examples/lit", pipeline)
        self.assertNotIn("pip install", pipeline)

    def test_progressive_runner_reuses_node_playwright_with_real_python_fixture(self):
        pkg = json.loads((ROOT / "examples/lit/package.json").read_text())
        self.assertIn("test:progressive", pkg["scripts"])
        self.assertEqual(pkg["devDependencies"]["@playwright/test"], "1.65.0")
        config = (ROOT / "examples/lit/playwright.progressive.config.mjs").read_text()
        script = (ROOT / "examples/lit/progressive-tests/progressive.spec.mjs").read_text()
        self.assertIn('testDir: "./progressive-tests"', config)
        self.assertIn('testDir: "./tests"', (ROOT / "examples/lit/playwright.config.mjs").read_text())
        for fragment in ("chromium", "firefox", "webkit", "javaScriptEnabled: false",
                         "htmx_server.py", "reuseExistingServer: false"):
            self.assertIn(fragment, config)
        for fragment in ("native-recipes.html", "#example-email", "native-report-fallback",
                         "#search-button", "Acme Corporation", "toBeFocused", "page.mouse.click"):
            self.assertIn(fragment, script)
        self.assertNotIn("page.evaluate", script)


if __name__ == "__main__":
    unittest.main()
