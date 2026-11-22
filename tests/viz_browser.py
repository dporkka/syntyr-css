"""Optional three-engine browser verification for the Syntyr Viz gallery.

Dev-only: uv run --with playwright python tests/viz_browser.py
"""
import argparse
import os
from pathlib import Path
import shutil
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / "examples/viz.html").as_uri()
THEMES = ("grid", "noir", "studio", "industrial", "terminal", "corporate", "minimal", "graphite", "midnight", "dim", "obsidian", "amethyst")


def check_browser(browser, engine):
    context = browser.new_context(
        viewport={"width": 1280, "height": 880},
        reduced_motion="reduce",
    )
    page = context.new_page()
    try:
        page.goto(URL)
        assert page.locator("script").count() == 0, (engine, "runtime JS added")
        assert page.locator(".viz-card").count() == len(THEMES)
        for theme in THEMES:
            card = page.locator(f'.viz-card[data-syn-theme="{theme}"]')
            values = card.evaluate("""(el) => {
              const css = getComputedStyle(el);
              return [css.getPropertyValue('--syn-chart-1').trim(),
                      css.getPropertyValue('--syn-accent').trim()];
            }""")
            assert values[0] and values[0] == values[1], (engine, theme, values)
            assert card.locator(".syn-viz-sparkline").count() == 1
            assert card.locator(".syn-viz-bars").count() == 1
            assert card.locator(".syn-viz-tracker > li").count() == 14
            assert card.locator(".syn-viz-heatmap > .syn-viz-cell").count() == 24
            assert card.locator("table tbody tr").count() == 6

        card = page.locator('.viz-card[data-syn-theme="grid"]')
        track = card.locator(".syn-viz-bar-track").first.bounding_box()
        fill = card.locator(".syn-viz-bar-fill").first.bounding_box()
        fraction = fill["width"] / track["width"]
        assert abs(fraction - .54) < .02, (engine, "bar width", fraction)

        colors = [
            card.locator(f'.syn-viz-cell[data-syn-level="{level}"]').first.evaluate(
                "(el) => getComputedStyle(el).backgroundColor")
            for level in range(5)
        ]
        assert len(set(colors)) == 5, (engine, "heatmap intensity collapsed", colors)

        page.screenshot(path=f"/tmp/syntyr-viz-desktop-{engine}.png", full_page=False)
        page.set_viewport_size({"width": 320, "height": 760})
        assert page.evaluate(
            "document.documentElement.scrollWidth - document.documentElement.clientWidth"
        ) <= 1, (engine, "mobile page overflow")
        assert card.locator(".syn-viz-sparkline").bounding_box()["width"] > 190

        details = card.locator("details")
        details.locator("summary").focus()
        page.keyboard.press("Enter")
        assert details.evaluate("(el) => el.open"), (engine, "keyboard-discoverable values")
        page.screenshot(path=f"/tmp/syntyr-viz-{engine}.png", full_page=False)
        print(f"PASS {engine}: 7 themes, SVG, bar width, heatmap, mobile and keyboard", flush=True)
    finally:
        context.close()

    context = browser.new_context(
        viewport={"width": 375, "height": 800},
        forced_colors="active",
    )
    page = context.new_page()
    try:
        page.goto(URL)
        degraded = page.locator('.viz-card[data-syn-theme="grid"] '
                                '.syn-viz-tracker [data-syn-state="degraded"]').first
        style = degraded.evaluate("(el) => getComputedStyle(el).borderTopStyle")
        assert style == "dashed", (engine, "forced-colors status distinction", style)
        print(f"PASS {engine}: forced-colors state distinction", flush=True)
    finally:
        context.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--browsers", nargs="+", choices=("chromium", "firefox", "webkit"),
                        default=("chromium", "firefox", "webkit"))
    args = parser.parse_args()
    failures = 0
    with sync_playwright() as p:
        for engine in args.browsers:
            try:
                options = {"headless": True}
                if engine == "chromium":
                    executable = (os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
                                  or shutil.which("chromium"))
                    if executable:
                        options.update(executable_path=executable, args=["--no-sandbox"])
                browser = getattr(p, engine).launch(**options)
            except Exception as exc:
                print(f"BLOCKED {engine}: {str(exc).splitlines()[0]}", flush=True)
                failures += 1
                continue
            try:
                check_browser(browser, engine)
            except Exception as exc:
                print(f"FAIL {engine}: {type(exc).__name__}: {exc}", flush=True)
                failures += 1
            finally:
                browser.close()
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
