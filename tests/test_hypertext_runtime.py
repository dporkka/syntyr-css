"""Contracts for real Unpoly and Turbo standalone HTML examples.

The server is localhost-only and the tests use only Python's standard library.
External runtime bundles are loaded only in opt-in browser tests.
"""
from html.parser import HTMLParser
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class HypertextRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from examples.hypertext_server import DemoHandler
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def get(self, path, headers=None):
        with urlopen(Request(self.base + path, headers=headers or {}), timeout=5) as response:
            return response.headers, response.read().decode("utf-8")

    def test_examples_keep_a_stable_theme_root_and_native_get_form(self):
        for framework in ("unpoly", "turbo"):
            with self.subTest(framework=framework):
                html = (ROOT / f"examples/{framework}.html").read_text()
                parsed = Tags()
                parsed.feed(html)
                main = next(attrs for tag, attrs in parsed.tags if tag == "main")
                form = next(attrs for tag, attrs in parsed.tags if tag == "form")
                field = next(attrs for tag, attrs in parsed.tags
                             if tag == "input" and attrs.get("name") == "q")
                self.assertIn("syn-root", main["class"])
                self.assertEqual(main["data-syn-theme"], "studio")
                self.assertEqual(form["method"], "get")
                self.assertEqual(form["action"], f"/customers/{framework}")
                self.assertTrue(field.get("id"))
                self.assertIn("syntyr.core.css", html)
                self.assertIn("syntyr.server.css", html)

    def test_framework_assets_are_pinned_and_not_packaged_as_syntyr_core(self):
        unpoly = (ROOT / "examples/unpoly.html").read_text()
        turbo = (ROOT / "examples/turbo.html").read_text()
        self.assertIn("unpoly@3.15.0", unpoly)
        self.assertIn("@hotwired/turbo@8.0.23", turbo)
        self.assertIn("up-target=\"#customer-results, #unpoly-search\"", unpoly)
        self.assertIn("up-fail-target=\"#unpoly-search\"", unpoly)
        self.assertIn("data-turbo-frame=\"customer-results\"", turbo)
        self.assertNotIn("unpoly.js", (ROOT / "dist/syntyr.core.css").read_text())
        self.assertNotIn("turbo.js", (ROOT / "dist/syntyr.server.css").read_text())

    def test_unpoly_native_request_renders_complete_page_and_escaped_results(self):
        response, html = self.get("/customers/unpoly?q=" + quote("<script>"))
        self.assertIn("text/html", response["Content-Type"])
        self.assertIn("<!doctype html>", html)
        self.assertIn('id="customer-results"', html)
        self.assertNotIn("<script></script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_turbo_frame_request_returns_only_matching_frame(self):
        response, html = self.get("/customers/turbo?q=Acme",
                                  headers={"Turbo-Frame": "customer-results"})
        self.assertEqual(response["Vary"], "Turbo-Frame")
        self.assertTrue(html.startswith('<turbo-frame id="customer-results">'))
        self.assertTrue(html.endswith("</turbo-frame>"))
        self.assertNotIn("<!doctype html>", html)
        self.assertIn("Acme Corporation", html)
        self.assertIn('value="Acme"', html)

    def test_turbo_plain_get_fallback_is_a_full_page(self):
        response, html = self.get("/customers/turbo?q=Acme")
        self.assertIn("<!doctype html>", html)
        self.assertIn("<turbo-frame", html)
        self.assertIn("Acme Corporation", html)

    def test_turbo_stream_request_updates_only_target_and_preserves_full_page_fallback(self):
        response, stream = self.get(
            "/customers/turbo-stream?q=Acme",
            headers={"Accept": "text/vnd.turbo-stream.html, text/html"}
        )
        self.assertEqual(response["Content-Type"], "text/vnd.turbo-stream.html; charset=utf-8")
        self.assertEqual(response["Vary"], "Accept")
        self.assertIn('<turbo-stream action="update" target="turbo-stream-results">', stream)
        self.assertIn("Acme Corporation", stream)
        self.assertNotIn("<!doctype", stream.lower())
        normal_response, html = self.get("/customers/turbo-stream?q=Acme")
        self.assertIn("text/html", normal_response["Content-Type"])
        self.assertEqual(normal_response["Vary"], "Accept")
        self.assertIn("<!doctype html>", html)
        self.assertIn('id="turbo-stream-results"', html)
        self.assertIn("Acme Corporation", html)
        self.assertEqual(html.count("Acme Corporation"), 1)
        escaped = quote("<script>attack()</script>")
        response, malicious_stream = self.get(
            "/customers/turbo-stream?q=" + escaped,
            headers={"Accept": "text/vnd.turbo-stream.html"}
        )
        self.assertIn("&lt;script&gt;", malicious_stream)
        self.assertNotIn("<script>attack()", malicious_stream)
        self.assertEqual(malicious_stream.count("<turbo-stream "), 1)

    def test_unpoly_failed_form_submission_returns_accessible_error_and_full_document(self):
        with self.assertRaises(HTTPError) as failure:
            self.get("/customers/unpoly?q=")
        response = failure.exception
        try:
            self.assertEqual(response.code, 422)
            self.assertIn("text/html", response.headers["Content-Type"])
            html = response.read().decode("utf-8")
            self.assertIn("<!doctype html>", html)
            self.assertIn('id="unpoly-search"', html)
            self.assertIn('aria-invalid="true"', html)
            self.assertIn('aria-describedby="unpoly-search-error"', html)
            self.assertIn('id="unpoly-search-error"', html)
        finally:
            response.close()

    def test_asset_routes_are_allowlisted_and_send_nosniff(self):
        response, css = self.get("/dist/syntyr.server.css")
        self.assertIn("text/css", response["Content-Type"])
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertIn("up-active", css)
        with self.assertRaises(HTTPError) as ctx:
            self.get("/../../etc/passwd")
        self.assertEqual(ctx.exception.code, 404)
        ctx.exception.close()


if __name__ == "__main__":
    unittest.main()
