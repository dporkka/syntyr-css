"""Optional real-browser parity for portable starters and static CMS outputs.

Run from the root: python3 -m tests.static_site_visual_browser
Optional maintainer dependencies: Playwright + Pillow, local Chromium.
Pass --cms-site NAME DIRECTORY BASE for each built independent CMS fixture.
Screenshots are compared within the same run; no system-font-dependent golden
images or browser dependencies ship with Syntyr.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
import json
import os
import shutil
import tempfile
import threading
from urllib.parse import urlsplit

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

from scripts.export_site_starter import STARTER_ROUTES, export_starter
from scripts.render_cms_starter import render_document

ROOT = Path(__file__).resolve().parents[1]
VIEWPORTS = (320, 390, 1280)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@contextmanager
def serve(directory):
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(directory)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def capture(browser, url, width, *, interactions=False):
    origin = urlsplit(url).netloc
    failures = []
    context = browser.new_context(viewport={"width": width, "height": 900}, device_scale_factor=1,
                                  java_script_enabled=False, reduced_motion="reduce")
    try:
        def local_only(route):
            if urlsplit(route.request.url).netloc == origin:
                route.continue_()
            else:
                failures.append("External request: " + route.request.url)
                route.abort()

        context.route("**/*", local_only)
        page = context.new_page()
        page.on("pageerror", lambda error: failures.append(str(error)))
        page.on("requestfailed", lambda request: failures.append(f"Failed: {request.url}"))
        page.on("response", lambda response: failures.append(f"HTTP {response.status}: {response.url}")
                if response.status >= 400 and not response.url.endswith("/favicon.ico") else None)
        page.goto(url, wait_until="load")
        page.evaluate("document.fonts.ready")
        assert page.locator("main").count() == 1, f"{url}: expected one main"
        assert page.locator("h1").count() == 1, f"{url}: expected one h1"
        assert page.locator(".syn-root").count(), f"{url}: missing Syntyr scope"
        assert page.evaluate("Array.from(document.styleSheets).every(s => s.cssRules.length > 0) && document.styleSheets.length > 0"), f"{url}: missing local CSS"
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), f"{url} overflows at {width}px"
        image = page.screenshot(full_page=True, animations="disabled")
        if interactions:
            page.keyboard.press("Tab")
            assert "skip" in page.locator(":focus").inner_text().lower(), f"{url}: skip link not first"
            page.keyboard.press("Enter")
            assert urlsplit(page.url).fragment in ("main", "content"), f"{url}: keyboard skip failed"
            details = page.locator("details").first
            if details.count():
                assert not details.evaluate("e => e.open"), f"{url}: unexpected initial disclosure"
                details.locator("summary").click()
                assert details.evaluate("e => e.open"), f"{url}: native disclosure did not open"
            # Verify a real primary-nav transition, if there is a local noncurrent link.
            nav = page.locator('nav[aria-label="Primary"] a:not([aria-current])').first
            if nav.count():
                href = nav.get_attribute("href")
                if href and not urlsplit(href).scheme and not href.startswith("#"):
                    nav.click()
                    page.wait_for_load_state("load")
                    assert page.locator("main").count() == 1, f"{url}: navigation failed"
        assert not failures, failures
        return image
    finally:
        context.close()


def assert_visual_match(reference, candidate, label, *, tolerance=0.002):
    """Within-run full-page pixel equivalence with a small antialias tolerance."""
    with Image.open(BytesIO(reference)) as one, Image.open(BytesIO(candidate)) as two:
        a, b = one.convert("RGB"), two.convert("RGB")
        assert a.size == b.size, f"{label}: screenshot dimensions differ {a.size} != {b.size}"
        channels = ImageChops.difference(a, b).split()
        difference = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
        changed = sum(difference.histogram()[25:]) / (a.width * a.height)
        assert changed <= tolerance, f"{label}: {changed:.3%} pixels differ (tolerance {tolerance:.3%})"


def starter_matrix(browser):
    cases = 0
    with tempfile.TemporaryDirectory(prefix="syntyr-starter-browser-") as temp:
        mount = Path(temp) / "nested"
        mount.mkdir()
        for name in STARTER_ROUTES:
            export_starter(name, mount / name)
        with serve(ROOT) as source_url, serve(Path(temp)) as export_url:
            for name, routes in STARTER_ROUTES.items():
                for route in routes:
                    for width in VIEWPORTS:
                        preview = capture(browser, f"{source_url}/examples/site-starters/{name}/{route}", width)
                        deployed = capture(browser, f"{export_url}/nested/{name}/{route}", width,
                                           interactions=True)
                        assert_visual_match(preview, deployed, f"{name}/{route} {width}px")
                        cases += 1
                print(f"PASS {name}: {len(routes) * len(VIEWPORTS)} preview/export browser comparisons")
    return cases


def parse_mount(base):
    if not base.startswith("/") or not base.endswith("/") or "//" in base:
        raise ValueError(f"Expected /mount/ base path: {base}")
    segments = base.strip("/").split("/") if base != "/" else []
    if any(part in ("", ".", "..") or not part.replace("-", "").replace("_", "").isalnum()
           for part in segments):
        raise ValueError(f"Unsafe mount path: {base}")
    return segments


def cms_matrix(browser, fixtures):
    cases = 0
    document = json.loads((ROOT / "examples/cms-starter/content/pages/home.json").read_text())
    with tempfile.TemporaryDirectory(prefix="syntyr-cms-visual-") as temp:
        root = Path(temp)
        reference = root / "reference"
        css = reference / "css"
        css.mkdir(parents=True)
        for name in ("syntyr.core.css", "syntyr.recipes.css"):
            shutil.copyfile(ROOT / "dist" / name, css / name)
        (reference / "index.html").write_text(render_document(document), encoding="utf-8")
        with serve(reference) as origin:
            screenshots = {width: capture(browser, origin + "/index.html", width) for width in VIEWPORTS}
        for index, (name, directory, base) in enumerate(fixtures):
            # Separate servers avoid overlapping mount paths; copy only built public output.
            source = Path(directory).resolve()
            if not (source / "index.html").is_file():
                raise ValueError(f"{name}: no built index.html in {source}")
            if any(path.is_symlink() for path in source.rglob("*")):
                raise ValueError(f"{name}: unexpected symlink in built fixture")
            served = root / f"fixture-{index}"
            mount = served.joinpath(*parse_mount(base))
            shutil.copytree(source, mount)
            with serve(served) as origin:
                for width in VIEWPORTS:
                    image = capture(browser, origin + base + "index.html", width, interactions=True)
                    assert_visual_match(screenshots[width], image, f"{name} CMS {width}px")
                    cases += 1
            print(f"PASS {name}: {len(VIEWPORTS)} CMS visual comparisons with Python reference")
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cms-site", nargs=3, action="append", metavar=("NAME", "DIRECTORY", "BASE"), default=[])
    parser.add_argument("--cms-only", action="store_true", help="Skip portable starter previews; requires CMS sites")
    args = parser.parse_args()
    if (args.cms_only or args.cms_site) and len(args.cms_site) < 2:
        parser.error("Supply at least two independently built CMS sites for cross-generator parity")
    names = [name for name, _, _ in args.cms_site]
    directories = [Path(directory).resolve() for _, directory, _ in args.cms_site]
    if len(set(names)) != len(names) or len(set(directories)) != len(directories):
        parser.error("CMS fixtures must use distinct names and output directories")
    executable = os.environ.get("SYNTYR_CHROMIUM_EXECUTABLE")
    with sync_playwright() as playwright:
        options = {"headless": True}
        if executable:
            options.update(executable_path=executable, args=["--no-sandbox"])
        browser = playwright.chromium.launch(**options)
        try:
            total = 0 if args.cms_only else starter_matrix(browser)
            if args.cms_site:
                total += cms_matrix(browser, args.cms_site)
            print(f"PASS {total} browser comparisons (JavaScript disabled, local requests only)")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
