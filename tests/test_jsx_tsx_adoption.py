"""Opt-in JSX runtime fixtures must consume the same pure CSS contract."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class JsxTsxAdoptionTests(unittest.TestCase):
    def test_preact_jsx_consumes_css_directly(self):
        root = ROOT / "examples/preact-jsx"
        package = json.loads((root / "package.json").read_text())
        self.assertIn("preact", package["dependencies"])
        self.assertIn("@syntyr/css", package["dependencies"])
        self.assertNotIn("@syntyr/react", package["dependencies"])
        entry = (root / "src/main.jsx").read_text()
        self.assertIn('@syntyr/css/core.css', entry)
        component = (root / "src/App.jsx").read_text()
        for contract in ('class="syn-root"', 'data-syn-theme="studio"', 'class="syn-panel"', 'class="syn-button syn-button--primary"', 'onClick'):
            self.assertIn(contract, component)

    def test_solid_tsx_consumes_css_directly(self):
        root = ROOT / "examples/solid-tsx"
        package = json.loads((root / "package.json").read_text())
        self.assertIn("solid-js", package["dependencies"])
        self.assertIn("@syntyr/css", package["dependencies"])
        self.assertNotIn("@syntyr/react", package["dependencies"])
        self.assertIn("vite-plugin-solid", package["devDependencies"])
        tsconfig = json.loads((root / "tsconfig.json").read_text())
        self.assertEqual(tsconfig["compilerOptions"]["jsx"], "preserve")
        self.assertEqual(tsconfig["compilerOptions"]["jsxImportSource"], "solid-js")
        self.assertIn('@syntyr/css/core.css', (root / "src/main.tsx").read_text())
        component = (root / "src/App.tsx").read_text()
        for contract in ('class="syn-root"', 'data-syn-theme="studio"', 'class="syn-panel"', 'class="syn-button syn-button--primary"', 'onClick'):
            self.assertIn(contract, component)

    def test_react_tsx_native_recipe_needs_no_wrappers(self):
        source = (ROOT / "examples/react-vite/src/NativeRecipe.tsx").read_text()
        for contract in ('className="syn-panel"', 'className="syn-input"', 'className="syn-button syn-button--primary"', 'htmlFor='):
            self.assertIn(contract, source)
        self.assertNotIn("@syntyr/react", source)
        self.assertIn("NativeRecipe", (ROOT / "examples/react-vite/src/App.tsx").read_text())

    def test_real_builds_and_optional_browser_include_all_consumers(self):
        runner = (ROOT / "scripts/test_js_adoption.py").read_text()
        ci = (ROOT / ".woodpecker/js-adoption.yaml").read_text()
        browser = (ROOT / "tests/js_adoption_browser.py").read_text()
        for folder in ("examples/preact-jsx", "examples/solid-tsx"):
            self.assertIn(folder, runner)
            self.assertIn(folder, ci)
            self.assertIn(folder, browser)
        guide = (ROOT / "docs/jsx-tsx-integration.md").read_text()
        for word in ("React", "Preact", "Solid", "JSX", "TSX", "className", "class=", "htmlFor", "for="):
            self.assertIn(word, guide)

    def test_core_remains_framework_neutral(self):
        package = json.loads((ROOT / "package.json").read_text())
        self.assertNotIn("dependencies", package)
        self.assertNotIn("peerDependencies", package)
        self.assertEqual(package["sideEffects"], ["**/*.css"])


if __name__ == "__main__":
    unittest.main()
