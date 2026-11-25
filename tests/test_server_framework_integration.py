"""Opt-in server-rendered framework compatibility; no added core runtime."""
from html.parser import HTMLParser
from pathlib import Path
import json
import unittest

from scripts.build import distributions

ROOT = Path(__file__).resolve().parents[1]


class TagParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class ServerFrameworkIntegrationTests(unittest.TestCase):
    def test_optional_stylesheet_is_distributed_and_does_not_change_core(self):
        files = distributions()
        self.assertEqual(files["syntyr.server.css"], ("server.css",))
        self.assertNotIn("server.css", files["syntyr.core.css"])
        self.assertNotIn("server.css", files["syntyr.semantic-bundle.css"])
        self.assertIn("server.css", files["syntyr.all.css"])
        self.assertEqual(
            (ROOT / "src/server.css").read_text().strip() + "\n",
            (ROOT / "dist/syntyr.server.css").read_text(),
        )
        pkg = json.loads((ROOT / "package.json").read_text())
        self.assertEqual(pkg["exports"]["./server.css"], "./dist/syntyr.server.css")

    def test_opt_in_styles_are_scoped_and_do_not_manage_state_or_dom(self):
        css = (ROOT / "src/server.css").read_text()
        self.assertIn("@layer syn.components", css)
        self.assertIn(".syn-root", css)
        for token in (
            "[data-loading]", ".htmx-request", ".phx-click-loading",
            ".phx-submit-loading", ".phx-change-loading", "turbo-frame[busy]",
            '[data-syn-state="loading"]',
        ):
            with self.subTest(token=token):
                self.assertIn(token, css)
        self.assertNotIn("!important", css)
        self.assertNotIn("pointer-events: none", css)
        self.assertNotIn("opacity:", css)
        self.assertNotIn("animation:", css)
        self.assertNotIn("@import", css)
        self.assertNotIn("url(", css)

    def test_copyable_templates_use_identical_css_contract(self):
        fixtures = {
            "liveview.heex": ("phx-submit", "phx-change", "phx-disable-with"),
            "livewire.blade.php": ("wire:submit", "wire:model", "data-syn-theme"),
            "turbo.html": ("turbo-frame", "data-turbo-frame", 'method="get"'),
            "search.templ": ('templ Search(', 'method="get"', 'class="syn-button'),
        }
        for file, required in fixtures.items():
            with self.subTest(file=file):
                template = (ROOT / "examples/server-rendered" / file).read_text()
                self.assertIn("syn-root", template)
                self.assertIn("syn-input", template)
                self.assertIn("syn-button", template)
                self.assertNotIn("<script", template.lower())
                for fragment in required:
                    self.assertIn(fragment, template)
        turbo = TagParser()
        turbo.feed((ROOT / "examples/server-rendered/turbo.html").read_text())
        self.assertTrue(any(tag == "turbo-frame" for tag, _ in turbo.tags))
        self.assertTrue(any(tag == "form" and a.get("method") == "get" for tag, a in turbo.tags))

    def test_copy_owned_go_server_components_reuse_core_without_runtime(self):
        base = ROOT / "examples/server-components-go"
        mod = (base / "go.mod").read_text()
        component = (base / "templates/components.html").read_text()
        page = (base / "templates/page.html").read_text()
        handler = (base / "main.go").read_text()
        guide = (ROOT / "docs/framework-integrations.md").read_text()
        # Go module files permit tabs, newlines, and parenthesized directives.
        self.assertNotRegex(mod, r"(?m)^\s*require(?:\s|\()")
        self.assertIn('"html/template"', handler)
        self.assertIn('"net/url"', handler)
        self.assertIn('template.ParseFS', handler)
        self.assertNotIn("template.HTML(", handler)
        self.assertIn("examples/server-components-go", guide)
        self.assertIn("examples/server-components-go", (ROOT / "llms.txt").read_text())
        for name in ("syn.field", "syn.notice", "syn.button", "syn.table", "syn.pagination"):
            self.assertIn('{{define "' + name + '"}}', component)
            self.assertIn('{{template "' + name + '"', page)
        for attr in ('aria-invalid="true"', 'aria-describedby=', 'role="alert"', 'scope="col"', 'scope="row"'):
            if attr == 'role="alert"':
                self.assertIn('role="{{if .Danger}}alert', component)
            else:
                self.assertIn(attr, component)
        for css_class in ("syn-field", "syn-input", "syn-alert", "syn-button", "syn-table"):
            self.assertIn(css_class, component)
        self.assertIn("syntyr.core.css", page)
        self.assertNotIn("<script", page.lower())
        self.assertNotIn("<script", component.lower())

    def test_optional_node_and_templ_adapters_share_native_component_contract(self):
        node = ROOT / "examples/server-components-node"
        go = ROOT / "examples/server-components-templ"
        node_html = (node / "components.mjs").read_text()
        node_server = (node / "server.mjs").read_text()
        templ_markup = (go / "components.templ").read_text()
        go_mod = (go / "go.mod").read_text()
        guide = (ROOT / "docs/framework-integrations.md").read_text()
        llms = (ROOT / "llms.txt").read_text()
        for name in ("field", "notice", "button", "table", "pagination"):
            self.assertIn("export function " + name + "(", node_html)
            self.assertIn("templ " + name.title() + "(", templ_markup)
        for cls in ("syn-field", "syn-input", "syn-alert", "syn-button", "syn-table"):
            self.assertIn(cls, node_html)
            self.assertIn(cls, templ_markup)
        for required in ('scope="col"', 'scope="row"', 'aria-describedby=', 'aria-current="page"'):
            self.assertIn(required, node_html)
            self.assertIn(required, templ_markup)
        self.assertIn("escapeHtml", node_html)
        self.assertIn("danger ? 'alert'", node_html)
        self.assertIn('role="alert"', templ_markup)
        self.assertIn("safePageHref", node_html)
        self.assertIn("URLSearchParams", node_server)
        self.assertIn("showResults", node_server)
        self.assertIn("showResults", node_html)
        self.assertIn("ShowResults", (go / "models.go").read_text())
        self.assertIn("data.ShowResults", templ_markup)
        self.assertIn("url.ParseQuery", (go / "main.go").read_text())
        self.assertIn("X-Content-Type-Options", node_server)
        self.assertIn("github.com/a-h/templ v0.3.1100", go_mod)
        self.assertIn("@Field(data.Query)", templ_markup)
        self.assertIn("@Pagination(data.Pager)", templ_markup)
        for path in ("server-components-node", "server-components-templ"):
            self.assertIn("examples/" + path, guide)
            self.assertIn("examples/" + path, llms)
        self.assertNotIn("<script", node_html.lower())
        self.assertNotIn("<script", templ_markup.lower())
        self.assertNotIn('"./server-components-node"', (ROOT / "package.json").read_text())

    def test_opt_in_htmx_and_datastar_fragments_reuse_node_components(self):
        base = ROOT / "examples/server-components-node/fragments"
        server = (base / "server.mjs").read_text()
        hook = (base / "htmx-validation.js").read_text()
        guide = (ROOT / "docs/framework-integrations.md").read_text()
        llms = (ROOT / "llms.txt").read_text()
        self.assertIn("from '../components.mjs'", server)
        self.assertIn("from '../server.mjs'", server)
        for token in ("field, notice, button, table, pagination", "pageData",
                      "renderWorkspace", "renderDocument", "HX-History-Restore-Request",
                      "X-Syntyr-Validation", "Vary: 'Accept'", "datastar-patch-elements",
                      "text/event-stream", "aria-live", "Cache-Control",
                      "X-Content-Type-Options", "JSON.parse(raw)",
                      "scopedPageHref", "ssePatch", "parseSignals"):
            self.assertIn(token, server)
        self.assertIn("htmx:beforeSwap", hook)
        self.assertIn("status === 422", hook)
        self.assertIn("X-Syntyr-Validation", hook)
        self.assertIn("node:test", (base / "test/fragment-server.test.mjs").read_text())
        self.assertIn("examples/server-components-node/fragments", guide)
        self.assertIn("examples/server-components-node/fragments", llms)
        self.assertTrue((ROOT / "tests/server_html_fragments_browser.py").is_file())
        self.assertNotIn("server-components-node/fragments", (ROOT / "package.json").read_text())
        self.assertNotIn("node_modules", (base / "README.md").read_text())

    def test_docs_cover_versions_and_dom_ownership_without_claiming_runtime(self):
        guide = (ROOT / "docs/framework-integrations.md").read_text()
        for name in ("LiveView", "Livewire", "Turbo", "HTMX", "Go templ",
                     "syntyr.server.css", "wire:loading", "data-loading",
                     "phx-submit-loading", "turbo-frame[busy]", "aria-busy"):
            self.assertIn(name, guide)
        self.assertIn("examples/server-rendered/", guide)
        self.assertIn("zero", guide.lower())


if __name__ == "__main__":
    unittest.main()
