"""Cross-engine smoke test for opt-in native HTML presentation. Dev-only Playwright."""
from pathlib import Path
import re
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / "examples/native-elements.html").as_uri()
PALETTES = ("grid", "noir", "studio", "industrial", "terminal", "corporate", "minimal")


def rgb(value):
    if not value.startswith(("rgb(", "rgba(")):
        raise AssertionError(f"Unexpected computed color {value!r}")
    parts = re.findall(r"[0-9.]+", value)
    return tuple(float(p) for p in parts[:3])


def brightness(color):
    channels = [channel / 255 for channel in rgb(color)]
    linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
    return linear[0] * .2126 + linear[1] * .7152 + linear[2] * .0722


def contrast(a, b):
    high, low = sorted((brightness(a), brightness(b)), reverse=True)
    return (high + .05) / (low + .05)


def run():
    with sync_playwright() as p:
        for engine in ("chromium", "firefox", "webkit"):
            browser = getattr(p, engine).launch()
            for width in (320, 900):
                page = browser.new_page(viewport={"width": width, "height": 800})
                page.goto(URL)
                assert page.locator("search[aria-label='Search examples']").count() == 1
                assert page.locator("meter#native-meter").get_attribute("value") == "65"
                assert page.locator("figure figcaption").count() == 1
                for palette in PALETTES:
                    page.locator("body").evaluate("(e, theme) => e.setAttribute('data-syn-theme', theme)", palette)
                    foreground, background = page.locator("mark").first.evaluate(
                        "(e) => [getComputedStyle(e).color, getComputedStyle(e).backgroundColor]"
                    )
                    ratio = contrast(foreground, background)
                    assert ratio >= 4.5, (engine, width, palette, ratio, foreground, background)
                    nested_fg = page.locator("mark code").evaluate("(e) => getComputedStyle(e).color")
                    assert contrast(nested_fg, background) >= 4.5, (engine, width, palette, "nested code", nested_fg, background)
                for scheme in ("light", "dark"):
                    page.emulate_media(color_scheme=scheme)
                    page.locator("body").evaluate("(e) => e.setAttribute('data-syn-theme', 'auto')")
                    foreground, background = page.locator("mark").first.evaluate(
                        "(e) => [getComputedStyle(e).color, getComputedStyle(e).backgroundColor]"
                    )
                    assert contrast(foreground, background) >= 4.5, (engine, width, "auto", scheme)
                page.emulate_media(color_scheme="light")
                if width == 320:
                    overflow = page.evaluate(
                        "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
                    )
                    assert overflow <= 1, (engine, width, "unexpected page overflow", overflow)
                    pre = page.locator("pre")
                    assert pre.evaluate("(e) => e.scrollWidth > e.clientWidth"), (engine, width, "code must overflow its own box")
                    assert pre.evaluate("(e) => ['auto', 'scroll'].includes(getComputedStyle(e).overflowX)")
                    pre.focus()
                    assert pre.evaluate("(e) => document.activeElement === e"), (engine, width, "code region keyboard focus")
                    pre.press("ArrowRight")
                    page.wait_for_function("() => document.querySelector('pre').scrollLeft > 0", timeout=2000)
                    for size in ("200%", "400%"):
                        page.evaluate("(size) => document.documentElement.style.fontSize = size", size)
                        overflow = page.evaluate(
                            "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
                        )
                        assert overflow <= 1, (engine, width, size, "enlarged-font overflow", overflow)
                        for control in ("#design-file", "#design-color"):
                            element = page.locator(control)
                            bounds = element.bounding_box()
                            assert bounds is not None
                            assert bounds["width"] >= 0 and bounds["x"] + bounds["width"] <= width + 1, (
                                engine, size, control, "native control exceeded viewport", bounds)
                        table_region = page.get_by_role("region", name="Example data table")
                        table_region.focus()
                        assert table_region.evaluate("(el) => document.activeElement === el")
                        kbd = page.get_by_text("Control+Alt+Shift+ArrowRight", exact=True)
                        rect = kbd.bounding_box()
                        assert rect is not None and rect["width"] <= width - 2, (engine, size, "long kbd overflow", rect)
                    page.evaluate("() => document.documentElement.style.fontSize = ''")
                page.emulate_media(forced_colors="active")
                foreground, background = page.locator("mark").first.evaluate(
                    "(e) => [getComputedStyle(e).color, getComputedStyle(e).backgroundColor]"
                )
                assert foreground != background, (engine, "forced colors mark indistinguishable")
                page.emulate_media(forced_colors="none")
                original = page.locator("mark").first.evaluate("(e) => getComputedStyle(e).backgroundColor")
                page.locator("body").evaluate("(e) => e.classList.remove('syn-root')")
                unscoped = page.locator("mark").first.evaluate("(e) => getComputedStyle(e).backgroundColor")
                assert original != unscoped, (engine, width, "semantic styling leaked outside root")
                page.locator("body").evaluate("(e) => e.classList.add('syn-root')")
                if width == 900:
                    page.locator("#native-q").fill("status")
                    page.get_by_role("button", name="Search").click()
                    assert "q=status" in page.url
                page.close()
            browser.close()
            print("PASS", engine, "7 themes + auto, 320/900px, 200/400% fonts, forced colors, native GET, scope")


if __name__ == "__main__":
    run()
