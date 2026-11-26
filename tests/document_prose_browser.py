"""Rendered generated-content fixture; optional developer Playwright install."""
import argparse
import os
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def check(browser, engine):
    page = browser.new_page(viewport={"width": 320, "height": 800}, java_script_enabled=False)
    page.goto((ROOT / "examples/document-starter.html").as_uri())
    prose = page.locator("#prose")
    pre = prose.locator("pre.chroma")
    style = lambda selector, prop: page.locator(selector).evaluate(
        "(el, prop) => getComputedStyle(el).getPropertyValue(prop)", prop)
    assert style("#heading", "font-size") != style("#layout", "font-size"), engine
    assert style(".cms-quote", "border-inline-start-width") == "2px", engine
    assert style(".cms-table", "border-collapse") == "collapse", engine
    assert style(".cms-table td", "overflow-wrap") == "anywhere", engine
    assert style("pre.chroma", "overflow-x") == "auto", engine
    assert style("pre.chroma", "border-top-width") == "1px", engine
    assert style("#embedded-pre", "border-top-width") == "0px", engine
    assert style("#host-pre", "border-top-width") == "0px", engine
    page.locator(".keyword").evaluate("el => el.style.color = 'rgb(24, 89, 184)'")
    assert style(".keyword", "color") == "rgb(24, 89, 184)", engine
    # A renderer-owned class or text color is not a reason to suppress prose,
    # and a syntax highlighter remains free to provide its own token colors.
    page.locator(".keyword").evaluate("el => el.style.removeProperty('color')")
    assert pre.evaluate("el => el.scrollWidth > el.clientWidth"), engine
    pre.focus()
    assert pre.evaluate("el => document.activeElement === el"), engine
    pre.press("ArrowRight")
    # Poll through the driver: wait_for_function's in-page timer may be
    # unavailable in a scripting-disabled document.
    deadline = time.monotonic() + 2
    while pre.evaluate("el => el.scrollLeft") == 0 and time.monotonic() < deadline:
        time.sleep(.05)
    assert pre.evaluate("el => el.scrollLeft > 0"), (engine, "keyboard scrolling")
    for palette in ("studio", "grid", "noir", "industrial", "terminal", "corporate", "minimal"):
        page.locator("main").evaluate("(el, theme) => el.dataset.synTheme = theme", palette)
        for width in (320, 390, 1280):
            page.set_viewport_size({"width": width, "height": 800})
            for size in ("100%", "200%", "400%"):
                page.evaluate("(size) => document.documentElement.style.fontSize = size", size)
                assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1"), (engine, palette, width, size)
                assert prose.locator("img").evaluate("el => el.width <= el.parentElement.clientWidth + 1"), (engine, palette, width, size)
    page.evaluate("document.documentElement.style.fontSize = ''")
    page.emulate_media(media="print")
    assert style("pre.chroma", "white-space") == "pre-wrap", engine
    assert style("pre.chroma", "overflow-x") == "visible", engine
    assert style("#embedded-pre", "white-space") == "pre", engine
    page.emulate_media(media="screen", forced_colors="active")
    assert pre.is_visible()
    page.close()
    print(f"PASS {engine}: generated prose, 7 palettes, widths 320/390/1280, 100/200/400% text, print, scope")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--browsers", nargs="+", default=["chromium", "firefox", "webkit"])
    args = parser.parse_args()
    with sync_playwright() as p:
        for engine in args.browsers:
            executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE") if engine == "chromium" else None
            browser = getattr(p, engine).launch(**({"executable_path": executable} if executable else {}))
            try:
                check(browser, engine)
            finally:
                browser.close()
