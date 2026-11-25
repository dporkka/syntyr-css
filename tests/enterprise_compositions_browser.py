"""Optional developer-only browser check for Syntyr enterprise recipes.

Run: uv run --offline --with playwright python tests/enterprise_compositions_browser.py
No consumer runtime dependencies, scripts or remote resources are loaded.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / "examples/enterprise-compositions.html").as_uri()


def check(browser, engine: str, width: int, font_px: int, height: int = 780) -> None:
    context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce")
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.goto(URL, wait_until="load")
    page.evaluate("(px) => document.documentElement.style.fontSize = px + 'px'", font_px)
    assert page.locator("script").count() == 0
    assert page.locator(".syn-view-switcher").evaluate(
        "e => getComputedStyle(e).display"
    ) in ("inline-flex", "flex")
    assert page.locator(".syn-evidence-card").count() == 2
    preview = page.locator(".syn-evidence-media").first
    clipped = preview.evaluate("e => ({vertical:e.scrollHeight-e.clientHeight, horizontal:e.scrollWidth-e.clientWidth})")
    assert clipped["vertical"] <= 1 and clipped["horizontal"] <= 1, (engine, width, font_px, "preview clipped", clipped)
    sheet = page.locator("#record-preview")
    assert not sheet.is_visible(), (engine, width, "popover not hidden initially")
    assert sheet.evaluate("e => getComputedStyle(e).display") == "none"
    assert page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth") <= 1, (engine, width, "page overflow")
    page.get_by_role("button", name="Open details").click()
    assert sheet.is_visible(), (engine, width, "native popover did not open")
    assert sheet.evaluate("e => e.matches(':popover-open')"), (engine, width)
    rect = sheet.bounding_box()
    assert rect is not None
    assert rect["x"] >= -1 and rect["x"] + rect["width"] <= width + 1, (engine, width, rect)
    assert sheet.evaluate("e => getComputedStyle(e).gridTemplateRows") != "none"
    # At extreme text zoom, the complete sheet (including footer actions) must
    # remain scroll-reachable even if the header alone consumes most of the height.
    if width == 320 and font_px == 64:
        assert sheet.evaluate("e => getComputedStyle(e).overflowY") in ("auto", "scroll"), (
            engine, "sheet lacks a user-scrollable fallback"
        )
        page.mouse.move(rect["x"] + min(16, rect["width"] / 2), rect["y"] + 12)
        page.mouse.wheel(0, 5000)
        page.wait_for_function("document.querySelector('#record-preview').scrollTop > 0")
        # The footer may itself exceed a short viewport at 400% text zoom.
        # Each individual control, not the entire footer, must be scroll-reachable.
        for control in (sheet.get_by_role("link", name="Return to collection"),
                        sheet.get_by_role("button", name="Done")):
            control.scroll_into_view_if_needed()
            bounds = control.bounding_box()
            assert bounds and bounds["height"] > 0
            assert bounds["y"] >= -1 and bounds["y"] + bounds["height"] <= height + 1, (
                engine, "footer action unreachable", bounds
            )
        sheet.evaluate("e => { e.scrollTop = 0; }")
        body = sheet.locator(".syn-sheet-body")
        # Regression: a nonzero, keyboard-scrollable body must be reachable
        # even after the header/footer consume the available block space.
        assert body.evaluate("e => e.clientHeight") >= 100, (
            engine, "sheet body collapsed at extreme zoom"
        )
        assert body.get_attribute("tabindex") == "0", (engine, "body not keyboard focusable")
        body.focus()
        assert body.evaluate("e => document.activeElement === e")
        assert body.evaluate("e => e.scrollHeight > e.clientHeight"), (
            engine, "expected overflow content at extreme zoom"
        )
        page.keyboard.press("PageDown")
        page.wait_for_function(
            "document.querySelector('#record-preview .syn-sheet-body').scrollTop > 0"
        )
    assert not errors, (engine, width, errors)
    page.keyboard.press("Escape")
    assert not sheet.is_visible(), (engine, width, "escape did not dismiss")

    # Exercise the other supported host element with test-only code; Syntyr
    # does not ship the script or claim to implement native modal behavior.
    page.evaluate("""() => {
        const dialog = document.createElement('dialog');
        dialog.id = 'modal-record-test';
        dialog.className = 'syn-sheet';
        dialog.setAttribute('aria-label', 'Illustrative modal');
        dialog.innerHTML = '<header class="syn-sheet-header">Review</header><div class="syn-sheet-body">Record</div><footer class="syn-sheet-footer">Close</footer>';
        document.body.appendChild(dialog);
    }""")
    modal = page.locator('#modal-record-test')
    assert not modal.is_visible()
    page.evaluate("document.querySelector('#modal-record-test').showModal()")
    assert modal.is_visible()
    assert modal.evaluate("e => getComputedStyle(e).display") == 'grid'
    page.keyboard.press("Escape")
    assert not modal.is_visible()
    assert not errors, (engine, width, errors)
    context.close()
    print(f"PASS {engine}: {width}x{height}px, {font_px}px root, native popover open/escape, no overflow")


def main():
    passed = 0
    blocked = []
    with sync_playwright() as p:
        for engine in ("chromium", "firefox", "webkit"):
            try:
                browser = getattr(p, engine).launch(headless=True)
            except Exception as error:
                blocked.append((engine, str(error).splitlines()[0]))
                continue
            try:
                for width, font_px, height in ((1280, 16, 780), (390, 16, 780), (320, 32, 780), (320, 64, 780), (320, 64, 420)):
                    check(browser, engine, width, font_px, height)
                    passed += 1
            finally:
                browser.close()
    print(f"RESULT {passed} passed, {len(blocked)} browser engines blocked")
    for engine, reason in blocked:
        print(f"BLOCKED {engine}: {reason}")
    if passed == 0:
        raise SystemExit("No browser engine verified")


if __name__ == "__main__":
    main()
