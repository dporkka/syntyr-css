"""Opt-in multi-page editor smoke test. Requires Python Playwright + Chromium.
Run: python3 tests/site_builder_browser.py
"""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def log_message(self, *_args):
        pass


def verify(browser, url):
    context = browser.new_context(viewport={"width": 1280, "height": 850}, accept_downloads=True)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(url + "/docs/page-builder.html", wait_until="load")
    preview = page.frame_locator("#builder-preview")
    expect(preview.locator(".syn-stage h1")).to_have_text("Build your next website visually.")

    page.locator("#builder-site-new-slug").fill("about")
    page.locator("#builder-site-add-page").click()
    expect(page.locator("#builder-site-page-select")).to_have_value("about")
    page.locator("#builder-page-title").fill("About Syntyr")
    page.locator("#builder-inspector [data-field='title']").fill("An independent about page")
    expect(preview.locator(".syn-stage h1")).to_have_text("An independent about page")

    page.locator("#builder-site-header-enabled").check()
    page.locator("#builder-site-header-brand").fill("Shared Syntyr brand")
    page.locator("#builder-site-header-brand").press("Tab")
    page.locator("#builder-site-footer-enabled").check()
    expect(preview.locator("header.syn-header strong")).to_have_text("Shared Syntyr brand")
    expect(preview.locator("footer.syn-region")).to_have_count(1)

    page.locator("#builder-site-page-select").select_option("")
    expect(preview.locator(".syn-stage h1")).to_have_text("Build your next website visually.")
    expect(preview.locator("header.syn-header strong")).to_have_text("Shared Syntyr brand")

    page.evaluate("""() => {
      const create = URL.createObjectURL.bind(URL);
      URL.createObjectURL = blob => { window.__lastSiteBlob = blob; return create(blob); };
    }""")
    with page.expect_download() as info:
        page.locator("#builder-export-json").click()
    assert info.value.suggested_filename == "syntyr-site.json"
    saved = json.loads(page.evaluate("async () => await window.__lastSiteBlob.text()"))
    assert saved["schema"] == "syntyr.site.v1"
    assert len(saved["pages"]) == 2
    assert saved["shared"]["header"]["props"]["brand"] == "Shared Syntyr brand"
    assert saved["pages"][1]["document"]["title"] == "About Syntyr"

    with page.expect_download() as info:
        page.locator("#builder-export-zip").click()
    assert info.value.suggested_filename == "syntyr-static-site.zip"
    names = page.evaluate("""async () => {
      const data = new TextDecoder().decode(await window.__lastSiteBlob.arrayBuffer());
      return ['index.html','about/index.html','syntyr.all.css'].every(name => data.includes(name));
    }""")
    assert names, "ZIP omitted one of the published page files"

    page.locator("#builder-import").set_input_files({
        "name": "syntyr-site.json", "mimeType": "application/json",
        "buffer": json.dumps(saved).encode(),
    })
    expect(page.locator("#builder-status")).to_contain_text("Site project opened")
    expect(page.locator("#builder-site-page-select option")).to_have_count(2)
    assert not errors, errors
    context.close()


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                verify(browser, "http://127.0.0.1:" + str(server.server_port))
                print("PASS site builder: multi-page editor and shared layouts")
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

if __name__ == "__main__":
    main()
