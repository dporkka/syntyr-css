"""Optional browser regression for enforced CSP on Cloudflare's generated site.

Run with the test-only Playwright environment:
    python3 tests/security_headers_browser.py --browsers chromium firefox webkit

Serves the exact publish directory over ephemeral HTTPS with the same global
_headers policy (requires the test host's openssl executable);
this is NOT a replacement for post-deploy verification at the public origin.
"""
from argparse import ArgumentParser
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import ssl
import subprocess
from tempfile import TemporaryDirectory
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / ".cloudflare-public"


def global_headers():
    rules = (PUBLIC / "_headers").read_text().split("\n\n", 1)[0].splitlines()
    assert rules[0] == "/*", "Global security headers must apply to every page"
    return dict(line.strip().split(": ", 1) for line in rules[1:] if line.strip())


class SecurityHeaderHandler(SimpleHTTPRequestHandler):
    security_headers = {}

    def end_headers(self):
        for name, value in self.security_headers.items():
            self.send_header(name, value)
        super().end_headers()

    def log_message(self, *_args):
        pass


@contextmanager
def local_site():
    SecurityHeaderHandler.security_headers = global_headers()
    # Test the production HTTPS CSP as written: WebKit upgrades loopback HTTP
    # subresources under upgrade-insecure-requests, which breaks HTTP-only tests.
    with TemporaryDirectory(prefix="syntyr-csp-tls-") as temp:
        cert = Path(temp) / "cert.pem"
        key = Path(temp) / "key.pem"
        subprocess.run(
            ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
             "-sha256", "-days", "1", "-subj", "/CN=localhost",
             "-addext", "subjectAltName=IP:127.0.0.1,DNS:localhost",
             "-keyout", str(key), "-out", str(cert)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=20,
        )
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SecurityHeaderHandler, directory=str(PUBLIC)))
        tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        tls.load_cert_chain(certfile=str(cert), keyfile=str(key))
        server.socket = tls.wrap_socket(server.socket, server_side=True)
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            yield f"https://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            worker.join(timeout=3)
            server.server_close()


def verify(browser, origin):
    context = browser.new_context(ignore_https_errors=True)
    try:
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        response = page.goto(origin + "/docs/playground.html", wait_until="load")
        assert response.status == 200
        assert "script-src 'self'" in response.headers["content-security-policy"]
        frame = page.frame_locator("#playground-preview")
        frame.locator(".syn-stat").first.wait_for(timeout=10000)
        assert frame.locator(".syn-stat").count() == 3
        studio = frame.locator("body").evaluate("e => getComputedStyle(e).getPropertyValue('--syn-accent').trim()")
        assert studio == "#2458c6", f"srcdoc iframe stylesheet failed: {studio}"
        page.locator("#playground-theme").select_option("grid")
        frame.locator("body[data-syn-theme='grid']").wait_for()
        grid = frame.locator("body").evaluate("e => getComputedStyle(e).getPropertyValue('--syn-accent').trim()")
        assert grid == "#76e7f7", f"External playground script blocked by CSP: {grid}"
        editor = page.locator('#playground-editor-mount .cm-content[contenteditable="true"]')
        editor.wait_for()
        editor.click()
        page.keyboard.press('ControlOrMeta+A')
        page.keyboard.insert_text('<div id="safe-csp">Safe content</div><script>parent.document.body.dataset.injected="yes"</script>')
        frame.locator("#safe-csp").wait_for()
        assert page.locator("body").get_attribute("data-injected") is None, "Sandbox escaped"
        # Injecting a DOM script with text content should be blocked by CSP.
        page.evaluate("""() => { const script = document.createElement('script');
            script.textContent = 'window.__syntyrInlineScriptExecuted = true';
            document.head.appendChild(script); }""")
        assert page.evaluate("() => Boolean(window.__syntyrInlineScriptExecuted)") is False, "Inline script executed"
        assert not errors, errors
        page.goto(origin + "/docs/catalog.html", wait_until="load")
        assert page.locator("#catalog-controls").is_visible(), "Catalog enhancement blocked by CSP"
        page.goto(origin + "/docs/how-to.html", wait_until="load")
        assert page.locator("#howto-controls").is_visible(), "How-To search blocked by CSP"
        page.locator("#howto-search").fill("pricing")
        assert page.locator(".howto-card:visible").count() == 1
        assert not errors, errors
    finally:
        context.close()


def main():
    parser = ArgumentParser()
    parser.add_argument("--browsers", nargs="+", choices=("chromium", "firefox", "webkit"), default=["chromium"])
    args = parser.parse_args()
    assert (PUBLIC / "_headers").is_file(), "Build Cloudflare site first"
    with local_site() as origin, sync_playwright() as playwright:
        for name in args.browsers:
            options = {"headless": True}
            if name == "webkit" and os.getenv("SYNTYR_WEBKIT_EXECUTABLE"):
                # Optional test-only executable for hosts with locally supplied WPE libraries.
                options["executable_path"] = os.environ["SYNTYR_WEBKIT_EXECUTABLE"]
            browser = getattr(playwright, name).launch(**options)
            try:
                verify(browser, origin)
                print(f"PASS {name}: enforced CSP, CSS, playground, sandbox, docs scripts")
            finally:
                browser.close()


if __name__ == "__main__":
    main()
