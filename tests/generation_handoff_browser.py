"""Real generator JSON -> local visual builder -> safe edited HTML export."""
import json
import os
from pathlib import Path
import subprocess
import sys
from http.server import ThreadingHTTPServer
from threading import Thread
from playwright.sync_api import sync_playwright, expect
from page_builder_browser import Handler

ROOT = Path(__file__).resolve().parents[1]


def main():
    request = {"release": "0.3.0-alpha.5", "title": "Generated CRM",
               "theme": "noir", "requirements": ["pipeline", "metrics"]}
    result = json.loads(subprocess.check_output(
        [sys.executable, "scripts/generate_ui.py"], cwd=ROOT,
        input=json.dumps(request), text=True, timeout=30))
    assert result["status"] == "generated"
    result["output"]["html"] = "<script>throw Error('untrusted output')</script>"
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get("SYNTYR_CHROMIUM_EXECUTABLE"))
            for width in (390, 1280):
                context = browser.new_context(viewport={"width": width, "height": 900})
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.goto(f"http://127.0.0.1:{server.server_port}/docs/page-builder.html")
                def upload(value):
                    page.locator("#builder-import").set_input_files({
                        "name": "generated.json", "mimeType": "application/json",
                        "buffer": json.dumps(value).encode()})
                upload(result)
                expect(page.locator("#builder-status")).to_contain_text("Generated project opened")
                expect(page.locator("#builder-page-title")).to_have_value("Generated CRM")
                expect(page.locator("#builder-outline > li")).to_have_count(2)
                preview = page.frame_locator("#builder-preview")
                expect(preview.locator("body")).to_have_attribute("data-syn-theme", "noir")
                assert preview.locator("script").count() == 0
                upload({**result, "status": "blocked"})
                expect(page.locator("#builder-status")).to_contain_text("Cannot open project")
                expect(page.locator("#builder-outline > li")).to_have_count(2)
                page.locator("#builder-page-title").fill("Edited CRM")
                page.evaluate("""() => {
                    const original = URL.createObjectURL.bind(URL);
                    URL.createObjectURL = blob => {
                        window.__handoffBlob = blob;
                        return original(blob);
                    };
                }""")
                with page.expect_download():
                    page.locator("#builder-export-html").click()
                html = page.evaluate("async () => await window.__handoffBlob.text()")
                assert "<title>Edited CRM</title>" in html
                assert "<script" not in html
                assert not errors, errors
                context.close()
                print("PASS generated project handoff", width)
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
