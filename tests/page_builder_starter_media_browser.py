"""Optional Chromium E2E: starter -> local photo -> portable project and scriptless site."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import io
import json
import os
import threading
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
# Valid, original 1x1 raster PNG made from Pillow.
from base64 import b64decode
PIXEL=b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WlJnE8AAAAASUVORK5CYII=")

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(ROOT),**kwargs)
    def log_message(self,*args):
        pass

def main():
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,executable_path=os.environ.get("SYNTYR_CHROMIUM_EXECUTABLE"),
                                        args=["--no-sandbox"])
            try:
                for width in (390,1280):
                    context=browser.new_context(viewport={"width":width,"height":900},accept_downloads=True)
                    page=context.new_page()
                    errors=[]
                    page.on("pageerror",lambda error: errors.append(str(error)))
                    page.goto(f"http://127.0.0.1:{server.server_port}/docs/page-builder.html",wait_until="load")
                    expect(page.locator("#builder-section-count")).to_have_text("91 of 91 copy-owned sections.")
                    page.locator("#builder-starter").select_option("portfolio")
                    page.once("dialog",lambda dialog: dialog.accept())
                    page.locator("#builder-apply-starter").click()
                    expect(page.locator("#builder-outline > li")).to_have_count(6)
                    expect(page.locator("#builder-page-title")).to_have_value("Creative portfolio | Example")
                    page.locator('#builder-outline [data-index="1"] [data-action="select"]').click()
                    page.locator('#builder-inspector input[type="file"][data-field="src1"]').set_input_files({
                        "name":"my-photo.png","mimeType":"image/png","buffer":PIXEL
                    })
                    expect(page.locator("#builder-status")).to_contain_text("bundled",timeout=12000)
                    page.locator('#builder-inspector [data-field="alt1"]').fill("A custom one-pixel test image")
                    preview=page.frame_locator("#builder-preview")
                    expect(preview.locator('img[alt="A custom one-pixel test image"]')).to_have_count(1)
                    image=preview.locator('img[alt="A custom one-pixel test image"]')
                    expect(image).to_have_js_property("complete",True)
                    assert image.evaluate("(img) => img.naturalWidth") == 1

                    with page.expect_download() as saved_project:
                        page.locator("#builder-export-json").click()
                    with TemporaryDirectory() as dirname:
                        project_file=Path(dirname)/"syntyr-page.json"
                        saved_project.value.save_as(project_file)
                        project=json.loads(project_file.read_text())
                        assert len(project["media"])==1
                        media_name=next(iter(project["media"]))
                        assert media_name.startswith("custom-") and media_name.endswith(".png")
                        assert project["blocks"][1]["props"]["src1"]=="assets/"+media_name
                        assert project["blocks"][1]["props"]["href1"]=="assets/"+media_name
                        with page.expect_download() as static_zip:
                            page.locator("#builder-export-zip").click()
                        zip_path=Path(dirname)/"static.zip"
                        static_zip.value.save_as(zip_path)
                        with ZipFile(zip_path) as archive:
                            assert archive.testzip() is None
                            assert archive.read("assets/"+media_name)==PIXEL
                            assert "assets/gallery-horizon.svg" not in archive.namelist()
                            html=archive.read("index.html").decode()
                            assert 'src="assets/'+media_name+'"' in html
                            assert 'href="assets/'+media_name+'"' in html
                            assert "A custom one-pixel test image" in html
                            assert "<script" not in html
                        page.locator("#builder-starter").select_option("saas")
                        page.once("dialog",lambda dialog: dialog.accept())
                        page.locator("#builder-apply-starter").click()
                        expect(page.locator("#builder-page-title")).to_have_value("SaaS landing page | Example")
                        # Reopen portfolio project with its own embedded images.
                        page.locator("#builder-import").set_input_files(str(project_file))
                        expect(page.locator("#builder-page-title")).to_have_value("Creative portfolio | Example")
                        page.locator('#builder-outline [data-index="1"] [data-action="select"]').click()
                        expect(preview.locator('img[alt="A custom one-pixel test image"]')).to_have_count(1)
                    assert not errors,errors
                    context.close()
                    print("PASS starter/media/browser",width)
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()

if __name__=="__main__":
    main()
