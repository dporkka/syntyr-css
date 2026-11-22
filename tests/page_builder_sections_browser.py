"""Optional end-to-end: canonical sections -> reorder -> self-contained static ZIP."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import os
import threading

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *_args):
        pass


def run():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                executable_path=os.environ.get("SYNTYR_CHROMIUM_EXECUTABLE"),
            )
            try:
                for width in (390, 1280):
                    context = browser.new_context(viewport={"width": width, "height": 900},
                                                  accept_downloads=True)
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda err: errors.append(str(err)))
                    page.goto(f"http://127.0.0.1:{server.server_port}/docs/page-builder.html")
                    expect(page.locator("#builder-section-count")).to_have_text(
                        "85 of 85 copy-owned sections.")
                    page.locator("#builder-section-search").fill("image gallery")
                    expect(page.locator("#builder-section-count")).to_have_text(
                        "2 of 85 copy-owned sections.")
                    page.locator("#builder-section-category").select_option("Portfolio")
                    page.locator('[data-block-type="section:image-gallery"]').click()
                    expect(page.locator("#builder-outline > li")).to_have_count(4)
                    preview = page.frame_locator("#builder-preview")
                    gallery = preview.locator('section[data-syntyr-block-id] .syn-image-gallery')
                    expect(gallery).to_be_visible()
                    expect(gallery.locator("img")).to_have_count(4)
                    expect(gallery.locator("img").first).to_have_js_property("complete", True)
                    assert gallery.locator("img").first.evaluate("(img) => img.naturalWidth") > 0

                    # Duplicate the image gallery, then move the copy to the beginning.
                    page.locator('#builder-outline [data-index="3"] [data-action="duplicate"]').click()
                    expect(page.locator("#builder-outline > li")).to_have_count(5)
                    page.locator('#builder-outline [data-index="4"] [data-action="first"]').click()
                    expect(page.locator("#builder-outline > li")).to_have_count(5)
                    assert "Image gallery" in page.locator('#builder-outline [data-index="0"]').inner_text() or \
                        "Responsive image gallery" in page.locator('#builder-outline [data-index="0"]').inner_text()

                    # The site's output contains all local assets, CSS, MIT license,
                    # and no framework or editor JavaScript.
                    with page.expect_download() as download_info:
                        page.locator("#builder-export-zip").click()
                    download = download_info.value
                    assert download.suggested_filename == "syntyr-static-site.zip"
                    with TemporaryDirectory() as temporary:
                        destination = Path(temporary) / "site.zip"
                        download.save_as(destination)
                        with ZipFile(destination) as archive:
                            names = set(archive.namelist())
                            assert {"index.html", "syntyr.all.css", "LICENSE",
                                    "README.txt", "assets/gallery-horizon.svg",
                                    "assets/gallery-botanical.svg",
                                    "assets/gallery-architecture.svg",
                                    "assets/gallery-signal.svg"} <= names
                            assert archive.testzip() is None
                            html = archive.read("index.html").decode()
                            assert html.count("syn-image-gallery") >= 2
                            assert 'src="assets/gallery-horizon.svg"' in html
                            assert "<script" not in html.lower()
                            assert "page-builder.js" not in html
                            assert 'href="syntyr.all.css"' in html
                    assert not errors, errors
                    context.close()
                    print("PASS static website composer", width)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    run()
