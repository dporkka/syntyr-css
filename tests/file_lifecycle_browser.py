"""Maintainer-only file-lifecycle example zoom and semantics check.

Run with uv run --offline --with playwright python tests/file_lifecycle_browser.py.
This browser tool is not shipped as a consumer runtime.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / "examples/file-lifecycle.html").as_uri()


def run():
    results = 0
    unavailable = []
    with sync_playwright() as playwright:
        for name in ("chromium", "firefox", "webkit"):
            try:
                browser = getattr(playwright, name).launch(headless=True)
            except Exception as exc:
                unavailable.append((name, str(exc).splitlines()[0]))
                continue
            try:
                for width, font in ((1280, 16), (390, 16), (320, 32), (320, 64)):
                    context = browser.new_context(
                        viewport={"width": width, "height": 800},
                        java_script_enabled=False,
                    )
                    page = context.new_page()
                    page.goto(URL)
                    page.evaluate("(font) => document.documentElement.style.fontSize = font + 'px'", font)
                    queue = page.get_by_role("list").filter(has=page.locator(".syn-file-item"))
                    assert queue.count() == 1, (name, width, font, "list role")
                    assert queue.locator("li").count() == 4
                    assert page.get_by_label("Choose attachments").get_attribute("type") == "file"
                    assert page.locator("progress").count() == 2
                    viewport = page.evaluate(
                        "({client: document.documentElement.clientWidth, "
                        "scroll: document.documentElement.scrollWidth})"
                    )
                    assert viewport["scroll"] <= viewport["client"] + 1, (
                        name, width, font, "horizontal overflow", viewport
                    )
                    results += 1
                    print(f"PASS {name} {width}px root={font}px: list, native file, no-JS, no overflow", flush=True)
                    context.close()
            finally:
                browser.close()
    for name, error in unavailable:
        print(f"BLOCKED {name}: {error}")
    if not results:
        raise SystemExit("No browser was available")
    print(f"RESULT {results} passed; {len(unavailable)} unavailable browser engines")


if __name__ == "__main__":
    run()
