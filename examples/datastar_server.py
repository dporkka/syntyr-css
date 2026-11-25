"""Localhost-only Datastar/Syntyr demo: SSE fragments plus native GET fallback.

Run: python3 examples/datastar_server.py
Open: http://127.0.0.1:8766/examples/datastar.html

Datastar is a pinned, demo-only browser dependency. Syntyr ships no JS.
"""
from __future__ import annotations

from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import json

if __package__:
    from .htmx_server import customer_results
else:
    from htmx_server import customer_results

ROOT = Path(__file__).resolve().parents[1]
ASSETS = {
    "/examples/datastar.html": ("examples/datastar.html", "text/html; charset=utf-8"),
    "/dist/syntyr.core.css": ("dist/syntyr.core.css", "text/css; charset=utf-8"),
    "/dist/syntyr.server.css": ("dist/syntyr.server.css", "text/css; charset=utf-8"),
}


def requested_query(parameters: dict[str, list[str]], *, streaming: bool) -> str:
    """Read only supported query inputs; signal values are never executable."""
    if streaming:
        raw = parameters.get("datastar", [""])[0]
        try:
            signals = json.loads(raw) if len(raw) <= 4096 else {}
        except (ValueError, TypeError):
            signals = {}
        query = signals.get("q", "") if isinstance(signals, dict) else ""
    else:
        query = parameters.get("q", [""])[0]
    return query.strip()[:120] if isinstance(query, str) else ""


def result_section(query: str) -> str:
    # SSE 'elements' must fit on one data line. IDs permit targeted morphing.
    # SSE line boundaries are CR, LF or CRLF: do not let untrusted text frame events.
    content = customer_results(query).replace("\r", " ").replace("\n", " ")
    return ('<section id="customer-results" class="syn-panel" role="region" '
            'aria-label="Search results" aria-live="polite">' + content + '</section>')


class DemoHandler(BaseHTTPRequestHandler):
    def respond(self, status: int, payload: bytes, mime: str, *, vary: bool = False):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if vary:
            self.send_header("Vary", "Accept")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path == "/":
            self.send_response(302)
            self.send_header("Location", "/examples/datastar.html")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if parsed.path == "/customers/search":
            streaming = "text/event-stream" in self.headers.get("Accept", "").lower()
            params = parse_qs(parsed.query, keep_blank_values=True)
            query = requested_query(params, streaming=streaming)
            if streaming:
                section = result_section(query)
                body = f"event: datastar-patch-elements\ndata: elements {section}\n\n"
                mime = "text/event-stream; charset=utf-8"
            else:
                html = (ROOT / "examples/datastar.html").read_text(encoding="utf-8")
                body = html.replace("<!-- RESULTS -->", customer_results(query)).replace(
                    'name="q" value=""', f'name="q" value="{escape(query, quote=True)}"', 1
                )
                mime = "text/html; charset=utf-8"
            self.respond(200, body.encode("utf-8"), mime, vary=True)
            return

        asset = ASSETS.get(parsed.path)
        if not asset:
            self.send_error(404)
            return
        source, mime = asset
        self.respond(200, (ROOT / source).read_bytes(), mime)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8766), DemoHandler).serve_forever()
