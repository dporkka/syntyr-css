"""Optional real-engine smoke for native CSS tokens, contrast, and compositions."""
from pathlib import Path
import os
import re
import shutil
import sys
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
THEMES = ("studio", "grid", "noir", "industrial", "terminal", "corporate", "minimal", "graphite", "midnight", "dim", "obsidian", "amethyst")

def luminance(rgb):
    values = [float(c) / 255 for c in re.findall(r"[\d.]+", rgb)[:3]]
    assert len(values) == 3, f"unexpected computed CSS color {rgb!r}"
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
    return sum(v * w for v, w in zip(linear, (0.2126, 0.7152, 0.0722)))

def contrast(a, b):
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)

def computed(page, selector, property_name):
    return page.locator(selector).evaluate(
        "(element, key) => getComputedStyle(element).getPropertyValue(key).trim()",
        property_name
    )

def verify(browser_name, browser, css):
    page = browser.new_page(viewport={"width": 1100, "height": 850})
    page.emulate_media(reduced_motion="reduce")
    buttons = "".join(
        f'<section class="syn-root" data-syn-theme="{theme}" style="padding:1rem">'
        f'<button id="btn-{theme}" class="syn-button syn-button--primary">{theme}</button>'
        '</section>'
        for theme in THEMES
    )
    markup = f"""<style>{css}</style>
        <button id="outside" class="syn-button syn-button--primary">Host</button>
        {buttons}
        <main class="syn-root" data-syn-theme="studio">
          <article id="raised" class="syn-panel syn-panel--raised">Elevation</article>
          <div id="flow" class="syn-flow" style="--syn-flow-gap: 2rem">
            <div id="flow-first">First</div><div id="flow-second">Second</div>
          </div>
          <div id="inline-flow" class="syn-flow" style="--syn-flow-gap: 2rem"><span id="inline-one">First inline</span><span id="inline-two">Second inline</span></div>
          <h2 id="heading" class="syn-section-heading">Balanced section typography</h2>
          <section data-syn-theme="grid" data-syn-intensity="cinematic" id="nested">
            <div class="syn-panel syn-horizon" id="nested-horizon" style="height: 6rem">Nested horizon</div>
          </section>
        </main>"""
    page.set_content(markup)
    assert computed(page, "#outside", "display") != "inline-flex", "host styling leaked"
    assert computed(page, "#heading", "text-wrap") == "balance", "balanced heading missing"
    first = page.locator("#inline-one").bounding_box()
    second = page.locator("#inline-two").bounding_box()
    assert second["y"] >= first["y"] + first["height"] + 31, f"inline flow children overlap instead of stacking: {first}, {second}"
    assert computed(page, "#flow", "row-gap") == "32px", "flow gap not applied"
    assert computed(page, "#raised", "box-shadow") != "none", "panel elevation missing"

    for theme in THEMES:
        selector = f"#btn-{theme}"
        page.locator(selector).hover()
        bg = computed(page, selector, "background-color")
        fg = computed(page, selector, "color")
        assert contrast(fg, bg) >= 4.5, f"{browser_name} {theme}: hover contrast {contrast(fg, bg):.2f}"
        assert computed(page, selector, "border-top-color") == fg, f"{browser_name} {theme}: no visible border affordance"
    page.emulate_media(contrast="more", reduced_motion="reduce")
    # Firefox's media emulation requires a fresh document for style recalculation.
    page.set_content(markup)
    strong_border = computed(page, "#nested", "--syn-frame-strong")
    subtle_border = computed(page, "#nested", "--syn-border-subtle")
    assert subtle_border == strong_border, f"nested high contrast border not promoted {strong_border!r} vs {subtle_border!r}"
    assert computed(page, "#nested", "--syn-grid-alpha") == "0%", "cinematic effects not suppressed"
    assert computed(page, "#nested", "--syn-glow-alpha") == "0%", "cinematic glow not suppressed"
    assert computed(page, "#nested-horizon", "background-image") == "none", "horizon fade remains at higher contrast"
    page.close()
    print(f"PASS {browser_name}: twelve-theme hover contrast, scoped styles, flow, heading, shadows, nested contrast")

def main():
    css = (ROOT / "dist/syntyr.all.css").read_text(encoding="utf-8")
    engines = sys.argv[1:] or ["chromium"]
    with sync_playwright() as p:
        for name in engines:
            kwargs = {"headless": True}
            if name == "chromium":
                executable = (os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
                              or shutil.which("chromium")
                              or shutil.which("chromium-browser"))
                if executable:
                    kwargs.update(executable_path=executable, args=["--no-sandbox"])
            browser = getattr(p, name).launch(**kwargs)
            try:
                verify(name, browser, css)
            finally:
                browser.close()

if __name__ == "__main__":
    main()
