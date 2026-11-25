"""Hypertext framework contracts: scoped CSS, progressive fallback, Datastar SSE.

No third-party runtime is required for these tests.
"""
from html.parser import HTMLParser
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class HypertextCompatibilityTests(unittest.TestCase):
    def test_unpoly_request_styles_are_scoped_and_opt_in(self):
        css = (ROOT / "src/server.css").read_text()
        self.assertIn(".up-active", css)
        self.assertIn("form.up-active", css)
        self.assertIn(".syn-root", css)
        for forbidden in ("!important", "pointer-events: none", "opacity:", "animation:", "@import", "url("):
            self.assertNotIn(forbidden, css)
        self.assertNotIn(".up-active", (ROOT / "dist/syntyr.core.css").read_text())

    def test_datastar_example_preserves_real_form_and_stable_morph_boundary(self):
        html = (ROOT / "examples/datastar.html").read_text()
        parsed = Tags()
        parsed.feed(html)
        attrs = parsed.tags
        root = next(a for t, a in attrs if t == "main" and "syn-root" in a.get("class", ""))
        self.assertIn("data-syn-theme", root)
        form = next(a for t, a in attrs if t == "form")
        self.assertEqual(form["action"], "/customers/search")
        self.assertEqual(form["method"], "get")
        self.assertEqual(form["data-indicator:_fetching"], "")
        self.assertIn("@get('/customers/search')", form["data-on:submit"])
        self.assertIn("$_fetching", form["data-attr:aria-busy"])
        field = next(a for t, a in attrs if t == "input" and a.get("name") == "q")
        self.assertEqual(field["data-bind:q"], "")
        self.assertTrue(field.get("id"))
        button = next(a for t, a in attrs if t == "button" and a.get("type") == "submit")
        self.assertIn("syn-button", button["class"])
        self.assertIn("$_fetching", button["data-attr:disabled"])
        self.assertIn("$_fetching", button["data-attr:data-syn-state"])
        results = next(a for t, a in attrs if a.get("id") == "customer-results")
        self.assertNotEqual(results.get("class"), root.get("class"))
        self.assertIn("aria-live", results)
        self.assertIn("data-show", html)
        self.assertIn("style=\"display: none\"", html)
        self.assertIn("datastar@v1.0.5", html)

    def test_documentation_covers_supported_hypertext_ownership_and_limits(self):
        guide = (ROOT / "docs/framework-integrations.md").read_text()
        for keyword in ("Datastar", "Unpoly", "HTMX", "Turbo", "Alpine", "LiveView",
                        "Livewire", "data-indicator", "data-bind:q", "data-on:submit",
                        "data-syn-state", "CSP", "SSE", "data-turbo-permanent"):
            self.assertIn(keyword, guide)
        self.assertIn("examples/datastar_server.py", guide)
        self.assertIn("examples/datastar.html", guide)


class DatastarServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from examples.datastar_server import DemoHandler
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def get(self, path, accept="text/html"):
        with urlopen(Request(self.url + path, headers={"Accept": accept}), timeout=5) as r:
            return r, r.read().decode("utf-8")

    def test_native_form_fallback_returns_full_page_and_cache_safety(self):
        response, html = self.get("/customers/search?q=Acme")
        self.assertIn("text/html", response.headers["Content-Type"])
        self.assertIn("Accept", response.headers["Vary"])
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertIn('class="syn-root', html)
        self.assertIn("Acme Corporation", html)
        self.assertIn('name="q" value="Acme"', html)

    def test_datastar_signal_query_returns_escaped_sse_patch(self):
        payload = quote(json.dumps({"q": "<script>alert(1)</script>"}), safe="")
        response, sse = self.get("/customers/search?datastar=" + payload, "text/event-stream")
        self.assertIn("text/event-stream", response.headers["Content-Type"])
        self.assertIn("Accept", response.headers["Vary"])
        self.assertIn("event: datastar-patch-elements", sse)
        self.assertIn("data: elements <section id=\"customer-results\"", sse)
        self.assertIn("&lt;script&gt;", sse)
        self.assertNotIn("<script>", sse)
        self.assertTrue(sse.endswith("\n\n"))

    def test_datastar_sse_rejects_protocol_framing_from_carriage_returns(self):
        malicious = "\\r\\nevent: datastar-patch-signals\\r\\ndata: signals {isAdmin: true}\\r\\n\\r\\n"
        # Decode JSON into actual CR/LF bytes inside the user's query string.
        malicious = malicious.replace("\\r", "\r").replace("\\n", "\n")
        payload = quote(json.dumps({"q": malicious}), safe="")
        response, sse = self.get("/customers/search?datastar=" + payload, "text/event-stream")
        self.assertEqual(response.status, 200)
        self.assertNotIn("\r", sse)
        self.assertEqual(sse.count("event: datastar-patch-elements"), 1)
        self.assertNotIn("\nevent: datastar-patch-signals", sse)
        self.assertNotIn("\ndata: signals", sse)
        self.assertEqual(sse.count("\n\n"), 1)

    def test_malformed_signal_json_cannot_crash_handler(self):
        response, sse = self.get("/customers/search?datastar=%7Bbad", "text/event-stream")
        self.assertEqual(response.status, 200)
        self.assertIn("datastar-patch-elements", sse)

    def test_static_assets_are_allowlisted(self):
        response, css = self.get("/dist/syntyr.server.css", "text/css")
        self.assertIn("text/css", response.headers["Content-Type"])
        self.assertIn("syn.components", css)
        with self.assertRaises(HTTPError) as error:
            self.get("/etc/passwd")
        self.assertEqual(error.exception.code, 404)
        error.exception.close()


if __name__ == "__main__":
    unittest.main()
