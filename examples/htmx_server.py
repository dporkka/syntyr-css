"""Dependency-free, localhost-only HTMX progressive-enhancement example.

Run from the repo root:
  python3 examples/htmx_server.py
Open http://127.0.0.1:8765/examples/htmx.html

The HTMX script is an explicitly pinned demo-only browser dependency.
Syntyr itself ships no runtime JavaScript.
"""
from __future__ import annotations

from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
CUSTOMERS = ("Acme Corporation", "Northstar Media", "Orion Advertising", "Meridian Operations")
ASSETS = {
    "/examples/htmx.html": ("examples/htmx.html", "text/html; charset=utf-8"),
    "/examples/htmx.css": ("examples/htmx.css", "text/css; charset=utf-8"),
    "/examples/htmx-recovery.js": ("examples/htmx-recovery.js", "text/javascript; charset=utf-8"),
    "/dist/syntyr.core.css": ("dist/syntyr.core.css", "text/css; charset=utf-8"),
    "/dist/syntyr.semantic.css": ("dist/syntyr.semantic.css", "text/css; charset=utf-8"),
}


def customer_results(query: str) -> str:
    """Return escaped HTML; the query is never interpreted as markup."""
    matches = [name for name in CUSTOMERS if query.casefold() in name.casefold()]
    if not matches:
        return ('<div class="syn-empty" role="status">'
                '<h2>No matching customers</h2>'
                f'<p>Nothing found for <strong>{escape(query, quote=True)}</strong>.</p></div>')
    items = "\n".join(
        f'<article class="syn-panel"><h3 class="syn-heading">{escape(name)}</h3>'
        '<span class="syn-badge">Active</span></article>'
        for name in matches
    )
    return (f'<div class="syn-stack"><h2 class="syn-heading">{len(matches)} customers</h2>'
            f'{items}</div>')


class DemoHandler(BaseHTTPRequestHandler):
    def respond(self, status: int, payload: bytes, content_type: str, *, vary: bool = False):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if vary:
            self.send_header("Vary", "HX-Request, HX-History-Restore-Request")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path == "/":
            self.send_response(302)
            self.send_header("Location", "/examples/htmx.html")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if parsed.path == "/customers/search":
            query = parse_qs(parsed.query, keep_blank_values=True).get("q", [""])[0].strip()[:120]
            fragment = customer_results(query)
            if (self.headers.get("HX-Request", "").lower() == "true"
                    and self.headers.get("HX-History-Restore-Request", "").lower() != "true"):
                body = fragment
            else:
                template = (ROOT / "examples/htmx.html").read_text(encoding="utf-8")
                body = template.replace("<!-- RESULTS -->", fragment).replace(
                    'name="q" value=""', f'name="q" value="{escape(query, quote=True)}"', 1
                )
            self.respond(200, body.encode("utf-8"), "text/html; charset=utf-8", vary=True)
            return

        asset = ASSETS.get(parsed.path)
        if asset is None:
            self.respond(404, b"Not found", "text/plain; charset=utf-8")
            return
        filename, mime = asset
        self.respond(200, (ROOT / filename).read_bytes(), mime)


if __name__ == "__main__":
    print("Syntyr + HTMX demo: http://127.0.0.1:8765/examples/htmx.html", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8765), DemoHandler).serve_forever()
