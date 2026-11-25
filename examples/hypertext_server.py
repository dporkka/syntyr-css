"""Localhost-only HTML-fragment demonstration for Unpoly and Turbo Frames.

Run from repo root:
  python3 examples/hypertext_server.py
Then open /examples/unpoly.html or /examples/turbo.html at localhost:8767.
Production applications must provide their own HTTP handlers and authentication.
"""
from __future__ import annotations

from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

if __package__:
    from .htmx_server import customer_results
else:
    from htmx_server import customer_results

ROOT = Path(__file__).resolve().parents[1]

ASSETS = {
    "/examples/unpoly.html": ("examples/unpoly.html", "text/html; charset=utf-8"),
    "/examples/turbo.html": ("examples/turbo.html", "text/html; charset=utf-8"),
    "/dist/syntyr.core.css": ("dist/syntyr.core.css", "text/css; charset=utf-8"),
    "/dist/syntyr.server.css": ("dist/syntyr.server.css", "text/css; charset=utf-8"),
}


def render_page(framework: str, query: str, *, frame_only: bool = False,
                stream_fallback: bool = False, validation_error: bool = False) -> str:
    """Both HTML-enhanced and no-JS requests derive from identical escaped markup."""
    html = (ROOT / f"examples/{framework}.html").read_text(encoding="utf-8")
    html = html.replace("<!-- QUERY -->", escape(query, quote=True))
    # Full-page navigation should show the results in only the form's own target.
    html = html.replace("<!-- RESULTS -->",
                        customer_results(query) if not stream_fallback else "")
    html = html.replace("<!-- STREAM_RESULTS -->",
                        customer_results(query) if stream_fallback else "")
    if framework == "unpoly":
        if validation_error:
            html = html.replace(
                'id="unpoly-query"',
                'id="unpoly-query" aria-invalid="true" aria-describedby="unpoly-search-error"',
                1,
            )
            html = html.replace(
                "<!-- VALIDATION -->",
                '<p id="unpoly-search-error" class="syn-error" role="alert">'
                'Enter a customer name before searching.</p>',
            )
        else:
            html = html.replace("<!-- VALIDATION -->", "")
    if frame_only:
        open_tag = '<turbo-frame id="customer-results">'
        close_tag = '</turbo-frame>'
        start = html.index(open_tag)
        end = html.index(close_tag, start) + len(close_tag)
        return html[start:end]
    return html


class DemoHandler(BaseHTTPRequestHandler):
    def respond(self, status: int, body: bytes, content_type: str, *, vary: str = ""):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if vary:
            self.send_header("Vary", vary)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path == "/":
            self.send_response(302)
            self.send_header("Location", "/examples/unpoly.html")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if parsed.path in ("/customers/unpoly", "/customers/turbo", "/customers/turbo-stream"):
            framework = "unpoly" if parsed.path == "/customers/unpoly" else "turbo"
            params = parse_qs(parsed.query, keep_blank_values=True)
            query = params.get("q", [""])[0].strip()[:120]
            if parsed.path == "/customers/turbo-stream":
                # A GET form remains a full document without Turbo; enhanced requests
                # deliver a tiny stream that updates only its matched target.
                is_stream = "text/vnd.turbo-stream.html" in self.headers.get("Accept", "").lower()
                if is_stream:
                    body = (
                        '<turbo-stream action="update" target="turbo-stream-results"><template>'
                        + customer_results(query)
                        + "</template></turbo-stream>"
                    )
                    mime = "text/vnd.turbo-stream.html; charset=utf-8"
                else:
                    body = render_page("turbo", query, stream_fallback=True)
                    mime = "text/html; charset=utf-8"
                self.respond(200, body.encode("utf-8"), mime, vary="Accept")
                return
            if framework == "unpoly" and not query:
                body = render_page(framework, query, validation_error=True)
                self.respond(422, body.encode("utf-8"), "text/html; charset=utf-8")
                return
            # Turbo explicitly requests a matching frame, unlike a native GET.
            frame_only = framework == "turbo" and self.headers.get("Turbo-Frame") == "customer-results"
            html = render_page(framework, query, frame_only=frame_only)
            self.respond(200, html.encode("utf-8"), "text/html; charset=utf-8",
                         vary="Turbo-Frame" if framework == "turbo" else "")
            return
        asset = ASSETS.get(parsed.path)
        if not asset:
            self.send_error(404)
            return
        path, mime = asset
        self.respond(200, (ROOT / path).read_bytes(), mime)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8767), DemoHandler).serve_forever()
