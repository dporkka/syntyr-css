"""Contracts for optional Node, React and Next.js consumers.

No consumer toolchain is required to run the Python suite; actual build and
HTTP/SSR checks live in the optional adoption verification script.
"""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NodeReactNextAdoptionTests(unittest.TestCase):
    def test_react_is_optional_and_package_is_server_safe(self):
        css = json.loads((ROOT / "package.json").read_text())
        react = json.loads((ROOT / "packages/react/package.json").read_text())
        self.assertNotIn("react", css.get("dependencies", {}))
        self.assertNotIn("react", css.get("peerDependencies", {}))
        self.assertIn("react", react["peerDependencies"])
        self.assertEqual(react["name"], "@syntyr/react")
        self.assertIn("./dist/index.js", react["exports"]["."]["import"])
        source = (ROOT / "packages/react/src/index.tsx").read_text()
        self.assertNotIn('"use client"', source)
        self.assertNotIn("'use client'", source)
        self.assertIn("forwardRef", source)
        for css_class in ("syn-root", "syn-button", "syn-panel", "syn-badge", "syn-input"):
            self.assertIn(css_class, source)

    def test_next_app_router_server_component_and_client_island(self):
        root = ROOT / "examples/next-app-router"
        pkg = json.loads((root / "package.json").read_text())
        self.assertIn("next", pkg["dependencies"])
        self.assertIn("@syntyr/css", pkg["dependencies"])
        self.assertIn("@syntyr/react", pkg["dependencies"])
        layout = (root / "app/layout.tsx").read_text()
        page = (root / "app/page.tsx").read_text()
        island = (root / "app/counter.tsx").read_text()
        self.assertIn("@syntyr/css/core.css", layout)
        self.assertIn("SyntyrRoot", layout)
        self.assertNotIn('"use client"', layout)
        self.assertNotIn('"use client"', page)
        self.assertIn('"use client"', island)
        self.assertIn("useState", island)

    def test_next_turbopack_root_includes_linked_monorepo_packages(self):
        # Next 16 defaults to Turbopack, which cannot import local file: links
        # outside the auto-detected Next app root. The config must be portable.
        config = (ROOT / "examples/next-app-router/next.config.mjs")
        self.assertTrue(config.is_file(), "Next must set its Turbopack workspace root")
        source = config.read_text()
        self.assertIn("turbopack:", source)
        self.assertIn("root:", source)
        self.assertIn("import.meta.url", source)
        self.assertIn('new URL("../..", import.meta.url)', source)
        self.assertIn("fileURLToPath", source)
        self.assertNotIn("process.cwd()", source)
        self.assertIn("turbopack.root", (ROOT / "docs/node-react-next-integration.md").read_text())

    def test_vite_react_is_real_consumer(self):
        root = ROOT / "examples/react-vite"
        pkg = json.loads((root / "package.json").read_text())
        self.assertIn("@syntyr/css", pkg["dependencies"])
        self.assertIn("@syntyr/react", pkg["dependencies"])
        self.assertIn("react-dom", pkg["dependencies"])
        self.assertIn("@syntyr/css/core.css", (root / "src/main.tsx").read_text())
        self.assertIn("createRoot", (root / "src/main.tsx").read_text())

    def test_node_template_escapes_user_input_and_serves_css(self):
        root = ROOT / "examples/node-express"
        pkg = json.loads((root / "package.json").read_text())
        self.assertIn("express", pkg["dependencies"])
        self.assertIn("ejs", pkg["dependencies"])
        server = (root / "server.mjs").read_text()
        template = (root / "views/index.ejs").read_text()
        self.assertIn('import.meta.resolve("@syntyr/css/core.css")', server)
        self.assertIn('express.static', server)
        self.assertIn('<%= query %>', template)
        self.assertNotIn('<%- query %>', template)
        self.assertIn('method="get"', template)
        self.assertTrue((root / "test/server.test.mjs").is_file())

    def test_documented_test_runner_exercises_built_consumers(self):
        runner = (ROOT / "scripts/test_js_adoption.py").read_text()
        for fixture in ("packages/react", "examples/react-vite", "examples/next-app-router", "examples/node-express"):
            self.assertIn(fixture, runner)
        self.assertTrue((ROOT / "docs/node-react-next-integration.md").is_file())
        self.assertTrue((ROOT / "tests/js_adoption_browser.py").is_file())
        self.assertIn("npm run build --prefix examples/next-app-router", (ROOT / ".woodpecker/js-adoption.yaml").read_text())


if __name__ == "__main__":
    unittest.main()
