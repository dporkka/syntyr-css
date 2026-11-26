"""Optional build-time Hugo/Zola contract and rendered-content smoke tests.

No generator or Playwright is required for consumers or the default Python
suite. Uses loopback HTTP under non-root prefixes and disposable build output.
"""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.verify_static_generators import verify_static_site

TABLE = """| Name | Value |
| --- | --- |
| Long identifier | averylongunbrokenidentifierthatmustfitinsideanarrowreader |"""
TABLE_WRAPPER = '<div class="syn-table-wrap" role="region" aria-label="Inventory" tabindex="0">'
PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TITLE</title><link rel="stylesheet" href="ASSET"></head>
<body><main class="syn-root syn-page" data-syn-theme="studio">
<article class="syn-shell syn-prose"><h1>TITLE</h1>CONTENT</article>
</main></body></html>"""
IMAGE = '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="100"><rect width="800" height="100" fill="#2458c6"/></svg>'


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build(generator, executable, work, destination, origin):
    """Render the same Markdown using each generator's native shortcode API."""
    prefix = f"/{generator}-prose/"
    source = work / generator
    source.mkdir()
    contents = (ROOT / "tests/fixtures/generated-prose.md").read_text(encoding="utf-8")
    assert contents.count("<!-- TABLE -->") == 1
    base = origin + prefix
    if generator == "hugo":
        write(source / "hugo.toml", f'baseURL = "{base}"\ntitle = "Document"\ndisableKinds = ["taxonomy","term","RSS","sitemap","robotsTXT"]\n[markup.goldmark.renderer]\nunsafe = false\n')
        write(source / "layouts/home.html", PAGE.replace("TITLE", "{{ .Title }}").replace("ASSET", '{{ "assets/minimal.css" | relURL }}').replace("CONTENT", "{{ .Content }}"))
        write(source / "layouts/shortcodes/prose-table.html", TABLE_WRAPPER + "{{ .Inner | markdownify }}</div>")
        table = "{{< prose-table >}}\n" + TABLE + "\n{{< /prose-table >}}"
        command = [executable, "--source", str(source), "--destination", str(destination), "--quiet"]
    elif generator == "zola":
        write(source / "config.toml", f'base_url = "{base}"\ntitle = "Document"\n')
        asset = '{{ get_url(path="assets/minimal.css") | replace(from="' + origin + '", to="") }}'
        page = PAGE.replace("ASSET", asset)
        write(source / "templates/index.html", page.replace("TITLE", "{{ section.title }}").replace("CONTENT", "{{ section.content | safe }}"))
        write(source / "templates/404.html", page.replace("TITLE", "Not found").replace("CONTENT", ""))
        write(source / "templates/shortcodes/prose_table.html", TABLE_WRAPPER + "{{ body | markdown | safe }}</div>")
        table = "{% prose_table() %}\n" + TABLE + "\n{% end %}"
        command = [executable, "build", "--output-dir", str(destination)]
    else:
        raise ValueError(generator)
    write(source / "content/_index.md", '+++\ntitle = "Document"\n+++\n' + contents.replace("<!-- TABLE -->", table))
    assets = source / "static/assets"
    assets.mkdir(parents=True)
    shutil.copyfile(ROOT / "dist/presets/minimal.css", assets / "minimal.css")
    write(source / "static/status.svg", IMAGE)
    subprocess.run(command, cwd=source, check=True, timeout=60)
    pages = verify_static_site(destination, base_path=prefix)
    print(f"PASS {generator}: {pages} generated pages; local CSS, prefix and no scripts", flush=True)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def render(page, url, name, engine):
    page.goto(url, wait_until="load")
    assert page.locator("article.syn-prose").count() == 1
    assert page.locator("article.syn-prose h2").inner_text() == "Release notes"
    assert page.locator("input[type=checkbox]:disabled").count() == 2
    assert page.locator("input[type=checkbox]:checked").count() == 1
    assert page.get_by_role("region", name="Inventory").locator("table").count() == 1
    assert page.get_by_role("region", name="Inventory").get_attribute("tabindex") == "0"
    assert page.locator("a[href^='#']").count() >= 1
    assert page.locator("a[href^='#']").evaluate_all(
        "links => links.every(a => document.getElementById(decodeURIComponent(a.hash.slice(1))))")
    pre = page.locator("article pre")
    assert pre.evaluate("e => getComputedStyle(e).overflowX") == "auto"
    assert page.locator("article blockquote").evaluate("e => getComputedStyle(e).borderInlineStartWidth") == "2px"
    assert page.locator("article img").evaluate("e => e.complete && e.naturalWidth === 800")
    for palette in ("studio", "grid", "noir", "industrial", "terminal", "corporate", "minimal"):
        page.locator("main").evaluate("(e, t) => e.dataset.synTheme = t", palette)
        for width in (320, 390, 1280):
            page.set_viewport_size({"width": width, "height": 800})
            for scale in ("100%", "200%", "400%"):
                page.evaluate("s => document.documentElement.style.fontSize = s", scale)
                assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"), (engine, name, palette, width, scale)
                assert page.locator("article img").evaluate("e => e.width <= e.parentElement.clientWidth + 1"), (engine, name, palette, width, scale)
    page.set_viewport_size({"width": 320, "height": 800})
    page.evaluate("document.documentElement.style.fontSize = '400%'")
    table = page.get_by_role("region", name="Inventory")
    assert table.evaluate("e => e.scrollWidth > e.clientWidth")
    table.focus()
    assert table.evaluate("e => document.activeElement === e")
    assert pre.evaluate("e => e.scrollWidth > e.clientWidth")
    print(f"PASS {engine}/{name}: 63 generated-content configurations; native table region, code overflow and image", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hugo", default="hugo")
    parser.add_argument("--zola", default="zola")
    parser.add_argument("--browsers", nargs="+", default=["chromium"])
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args()
    specs = [(name, shutil.which(getattr(args, name))) for name in ("hugo", "zola")]
    for name, exe in specs:
        if not exe:
            parser.error(f"{name} executable not found")
    with tempfile.TemporaryDirectory(prefix="syntyr-generated-prose-") as tmp:
        work = Path(tmp)
        site = work / "site"
        site.mkdir()
        with ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=site)) as server:
            origin = f"http://127.0.0.1:{server.server_port}"
            for name, exe in specs:
                subprocess.run([exe, "version" if name == "hugo" else "--version"], check=True)
                build(name, exe, work, site / f"{name}-prose", origin)
            if args.build_only:
                return
            from playwright.sync_api import sync_playwright
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with sync_playwright() as p:
                    for engine in args.browsers:
                        executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE") if engine == "chromium" else None
                        # An optional alternative Chromium is for isolated local
                        # testing; standard Playwright browser launches are unchanged.
                        launch = {"executable_path": executable} if executable else {}
                        if executable and os.environ.get("SYNTYR_TEST_CHROMIUM_SINGLE_PROCESS") == "1":
                            launch["args"] = ["--single-process", "--no-zygote", "--disable-gpu"]
                        browser = getattr(p, engine).launch(**launch)
                        try:
                            page = browser.new_page(viewport={"width": 320, "height": 800}, java_script_enabled=False)
                            for name, _ in specs:
                                render(page, f"{origin}/{name}-prose/", name, engine)
                        finally:
                            browser.close()
            finally:
                server.shutdown()
                thread.join()


if __name__ == "__main__":
    main()
