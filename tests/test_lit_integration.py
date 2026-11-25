"""Contracts for the opt-in Lit demonstration; no Node dependency for this suite."""
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples" / "lit"


class ElementParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class LitInteroperabilityContract(unittest.TestCase):
    def test_lit_demo_is_isolated_from_the_css_distribution(self):
        core = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        demo = json.loads((DEMO / "package.json").read_text(encoding="utf-8"))
        self.assertNotIn("dependencies", core)
        self.assertNotIn("devDependencies", core)
        self.assertTrue(demo["private"])
        self.assertIn("lit", demo["dependencies"])
        self.assertIn("esbuild", demo["devDependencies"])
        self.assertEqual(demo["scripts"]["build"].count("--bundle"), 3)
        self.assertTrue((DEMO / ".gitignore").is_file())
        self.assertNotIn("examples/lit", (ROOT / "scripts/build_cloudflare_site.py").read_text())

    def test_html_has_static_fallback_and_only_local_assets(self):
        html = (DEMO / "index.html").read_text(encoding="utf-8")
        parser = ElementParser()
        parser.feed(html)
        self.assertTrue(any(
            tag in {"main", "body"} and "syn-root" in attrs.get("class", "").split()
            for tag, attrs in parser.elements
        ))
        self.assertTrue(any(
            tag == "link" and attrs.get("href") == "../../dist/syntyr.core.css"
            for tag, attrs in parser.elements
        ))
        self.assertEqual(
            [attrs.get("src") for tag, attrs in parser.elements if tag == "script"],
            ["./dist/demo.js"],
        )
        for tag in ("syn-demo-status-panel", "syn-demo-shadow-signal"):
            self.assertTrue(any(el == tag for el, _ in parser.elements), tag)
        self.assertGreaterEqual(html.count("data-lit-fallback"), 2)
        self.assertNotIn("https://", html)
        self.assertNotIn("onclick=", html)

    def test_light_dom_component_uses_real_syntyr_classes_and_public_event(self):
        js = (DEMO / "status-panel.js").read_text(encoding="utf-8")
        self.assertIn("createRenderRoot()", js)
        self.assertIn("return this;", js)
        self.assertIn("data-lit-fallback", js)
        self.assertIn("syn-panel", js)
        self.assertIn("syn-status--success", js)
        self.assertIn("static properties", js)
        self.assertIn("reflect: true", js)
        self.assertIn("?disabled=", js)
        self.assertIn("new CustomEvent(", js)
        self.assertIn("bubbles: true", js)
        self.assertIn("composed: true", js)

    def test_shadow_dom_component_uses_inherited_tokens_and_exposes_parts(self):
        js = (DEMO / "shadow-signal.js").read_text(encoding="utf-8")
        self.assertIn("static styles = css", js)
        for token in ("--syn-surface", "--syn-text", "--syn-accent", "--syn-focus-ring"):
            self.assertIn(token, js)
        for part in ('part="panel"', 'part="toggle"'):
            self.assertIn(part, js)
        self.assertIn("aria-pressed=", js)
        self.assertIn("new CustomEvent(", js)
        self.assertNotIn("createRenderRoot()", js)

    def test_contract_and_guides_describe_interoperability_boundary(self):
        guide = (ROOT / "docs/lit-integration.md").read_text(encoding="utf-8")
        spec = (ROOT / "docs/component-authoring.md").read_text(encoding="utf-8")
        framework_guide = (ROOT / "docs/framework-integrations.md").read_text()
        readme = (ROOT / "README.md").read_text()
        for term in ("Shadow DOM", "Light DOM", "::part()", "--syn-", "npm ci",
                     "progressive enhancement", "custom event"):
            self.assertIn(term.lower(), guide.lower(), term)
        for term in ("disabled", "aria-", "data-syn-", "CSS", "CustomEvent", "keyboard"):
            self.assertIn(term.lower(), spec.lower(), term)
        self.assertIn("lit-integration.md", framework_guide)
        self.assertIn("lit-integration.md", readme)
        self.assertIn('href="lit-integration.html"', (ROOT / "docs/guides.html").read_text())
        self.assertTrue((DEMO / "tests/lit.spec.mjs").is_file())


    def test_lit_browser_ci_runs_outside_python_css_gate(self):
        pipeline = (ROOT / ".woodpecker/lit.yaml").read_text(encoding="utf-8")
        self.assertIn("npm ci --prefix examples/lit", pipeline)
        self.assertIn("npm run build --prefix examples/lit", pipeline)
        self.assertIn("npm test --prefix examples/lit", pipeline)
        demo = json.loads((DEMO / "package.json").read_text(encoding="utf-8"))
        self.assertIn("playwright:v" + demo["devDependencies"]["@playwright/test"] + "-noble", pipeline)
        self.assertNotIn("pip install", pipeline)
        self.assertIn("event: pull_request", pipeline)
        self.assertNotIn("npm ", (ROOT / ".woodpecker/quality.yaml").read_text())

    def test_lit_interop_pages_use_real_react_and_htmx_without_core_dependencies(self):
        demo = json.loads((DEMO / "package.json").read_text(encoding="utf-8"))
        for dep in ("react", "react-dom", "htmx.org", "lit"):
            self.assertIn(dep, demo["dependencies"])
        self.assertIn("@playwright/test", demo["devDependencies"])
        self.assertIn("playwright test", demo["scripts"]["test"])
        self.assertIn("react-interop.jsx", demo["scripts"]["build"])
        self.assertIn("htmx-interop.js", demo["scripts"]["build"])
        react_page = (DEMO / "react-interop.html").read_text(encoding="utf-8")
        htmx_page = (DEMO / "htmx-interop.html").read_text(encoding="utf-8")
        react_app = (DEMO / "react-interop.jsx").read_text(encoding="utf-8")
        self.assertIn("dist/react-demo.js", react_page)
        self.assertIn("onsyn-demo-status-change", react_app)
        self.assertIn("createRoot", react_app)
        self.assertIn('action="./htmx-result.html"', htmx_page)
        self.assertIn('hx-target="#htmx-result"', htmx_page)
        self.assertIn("dist/htmx-demo.js", htmx_page)
        self.assertIn("data-lit-fallback", htmx_page)
        self.assertNotIn("https://", react_page + htmx_page)

    def test_lit_interop_docs_cover_app_owned_behavior_and_shadow_boundaries(self):
        guide = (ROOT / "docs/lit-integration.md").read_text(encoding="utf-8")
        for text in ("react-interop.html", "htmx-interop.html", "form action",
                     "custom event", "Shadow DOM", "JavaScript"):
            self.assertIn(text.lower(), guide.lower())


    def test_native_web_components_remain_optional_and_framework_free(self):
        native = ROOT / "examples" / "web-components"
        for name in ("README.md", "index.html", "ssr.html",
                     "main.js", "status-toggle.js", "status-toggle.css"):
            self.assertTrue((native / name).is_file(), name)
        js = (native / "status-toggle.js").read_text(encoding="utf-8")
        self.assertIn("extends HTMLElement", js)
        self.assertIn("disconnectedCallback()", js)
        self.assertIn("new AbortController()", js)
        self.assertIn("this.shadowRoot", js)
        self.assertIn("textContent", js)
        self.assertNotIn('from "lit"', js)
        self.assertIn('shadowrootmode="open"',
                      (native / "ssr.html").read_text(encoding="utf-8"))
        self.assertIn("/examples/web-components/",
                      (DEMO / "server.mjs").read_text(encoding="utf-8"))
        self.assertTrue((DEMO / "tests" / "native.spec.mjs").is_file())


    def test_form_associated_fixture_is_optional_and_native_first(self):
        native = ROOT / "examples" / "web-components"
        js = (native / "asset-range.js").read_text(encoding="utf-8")
        html = (native / "form-associated.html").read_text(encoding="utf-8")
        self.assertTrue((native / "form-result.html").is_file())
        for feature in ("formAssociated = true", "attachInternals()",
                        "setFormValue(data,", "setValidity(", "formDisabledCallback(",
                        "formResetCallback()", "formStateRestoreCallback(", "AbortController"):
            self.assertIn(feature, js)
        self.assertIn('method="get"', html)
        self.assertIn('name="assets_min"', html)
        self.assertIn('name="assets_max"', html)
        self.assertIn('type="number"', html)
        self.assertIn('required', html)
        self.assertNotIn('type="hidden"', html)
        self.assertNotIn("from \"lit\"", js)
        self.assertNotIn("innerHTML", js)
        self.assertTrue((DEMO / "tests" / "form-associated.spec.mjs").is_file())
        self.assertNotIn("asset-range.js",
                         (ROOT / "scripts/build_cloudflare_site.py").read_text())


if __name__ == "__main__":
    unittest.main()
