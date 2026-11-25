"""Cross-stack HTML integration contracts; stdlib-only and offline."""
from html.parser import HTMLParser
from pathlib import Path
from threading import Thread
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attributes):
        self.tags.append((tag, dict(attributes)))


class HtmlIntegrationTests(unittest.TestCase):
    def test_semantic_styling_can_survive_dynamic_host_classes(self):
        css = (ROOT / "src/semantic.css").read_text(encoding="utf-8")
        for tag in ("button", "input", "select", "textarea", "article", "table", "label"):
            with self.subTest(tag=tag):
                self.assertIn(f"{tag}[data-syn-semantic]", css)
        self.assertIn("button:not([class])", css)
        self.assertIn("select:not([class])", css)
        self.assertNotIn(".htmx-request", css, "the semantic API must not depend on a framework")

    def test_browser_pending_state_uses_a_controlled_response_gate(self):
        source = (ROOT / "tests/htmx_browser.py").read_text()
        self.assertNotIn("time.sleep(0.3)", source)
        self.assertIn("threading", source)
        self.assertIn("search_response_gate", source)
        self.assertIn("search_response_gate.clear()", source)
        self.assertIn("search_response_gate.set()", source)
        self.assertIn("finally:", source)

    def test_htmx_example_has_native_form_fallback_and_is_opt_in(self):
        html = (ROOT / "examples/htmx.html").read_text(encoding="utf-8")
        parser = FormParser()
        parser.feed(html)
        forms = [attrs for tag, attrs in parser.tags if tag == "form"]
        self.assertEqual(len(forms), 1)
        form = forms[0]
        self.assertEqual(form["method"], "get")
        self.assertEqual(form["action"], "/customers/search")
        self.assertEqual(form["hx-get"], "/customers/search")
        self.assertEqual(form["hx-target"], "#results")
        self.assertEqual(form["hx-indicator"], "#search-button")
        self.assertTrue(any(tag in ("main", "body") and "syn-root" in a.get("class", "") for tag, a in parser.tags))
        self.assertTrue(any(tag == "button" and "data-syn-semantic" in a for tag, a in parser.tags))
        self.assertEqual(
            [a.get("src") for tag, a in parser.tags if tag == "script"],
            ["https://unpkg.com/htmx.org@2.0.8/dist/htmx.min.js",
             "/examples/htmx-recovery.js"],
        )
        self.assertNotIn("onload=", html)
        self.assertNotIn("onclick=", html)

    def test_htmx_history_cache_miss_has_full_document_even_with_hx_request_header(self):
        from examples.htmx_server import DemoHandler

        html = (ROOT / "examples/htmx.html").read_text(encoding="utf-8")
        self.assertIn('"historyRestoreAsHxRequest":false', html)

        server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/customers/search?q=Acme"
            headers = {"HX-Request": "true", "HX-History-Restore-Request": "true"}
            with urlopen(Request(url, headers=headers), timeout=5) as response:
                document = response.read().decode("utf-8")
                self.assertIn("<!doctype html>", document.lower())
                self.assertIn('id="results"', document)
                self.assertEqual(
                    response.headers["Vary"], "HX-Request, HX-History-Restore-Request"
                )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_server_returns_fragment_or_full_page_and_escapes_user_input(self):
        from examples.htmx_server import DemoHandler

        server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            url = base + "/customers/search?q=%3Cscript%3Ealert(1)%3C%2Fscript%3E"
            with urlopen(Request(url, headers={"HX-Request": "true"})) as response:
                fragment = response.read().decode()
                self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")
                self.assertEqual(response.headers["Vary"], "HX-Request, HX-History-Restore-Request")
                self.assertNotIn("<!doctype", fragment.lower())
                self.assertNotIn("<script>", fragment.lower())
                self.assertIn("&lt;script&gt;", fragment)
            with urlopen(url) as response:
                document = response.read().decode()
                self.assertIn("<!doctype html>", document.lower())
                self.assertIn('id="results"', document)
                self.assertIn("&lt;script&gt;", document)
                self.assertIn('name="q" value="&lt;script&gt;alert(1)&lt;/script&gt;"', document)
            with urlopen(base + "/examples/htmx.html") as response:
                self.assertIn('data-syn-semantic', response.read().decode())
            with urlopen(base + "/dist/syntyr.core.css") as response:
                self.assertIn("text/css", response.headers["Content-Type"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
