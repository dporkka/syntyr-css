"""Optional browser smoke test for Syntyr's local-only visual page composer.

Run from repository root: python3 tests/page_builder_browser.py
"""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os
import json
import threading
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *_args):
        pass


def verify(browser, base_url, width):
    context = browser.new_context(viewport={"width": width, "height": 900}, accept_downloads=True)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.goto(base_url + "/docs/page-builder.html", wait_until="load")
    preview = page.frame_locator("#builder-preview")
    preview.locator(".syn-stage h1").wait_for()
    expect(preview.locator(".syn-stage h1")).to_have_text("Build your next website visually.")
    assert page.locator("#builder-outline > li").count() == 3

    page.locator('[data-block-type="quote"]').click()
    assert page.locator("#builder-outline > li").count() == 4
    page.locator("#builder-inspector [data-field='quote']").fill("Testimonial from browser smoke test")
    expect(preview.locator("blockquote p")).to_have_text("Testimonial from browser smoke test")

    page.locator("#builder-undo").click()
    expect(preview.locator("blockquote p")).not_to_have_text("Testimonial from browser smoke test")
    page.locator("#builder-redo").click()
    expect(preview.locator("blockquote p")).to_have_text("Testimonial from browser smoke test")
    page.locator('#builder-outline [data-index="3"] [data-action="up"]').click()
    assert page.locator('#builder-outline [data-index="2"] [data-action="select"]').get_attribute("aria-label").startswith("Edit Testimonial")
    page.locator('#builder-outline [data-index="2"] [data-action="down"]').click()

    page.locator("#builder-theme").select_option("grid")
    expect(preview.locator("body")).to_have_attribute("data-syn-theme", "grid")
    for preset, pixels in (("desktop", 1200), ("tablet", 760), ("mobile", 390)):
        page.locator("#builder-viewport").select_option(preset)
        expect(page.locator("#builder-viewport-frame")).to_have_class(
            "builder-viewport builder-viewport--" + preset
        )
        assert preview.locator("body").evaluate("() => innerWidth") == pixels

    page.locator('[data-block-type="faq"]').click()
    expect(page.locator("#builder-outline > li")).to_have_count(5)
    preview.locator("details summary").first.click()
    expect(preview.locator("details").first).to_have_attribute("open", "")
    expect(preview.locator("details p").first).to_be_visible()
    page.locator("#builder-undo").click()
    expect(page.locator("#builder-outline > li")).to_have_count(4)
    page.locator("#builder-redo").click()
    expect(page.locator("#builder-outline > li")).to_have_count(5)
    page.locator('#builder-outline [data-index="4"] [data-action="up"]').click()
    expect(page.locator('#builder-outline [data-index="3"] [data-action="up"]')).to_be_focused()

    # Some remote headless browsers cancel file downloads at the OS boundary.
    # Capture the actual Blob payload without mocking the builder's export code.
    page.evaluate("""() => {
        const original = URL.createObjectURL.bind(URL);
        URL.createObjectURL = (blob) => {
            window.__lastBuilderBlob = blob;
            return original(blob);
        };
    }""")
    with page.expect_download() as download_info:
        page.locator("#builder-export-html").click()
    assert download_info.value.suggested_filename == "index.html"
    html = page.evaluate("async () => await window.__lastBuilderBlob.text()")
    assert 'href="syntyr.all.css"' in html
    assert "Testimonial from browser smoke test" in html
    assert "<script" not in html

    with page.expect_download() as download_info:
        page.locator("#builder-export-json").click()
    assert download_info.value.suggested_filename == "syntyr-page.json"
    data = json.loads(page.evaluate("async () => await window.__lastBuilderBlob.text()"))
    assert data["schema"] == "syntyr.page.v1"
    assert data["theme"] == "grid"
    assert data["blocks"][-1]["type"] == "quote"

    project_bytes = json.dumps(data).encode()
    page.locator("#builder-import").set_input_files({
        "name": "page.json", "mimeType": "application/json", "buffer": project_bytes,
    })
    expect(page.locator("#builder-status")).to_contain_text("Project opened.")
    expect(page.locator("#builder-outline > li")).to_have_count(5)
    page.locator("#builder-import").set_input_files({
        "name": "bad.json", "mimeType": "application/json", "buffer": b'{"schema":"invalid"}',
    })
    expect(page.locator("#builder-status")).to_contain_text("Cannot open project")
    expect(page.locator("#builder-outline > li")).to_have_count(5)

    invalid = json.loads(json.dumps(data))
    invalid["blocks"][0]["type"] = ["hero"]
    page.locator("#builder-import").set_input_files({
        "name": "invalid-type.json", "mimeType": "application/json",
        "buffer": json.dumps(invalid).encode(),
    })
    expect(page.locator("#builder-status")).to_contain_text("Cannot open project")
    expect(page.locator("#builder-outline > li")).to_have_count(5)

    # A gallery-backed block uses the generated manifest and editable strings.
    gallery_count = len(json.loads((ROOT / "metadata/component-gallery.v1.json").read_text())["examples"])
    expect(page.locator("#builder-gallery-count")).to_have_text(f"{gallery_count} gallery examples.")
    page.locator("#builder-gallery-search").fill("buttons")
    assert page.locator("#builder-gallery-palette [data-block-type]").count() == 1
    page.locator('[data-block-type="gallery:catalog-buttons-title"]').click()
    assert page.locator("#builder-outline > li").count() == 6
    page.locator('#builder-inspector [data-field="text1"]').fill("Custom gallery action")
    assert preview.locator('[data-syntyr-block-id] .syn-button--primary').last.inner_text() == "Custom gallery action"
    with page.expect_download() as download_info:
        page.locator("#builder-export-html").click()
    assert download_info.value.suggested_filename == "index.html"
    html = page.evaluate("async () => await window.__lastBuilderBlob.text()")
    assert "Custom gallery action" in html
    assert 'href="syntyr.all.css"' in html
    assert "<script" not in html

    with page.expect_download() as download_info:
        page.locator("#builder-export-json").click()
    assert download_info.value.suggested_filename == "syntyr-page.json"
    gallery_project = json.loads(page.evaluate("async () => await window.__lastBuilderBlob.text()"))
    verify_manifest_import_order(browser, base_url, data, gallery_project)

    assert page.locator("body").evaluate("e => e.scrollWidth <= innerWidth + 1")
    assert not errors, errors
    context.close()


def verify_manifest_import_order(browser, base_url, native_project, gallery_project):
    """Native imports must not depend on fetching optional gallery metadata."""
    native_context = browser.new_context()
    native_context.add_init_script("""(() => {
        const original = window.fetch.bind(window);
        window.fetch = (url, options) => String(url).includes("component-gallery.v1.json")
            ? new Promise(() => {}) : original(url, options);
    })()""")
    try:
        native_page = native_context.new_page()
        native_page.goto(base_url + "/docs/page-builder.html", wait_until="load")
        native_page.locator("#builder-import").set_input_files({
            "name": "native-project.json", "mimeType": "application/json",
            "buffer": json.dumps(native_project).encode()
        })
        expect(native_page.locator("#builder-status")).to_contain_text("Project opened.", timeout=2000)
        expect(native_page.locator("#builder-outline > li")).to_have_count(len(native_project["blocks"]))
    finally:
        native_context.close()

    gallery_context = browser.new_context()
    gallery_context.add_init_script("""(() => {
        const original = window.fetch.bind(window);
        window.fetch = (url, options) => String(url).includes("component-gallery.v1.json")
            ? new Promise(resolve => setTimeout(resolve, 750)).then(() => original(url, options))
            : original(url, options);
    })()""")
    try:
        gallery_page = gallery_context.new_page()
        gallery_page.goto(base_url + "/docs/page-builder.html", wait_until="load")
        gallery_page.locator("#builder-import").set_input_files({
            "name": "gallery-project.json", "mimeType": "application/json",
            "buffer": json.dumps(gallery_project).encode()
        })
        expect(gallery_page.locator("#builder-status")).to_contain_text("Project opened.", timeout=6000)
        expect(gallery_page.locator("#builder-outline > li")).to_have_count(len(gallery_project["blocks"]))
    finally:
        gallery_context.close()

    # A slow gallery import must never overwrite a newer native-only import.
    overlap_context = browser.new_context()
    overlap_context.add_init_script("""(() => {
        const original = window.fetch.bind(window);
        window.fetch = (url, options) => String(url).includes("component-gallery.v1.json")
            ? new Promise(resolve => setTimeout(resolve, 1400)).then(() => original(url, options))
            : original(url, options);
    })()""")
    try:
        overlap = overlap_context.new_page()
        overlap.goto(base_url + "/docs/page-builder.html", wait_until="load")
        overlap.locator("#builder-import").set_input_files({
            "name": "older-gallery.json", "mimeType": "application/json",
            "buffer": json.dumps(gallery_project).encode()
        })
        overlap.wait_for_timeout(150)
        overlap.locator("#builder-import").set_input_files({
            "name": "newer-native.json", "mimeType": "application/json",
            "buffer": json.dumps(native_project).encode()
        })
        expect(overlap.locator("#builder-status")).to_contain_text("Project opened.", timeout=2000)
        overlap.wait_for_timeout(1650)
        expect(overlap.locator("#builder-page-title")).to_have_value(native_project["title"])
        expect(overlap.locator("#builder-outline > li")).to_have_count(len(native_project["blocks"]))
    finally:
        overlap_context.close()


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, executable_path=os.environ.get("SYNTYR_CHROMIUM_EXECUTABLE"))
            try:
                for width in (390, 1280):
                    verify(browser, "http://127.0.0.1:" + str(server.server_port), width)
                    print("PASS visual builder chromium", width)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
