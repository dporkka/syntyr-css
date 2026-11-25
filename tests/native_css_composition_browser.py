"""Optional real-browser validation for native Subgrid and direction-aware CSS.

Usage: /path/to/playwright-python tests/native_css_composition_browser.py [chromium firefox webkit]
"""
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def geometry(page, selector):
    box = page.locator(selector).bounding_box()
    assert box is not None, f"{selector}: missing geometry"
    return box


def verify(browser, engine):
    core = (ROOT / "dist/syntyr.core.css").read_text()
    recipes = (ROOT / "dist/syntyr.recipes.css").read_text()
    page = browser.new_page(viewport={"width": 1100, "height": 900})
    page.set_content(f"""<style>{core}{recipes}</style>
      <dl class="syn-record-fields" id="outside"><div><dt>Outside</dt><dd>Unstyled</dd></div></dl>
      <main class="syn-root" data-syn-theme="studio">
        <section style="inline-size: 640px">
          <dl class="syn-record-fields" id="wide">
            <div><dt id="wide-label-a">Account owner</dt><dd id="wide-value-a">Team A</dd></div>
            <div><dt id="wide-label-b">Revenue</dt><dd id="wide-value-b">$1,234</dd></div>
          </dl>
        </section>
        <section style="inline-size: 280px">
          <dl class="syn-record-fields" id="narrow">
            <div><dt id="narrow-label">Name</dt><dd id="narrow-value">Contact</dd></div>
          </dl>
        </section>
        <article class="syn-panel syn-panel--cut" id="ltr-cut">LTR</article>
        <ol class="syn-activity-timeline" id="ltr-timeline"><li>LTR event</li></ol>
        <section dir="rtl" id="rtl">
          <article class="syn-panel syn-panel--cut" id="rtl-cut">RTL</article>
          <ol class="syn-activity-timeline" id="rtl-timeline"><li>RTL event</li></ol>
          <div class="syn-popover" popover="manual" id="rtl-pop">RTL menu</div>
        </section>
        <div class="syn-popover" popover="manual" id="ltr-pop">LTR menu</div>
      </main>""")
    assert page.locator("#outside").evaluate("(n) => getComputedStyle(n).display") != "grid", engine
    if page.evaluate("CSS.supports('grid-template-columns','subgrid')"):
        wide_a, wide_b = geometry(page, "#wide-value-a"), geometry(page, "#wide-value-b")
        assert abs(wide_a["x"] - wide_b["x"]) < 2, (engine, wide_a, wide_b)
        label = geometry(page, "#wide-label-a")
        assert wide_a["x"] > label["x"] + label["width"] - 2, (engine, label, wide_a)
        small_label, small_value = geometry(page, "#narrow-label"), geometry(page, "#narrow-value")
        assert small_value["y"] >= small_label["y"] + small_label["height"] - 2, (engine, small_label, small_value)
    ltr = page.locator("#ltr-cut").evaluate("(n) => getComputedStyle(n,'::after').right")
    rtl = page.locator("#rtl-cut").evaluate("(n) => getComputedStyle(n,'::after').left")
    assert ltr == "-1px" and rtl == "-1px", (engine, ltr, rtl)
    polygon = page.locator("#rtl-cut").evaluate("(n) => getComputedStyle(n,'::after').clipPath")
    assert "0px 0px" in polygon or "0 0" in polygon, (engine, polygon)
    ltr_marker = page.locator("#ltr-timeline li").evaluate("(n) => getComputedStyle(n,'::before').left")
    rtl_marker = page.locator("#rtl-timeline li").evaluate("(n) => getComputedStyle(n,'::before').right")
    assert ltr_marker == rtl_marker == "4px", (engine, ltr_marker, rtl_marker)
    page.locator("#ltr-pop").evaluate("(n) => n.showPopover()")
    ltr_pop = geometry(page, "#ltr-pop")
    assert ltr_pop["x"] + ltr_pop["width"] > 1060, (engine, ltr_pop)
    page.locator("#ltr-pop").evaluate("(n) => n.hidePopover()")
    page.locator("#rtl-pop").evaluate("(n) => n.showPopover()")
    rtl_pop = geometry(page, "#rtl-pop")
    assert rtl_pop["x"] < 40, (engine, rtl_pop)
    page.close()
    print(f"PASS {engine}: Subgrid reflow, RTL corner, logical popover fallback, scope")


if __name__ == "__main__":
    names = sys.argv[1:] or ["chromium", "firefox", "webkit"]
    with sync_playwright() as p:
        for name in names:
            browser = getattr(p, name).launch(headless=True)
            try:
                verify(browser, name)
            finally:
                browser.close()
