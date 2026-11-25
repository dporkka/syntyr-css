"""Opt-in layout/reflow check of the exact Cloudflare allowlisted public HTML.

Run after the deterministic build:
  uv run --with playwright python tests/published_reflow_browser.py --browsers chromium firefox webkit

This covers text enlargement and CSS viewport reflow, NOT native browser UI
zoom, touch hardware, or manual screen-reader verification. Internal horizontal
scrolling is allowed only inside an actually scrollable ancestor.
"""
import argparse
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import tempfile
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_cloudflare_site import source_files  # noqa: E402

# CSS pixel viewports: small/large phones, tablet, laptops, widescreen,
# mobile landscape, and enlarged text at narrow widths.
VIEWPORTS = (
    (320, 800, 1), (375, 812, 1), (390, 844, 1), (430, 932, 1),
    (768, 1024, 1), (1024, 768, 1), (1440, 900, 1), (1920, 1080, 1),
    (667, 375, 1), (844, 390, 1),
    (320, 800, 1.5), (320, 800, 2), (390, 844, 2),
)

INSPECT = """() => {
  const root = document.documentElement;
  const controls = document.querySelectorAll('a, button, input, select, textarea, summary');
  function scrollableAncestor(node) {
    for (let p = node.parentElement; p; p = p.parentElement) {
      const style = getComputedStyle(p);
      if (/(auto|scroll)/.test(style.overflowX) && p.scrollWidth > p.clientWidth + 1) {
        // The scrollport must itself fit inside the viewport.
        const bounds = p.getBoundingClientRect();
        if (bounds.left >= -1 && bounds.right <= innerWidth + 1) return true;
      }
    }
    return false;
  }
  const clipped = [...controls].filter(el => {
    const style = getComputedStyle(el), r = el.getBoundingClientRect();
    if (!r.width || !r.height || style.display === 'none' || style.visibility === 'hidden') return false;
    if (el.closest('details:not([open])') && !el.closest('summary')) return false;
    return !scrollableAncestor(el) && (r.left < -1 || r.right > innerWidth + 1);
  }).slice(0, 5).map(el => [el.tagName, el.textContent.trim().slice(0, 45)]);
  const missingStyles = [...document.querySelectorAll('link[rel="stylesheet"]')]
    .filter(link => !link.sheet).map(link => link.getAttribute('href'));
  return {scrollWidth: root.scrollWidth, clientWidth: root.clientWidth, clipped, missingStyles};
}"""


# Minimum 24 CSS-pixel targets for standalone native controls. Associated
# <label> targets can satisfy the rule even when a native checkbox is 13px.
# This is a focused geometry regression, not a full WCAG 2.2 target-spacing audit.
INSPECT_TOUCH_TARGETS = """() => {
  const targets = document.querySelectorAll(
    'button, summary, input:not([type="hidden"]), select, textarea, [role="button"], [role="tab"]'
  );
  return [...targets].filter(el => {
    const style = getComputedStyle(el), r = el.getBoundingClientRect();
    if (el.disabled || !r.width || !r.height
        || style.display === 'none' || style.visibility === 'hidden') return false;
    if (el.closest('details:not([open])') && !el.closest('summary')) return false;
    if (r.width >= 24 && r.height >= 24) return false;
    const labels = [...document.querySelectorAll('label[for]')]
      .filter(label => el.id && label.htmlFor === el.id);
    const wrapped = el.closest('label');
    if (wrapped) labels.push(wrapped);
    return !labels.some(label => {
      const box = label.getBoundingClientRect();
      return box.width >= 24 && box.height >= 24;
    });
  }).slice(0, 12).map(el => {
    const r = el.getBoundingClientRect();
    return [el.tagName, (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 48),
            Math.round(r.width), Math.round(r.height)];
  });
}"""


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def copyfile(self, source, output):
        # Closing a page can abort an in-flight asset request. Do not mistake
        # the server's broken pipe for a page test failure; loading is checked.
        try:
            super().copyfile(source, output)
        except (BrokenPipeError, ConnectionResetError):
            pass


def check(browser, engine, origin, pages):
    cases = 0
    for width, height, scale in VIEWPORTS:
        context = browser.new_context(
            viewport={"width": width, "height": height},
            reduced_motion="reduce",
        )
        page = context.new_page()
        try:
            for name in pages:
                response = page.goto(f"{origin}/{name}", wait_until="load", timeout=15_000)
                assert response and response.status == 200, (engine, name, "HTTP", response)
                if scale != 1:
                    page.evaluate("(scale) => document.documentElement.style.fontSize = (16 * scale) + 'px'", scale)
                layout = page.evaluate(INSPECT)
                assert not layout["missingStyles"], (engine, name, width, scale, layout)
                assert layout["scrollWidth"] <= layout["clientWidth"] + 1 and not layout["clipped"], (
                    engine, name, width, scale, layout
                )
                if width in (320, 390) and scale == 1:
                    too_small = page.evaluate(INSPECT_TOUCH_TARGETS)
                    assert not too_small, (engine, name, "touch targets below 24px", too_small)
                if name == "examples/viz.html" and width == 320 and scale == 2:
                    heatmap = page.locator(".syn-viz-heatmap").first
                    grid = heatmap.evaluate("""e => ({
                        columns: getComputedStyle(e).gridTemplateColumns.split(' ').length,
                        inner: e.clientWidth, scroll: e.scrollWidth
                    })""")
                    assert grid["columns"] == 6 and grid["scroll"] <= grid["inner"] + 1, grid
                    details = page.locator(".viz-values").first
                    details.evaluate("e => e.open = true")
                    region = details.evaluate("""e => ({
                        scroll: e.scrollWidth, inner: e.clientWidth,
                        overflow: getComputedStyle(e).overflowX
                    })""")
                    assert region["overflow"] == "auto" and region["scroll"] > region["inner"], region
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
                cases += 1
        finally:
            context.close()
        print(f"PASS {engine}: {len(pages)} published pages, {width}x{height}px, font={scale}x", flush=True)
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browsers", nargs="+",
                        choices=("chromium", "firefox", "webkit"),
                        default=("chromium", "firefox", "webkit"))
    args = parser.parse_args()

    files = source_files()
    pages = sorted(name for name in files if name.endswith(".html"))
    assert "docs/reference.html" in pages
    assert "examples/landing.html" in pages
    assert "examples/viz.html" in pages
    with tempfile.TemporaryDirectory(prefix="syntyr-public-reflow-") as folder:
        base = Path(folder)
        for name, data in files.items():
            target = base / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(base)))
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        failures = 0
        total = 0
        try:
            with sync_playwright() as playwright:
                for engine in args.browsers:
                    try:
                        options = {"headless": True}
                        if engine == "webkit" and os.getenv("SYNTYR_WEBKIT_EXECUTABLE"):
                            options["executable_path"] = os.environ["SYNTYR_WEBKIT_EXECUTABLE"]
                        browser = getattr(playwright, engine).launch(**options)
                    except Exception as exc:
                        print(f"BLOCKED {engine}: {str(exc).splitlines()[0]}", flush=True)
                        failures += 1
                        continue
                    try:
                        total += check(browser, engine, f"http://127.0.0.1:{server.server_port}", pages)
                    except Exception as exc:
                        print(f"FAIL {engine}: {exc}", flush=True)
                        failures += 1
                    finally:
                        browser.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
    print(f"FINISHED {total} public reflow cases, {failures} failed/blocked engine(s)", flush=True)
    return int(bool(failures))


if __name__ == "__main__":
    sys.exit(main())
