"""Optional browser regression for use-case filters, live visual previews and insert/export."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zipfile import ZipFile
from tempfile import TemporaryDirectory
import os
import threading

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *_args):
        pass


def verify(page, width, port):
    page.goto(f"http://127.0.0.1:{port}/docs/page-builder.html")
    expect(page.locator("#builder-section-count")).to_have_text("102 of 102 copy-owned sections.")
    expect(page.locator("#builder-section-palette .builder-section-card")).to_have_count(102)
    assert page.locator(".builder-section-thumbnail span").count() == 102 * 4
    page.locator("#builder-section-use-case").select_option("publishing")
    expect(page.locator("#builder-section-count")).not_to_have_text("102 of 102 copy-owned sections.")
    expect(page.locator("[data-section-preview='section:article-toc']")).to_be_visible()

    # Preview is the actual canonical block, not the thumbnail sketch.
    preview_button = page.locator("[data-section-preview='section:article-toc']")
    preview_button.click()
    dialog = page.locator("#builder-section-preview-dialog")
    expect(dialog).to_be_visible()
    iframe = page.frame_locator("#builder-section-preview-frame")
    expect(iframe.locator("h2")).to_contain_text("A practical way to write clearer product pages")
    assert iframe.locator("script").count() == 0
    assert "allow-scripts" not in page.locator("#builder-section-preview-frame").get_attribute("sandbox")
    iframe.locator('a[href="#section-picker-preview--syn-layout-article-practices"]').click()
    expect(dialog).to_be_visible()
    page.keyboard.press("Escape")
    expect(dialog).not_to_be_visible()
    expect(preview_button).to_be_focused()

    # A single Add click inserts; a repeated addition respects the chosen insertion point.
    page.locator("[data-block-type='section:article-toc']").click()
    expect(page.locator("#builder-outline > li")).to_have_count(4)
    page.locator("#builder-insert-after").check()
    page.locator("#builder-section-use-case").select_option("landing")
    page.locator("[data-section-preview='section:hero-product']").click()
    expect(dialog).to_be_visible()
    page.locator("#builder-section-preview-add").click()
    expect(dialog).not_to_be_visible()
    expect(page.locator("#builder-outline > li")).to_have_count(5)
    expect(page.locator('#builder-outline > li[data-index="3"]')).to_contain_text("Article with contents sidebar")
    expect(page.locator('#builder-outline > li[data-index="4"]')).to_contain_text("Product launch hero")

    # Changing use case resets a stale category and keeps all-category browsing available.
    page.locator("#builder-section-category").select_option("Portfolio")
    page.locator("#builder-section-use-case").select_option("commerce")
    expect(page.locator("#builder-section-category")).to_have_value("all")
    assert page.locator("[data-block-type='section:product-collection']").count() == 1

    preview = page.frame_locator("#builder-preview")
    expect(preview.locator("section[data-syntyr-block-id]")).to_have_count(5)
    if width == 390:
        assert page.locator("body").evaluate("(node) => node.scrollWidth <= innerWidth + 1")

    with page.expect_download() as download_info:
        page.locator("#builder-export-zip").click()
    with TemporaryDirectory() as temp:
        dest = Path(temp) / "site.zip"
        download_info.value.save_as(dest)
        with ZipFile(dest) as archive:
            html = archive.read("index.html").decode()
            assert "A practical way to write clearer product pages" in html
            assert "Understand your product." in html
            assert "page-builder-section-picker" not in html
            assert "<script" not in html
            assert 'href="syntyr.all.css"' in html


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True, executable_path=os.environ.get("SYNTYR_CHROMIUM_EXECUTABLE"))
            try:
                for width in (390, 1280):
                    context = browser.new_context(viewport={"width": width, "height": 900},
                                                  accept_downloads=True)
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda exc: errors.append(str(exc)))
                    verify(page, width, server.server_port)
                    assert errors == [], errors
                    context.close()
                    print("PASS visual picker", width)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
