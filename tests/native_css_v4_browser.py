"""Browser-level opt-in layout, state, and OKLCH validation (maintainer-only).

Usage: <playwright-python> tests/native_css_v4_browser.py [chromium firefox webkit]
"""
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
THEMES = ("studio", "grid", "noir", "industrial", "terminal", "corporate", "minimal")


def css_value(page, selector, name):
    return page.locator(selector).evaluate(
        "(node, name) => getComputedStyle(node).getPropertyValue(name).trim()", name
    )


def assert_same_row(page, a, b, expected):
    first = page.locator(a).bounding_box()
    second = page.locator(b).bounding_box()
    same_row = abs(first["y"] - second["y"]) < 4
    assert same_row == expected, f"{a} / {b}: same_row={same_row}, expected {expected}"


def canvas_color(page, selector, name):
    return page.locator(selector).evaluate(
        """(node, name) => {
          const css = getComputedStyle(node).getPropertyValue(name);
          const canvas = document.createElement('canvas');
          canvas.width = 1; canvas.height = 1;
          const context = canvas.getContext('2d', {willReadFrequently: true});
          context.fillStyle = css;
          context.fillRect(0, 0, 1, 1);
          return [...context.getImageData(0, 0, 1, 1).data].slice(0, 3);
        }""", name
    )


def contrast(a, b):
    def lum(color):
        vals = [v / 255 for v in color]
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
                  for v in vals]
        return sum(v * k for v, k in zip(linear, (0.2126, 0.7152, 0.0722)))
    high, low = sorted((lum(a), lum(b)), reverse=True)
    return (high + .05) / (low + .05)


def verify(browser, engine, css):
    page = browser.new_page(viewport={"width": 1200, "height": 900})
    page.emulate_media(reduced_motion="reduce")
    markup = f"""<style>{css}</style>
      <div class="syn-grid" id="outside"><div>host</div></div>
      <section class="syn-root" data-syn-theme="studio">
        <div id="default-layout-grid" class="syn-grid" style="width:650px">
          <div>one</div><div>two</div><div>three</div>
        </div>
        <div id="custom-layout-grid" class="syn-grid" style="width:650px;--syn-grid-min:12rem;--syn-grid-gap:24px">
          <div>one</div><div>two</div><div>three</div>
        </div>
        <div id="compact-layout-grid" class="syn-grid" style="width:380px;--syn-grid-min:12rem">
          <div>one</div><div>two</div><div>three</div>
        </div>
        <div class="syn-field" id="field">
          <label for="customer" class="syn-label" id="customer-label">Customer</label>
          <div class="syn-input-group" id="group">
            <input class="syn-input" id="customer" aria-describedby="customer-error">
            <span class="syn-input-addon" id="addon">ID</span>
          </div>
          <small class="syn-error" id="customer-error">Required</small>
        </div>
        <div class="syn-panel" id="active-panel">Active</div>
        <div class="syn-panel" id="inert-panel" inert>Unavailable</div>
        <div id="filters" class="syn-filter-bar" style="width:420px">
          <div class="syn-filter-field syn-filter-field--query" id="filter-query">Search</div>
          <div class="syn-filter-field" id="filter-type">Type</div>
        </div>
        <div id="filters-custom" class="syn-filter-bar" style="width:420px;--syn-filter-field-min:8rem;--syn-filter-query-min:14rem">
          <div class="syn-filter-field syn-filter-field--query" id="filter-query-custom">Search</div>
          <div class="syn-filter-field" id="filter-type-custom">Type</div>
        </div>
        <div id="details" class="syn-detail-layout" style="width:780px">
          <article class="syn-detail-main" id="detail-main">Details</article>
          <aside class="syn-detail-aside" id="detail-aside">Inspector</aside>
        </div>
        <div id="details-custom" class="syn-detail-layout" style="width:780px;--syn-detail-main-basis:28rem;--syn-detail-aside-basis:14rem">
          <article class="syn-detail-main" id="detail-main-custom">Details</article>
          <aside class="syn-detail-aside" id="detail-aside-custom">Inspector</aside>
        </div>
      </section>
    """ + "".join(
        f'<section class="syn-root" data-syn-theme="{theme}" id="default-{theme}">'
        f'<button class="syn-button" id="default-button-{theme}">Default {theme}</button></section>'
        f'<section class="syn-root" data-syn-theme="{theme}" data-syn-color-space="oklch" id="oklch-{theme}">'
        f'<button class="syn-button" id="oklch-button-{theme}">OKLCH {theme}</button>'
        f'<div data-syn-theme="grid" id="nested-srgb-{theme}">Nested sRGB</div>'
        f'<div data-syn-theme="grid" data-syn-color-space="oklch" id="nested-oklch-{theme}">Nested OKLCH</div>'
        '</section>'
        for theme in THEMES
    )
    page.set_content(markup)
    assert css_value(page, "#outside", "display") != "grid", "host styles leaked"
    assert len(css_value(page, "#default-layout-grid", "grid-template-columns").split()) == 2
    assert len(css_value(page, "#custom-layout-grid", "grid-template-columns").split()) == 3
    assert len(css_value(page, "#compact-layout-grid", "grid-template-columns").split()) == 1
    assert css_value(page, "#custom-layout-grid", "column-gap") == "24px"
    assert_same_row(page, "#filter-query", "#filter-type", False)
    assert_same_row(page, "#filter-query-custom", "#filter-type-custom", True)
    assert_same_row(page, "#detail-main", "#detail-aside", False)
    assert_same_row(page, "#detail-main-custom", "#detail-aside-custom", True)
    assert css_value(page, "#inert-panel", "border-top-style") == "dashed"
    assert css_value(page, "#active-panel", "background-color") != css_value(page, "#inert-panel", "background-color")
    assert page.locator("#inert-panel").get_attribute("inert") is not None

    page.locator("#customer").focus()
    assert canvas_color(page, "#customer-label", "color") == canvas_color(page, "#field", "--syn-accent")
    assert canvas_color(page, "#addon", "border-top-color") == canvas_color(page, "#field", "--syn-border-focus")
    page.locator("#customer").evaluate("(node) => node.setAttribute('aria-invalid','true')")
    assert canvas_color(page, "#customer-label", "color") == canvas_color(page, "#field", "--syn-danger")
    assert css_value(page, "#customer", "outline-style") != "none" or css_value(page, "#customer", "border-top-style") != "none"

    for theme in THEMES:
        default = f"#default-{theme}"
        oklch = f"#oklch-{theme}"
        assert "in srgb" in css_value(page, default, "--syn-surface-hover")
        assert "in oklch" in css_value(page, oklch, "--syn-surface-hover")
        assert "in srgb" in css_value(page, f"#nested-srgb-{theme}", "--syn-surface-hover")
        assert "in oklch" in css_value(page, f"#nested-oklch-{theme}", "--syn-surface-hover")
        selector = f"#oklch-button-{theme}"
        page.locator(selector).hover()
        background = canvas_color(page, selector, "background-color")
        foreground = canvas_color(page, selector, "color")
        assert contrast(foreground, background) >= 4.5, (
            f"{engine} {theme}: OKLCH hover text contrast {contrast(foreground, background):.2f}"
        )
    page.close()
    print(f"PASS {engine}: responsive overrides, native field/inert states, 7-theme OKLCH contrast")


def main():
    css = (ROOT / "dist/syntyr.all.css").read_text(encoding="utf-8")
    engines = sys.argv[1:] or ["chromium"]
    with sync_playwright() as p:
        for engine in engines:
            browser = getattr(p, engine).launch(headless=True)
            try:
                verify(browser, engine, css)
            finally:
                browser.close()


if __name__ == "__main__":
    main()
