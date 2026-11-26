"""Opt-in multi-page editor smoke test. Requires Python Playwright + Chromium.
Run: python3 tests/site_builder_browser.py
"""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from zipfile import ZipFile
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

    # Astra-style multi-page kits import into the same validated site project.
    expect(page.locator("#builder-apply-site-kit")).to_be_enabled(timeout=10000)
    page.locator("#builder-site-kit-select").select_option("saas")
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.locator("#builder-apply-site-kit").click()
    expect(page.locator("#builder-site-page-select option")).to_have_count(2)
    page.once("dialog", lambda dialog: dialog.accept())
    page.locator("#builder-apply-site-kit").click()
    expect(page.locator("#builder-site-page-select option")).to_have_count(4)
    expect(page.locator("#builder-site-header-brand")).to_have_value("Your SaaS product")
    expect(page.locator("#builder-site-header-link-href")).to_have_value("/pricing/")
    expect(preview.locator(".syn-stage h1")).to_have_text("Show the value of your software.")
    page.locator("#builder-site-page-select").select_option("pricing")
    expect(preview.locator(".syn-stage h1")).to_have_text("Make your pricing easy to understand.")
    with page.expect_download() as info:
        page.locator("#builder-export-json").click()
    assert info.value.suggested_filename == "syntyr-site.json"
    kit = json.loads(page.evaluate("async () => await window.__lastSiteBlob.text()"))
    assert [entry["slug"] for entry in kit["pages"]] == ["", "features", "pricing", "contact"]
    with page.expect_download() as info:
        page.locator("#builder-export-zip").click()
    assert info.value.suggested_filename == "syntyr-static-site.zip"
    names = page.evaluate("""async () => {
      const data = new TextDecoder().decode(await window.__lastSiteBlob.arrayBuffer());
      return ['index.html','features/index.html','pricing/index.html',
        'contact/index.html','syntyr.all.css'].every(name => data.includes(name));
    }""")
    assert names, "Website kit ZIP omitted required page files"
    # A valid ten-page import can reference more files than a single-page ZIP.
    saved["pages"] = page.evaluate("""async (base) => {
      const {createBlock} = await import('/docs/page-builder-model.mjs');
      const png = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WlJnE8AAAAASUVORK5CYII=';
      const pages = [];
      for (let i = 0; i < 10; i++) {
        const document = structuredClone(base);
        document.media = {};
        document.blocks = [];
        for (let j = 0; j < 12; j++) {
          const block = createBlock('section:image-gallery', 'gallery-' + j);
          // Unique suffixes make distinct content-addressed fixtures.
          const binary = atob(png) + String.fromCharCode(i * 12 + j);
          const bytes = Uint8Array.from(binary, c => c.charCodeAt(0));
          const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', bytes));
          const name = 'custom-' + Array.from(digest, n => n.toString(16).padStart(2, '0')).join('') + '.png';
          document.media[name] = 'data:image/png;base64,' + btoa(binary);
          block.props.src1 = 'assets/' + name;
          document.blocks.push(block);
        }
        pages.push({slug: i ? 'page-' + i : '', document});
      }
      return pages;
    }""", saved["pages"][0]["document"])
    # A forged content-addressed import must not replace the current project.
    tampered = json.loads(json.dumps(saved))
    media = tampered["pages"][0]["document"]["media"]
    name = next(iter(media))
    other = next(value for key, value in media.items() if key != name)
    media[name] = other
    page.locator("#builder-import").set_input_files({
        "name": "tampered-site.json",
        "mimeType": "application/json",
        "buffer": json.dumps(tampered).encode(),
    })
    expect(page.locator("#builder-status")).to_contain_text("image content hash mismatch")
    expect(page.locator("#builder-site-page-select option")).to_have_count(4)
    page.locator("#builder-import").set_input_files({
        "name": "large-site.json",
        "mimeType": "application/json",
        "buffer": json.dumps(saved).encode(),
    })
    expect(page.locator("#builder-site-page-select option")).to_have_count(10)
    with page.expect_download() as info:
        page.locator("#builder-export-zip").click()
        expect(page.locator("#builder-status")).to_contain_text("Static-site ZIP downloaded")
    with ZipFile(info.value.path()) as archive:
        names = archive.namelist()
        assert len(names) > 128
        assert "page-9/index.html" in names
        assert sum(name.startswith("assets/custom-") for name in names) == 120
        assert archive.testzip() is None
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
