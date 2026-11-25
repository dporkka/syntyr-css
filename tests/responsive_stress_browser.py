"""Resize live documents bidirectionally; stress real localized content.

Sample every <=32 CSS pixels plus canonical widths and media boundaries.
Root font changes are text enlargement, not actual browser zoom.
"""
import argparse
from html import escape
from pathlib import Path

from playwright.sync_api import sync_playwright
from responsive_stress import CONTENT_CASES, sweep_widths
from responsive_viewports import CANONICAL_VIEWPORTS
from published_reflow_browser import INSPECT

ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "docs/playground.html", "examples/saas.html", "examples/crm.html",
    "examples/form-composition.html", "examples/media-entertainment.html",
    "examples/premium-compositions.html",
)


def assert_layout(page):
    layout = page.evaluate(INSPECT)
    assert layout["scrollWidth"] <= layout["clientWidth"] + 1 and not layout["clipped"] and not layout["missingStyles"], layout


def localized_fixture(case):
    lang, direction, label, action, identifier = map(escape, case)
    return f"""<!doctype html><html lang="{lang}" dir="{direction}"><body class="syn-root" data-syn-theme="studio">
    <main class="syn-shell syn-region" id="stress">
      <h1 class="syn-section-heading" data-probe>{label}</h1>
      <div class="syn-field-row">
        <label class="syn-label" for="query" data-probe>{label}</label>
        <div class="syn-field-body"><div class="syn-input-group">
          <input id="query" class="syn-input" value="{identifier}">
          <button type="button" class="syn-button" data-probe>{action}</button>
        </div></div>
      </div>
      <dl class="syn-record-fields"><div><dt data-probe>{label}</dt><dd data-probe>{identifier}</dd></div></dl>
      <div class="syn-stats"><article class="syn-stat"><p class="syn-stat-label" data-probe>{label}</p><p class="syn-stat-value">123</p></article>
        <article class="syn-stat"><p class="syn-stat-label" data-probe>{label}</p><p class="syn-stat-value">456</p></article></div>
      <div class="syn-field--floating"><input class="syn-input" id="name" placeholder=" "><label for="name" class="syn-floating-label">{label}</label></div>
      <div class="syn-button-group"><button class="syn-button" data-probe>{action}</button><button class="syn-button" data-probe>{label}</button></div>
    </main></body></html>"""


def assert_localized(page, direction):
    assert_layout(page)
    result = page.evaluate("""() => {
      const probes = [...document.querySelectorAll('[data-probe]')];
      const clipped = probes.filter(e => e.scrollWidth > e.clientWidth + 1).map(e => [e.tagName, e.className, e.scrollWidth, e.clientWidth]);
      const cards = [...document.querySelectorAll('.syn-stat')].map(e => e.getBoundingClientRect().toJSON());
      const input = document.querySelector('#query').getBoundingClientRect();
      const button = document.querySelector('.syn-input-group button').getBoundingClientRect();
      return {direction: getComputedStyle(document.documentElement).direction, clipped, cards,
        // The connected controls intentionally share a 1px border seam.
        // Allow a small fractional rounding tolerance across browser engines.
        overlaps: Math.min(input.right, button.right) - Math.max(input.left, button.left) > 1.1 && Math.min(input.bottom, button.bottom) - Math.max(input.top, button.top) > 1.1};
    }""")
    assert result["direction"] == direction
    assert not result["clipped"], result["clipped"]
    assert not result["overlaps"], "input and action overlap"
    a, b = result["cards"]
    if abs(a["top"] - b["top"]) < 1:
        assert (a["left"] > b["left"]) == (direction == "rtl"), result["cards"]


def run_engine(browser, engine):
    page = browser.new_page(viewport={"width": 320, "height": 900}, reduced_motion="reduce")
    passed = failed = 0
    def check(label, fn):
        nonlocal passed, failed
        try:
            fn()
        except Exception as exc:
            failed += 1
            if failed <= 30:
                print(f"FAIL {engine} {label}: {exc}", flush=True)
        else:
            passed += 1
    try:
        widths = sweep_widths()
        for name in PAGES:
            page.goto((ROOT / name).as_uri(), wait_until="load")
            for width in (*widths, *reversed(widths[:-1])):
                page.set_viewport_size({"width": width, "height": 900})
                check(f"{name} {width}px", lambda: assert_layout(page))
        print(f"{engine} resize: {passed} passed, {failed} failed", flush=True)
        for case in CONTENT_CASES:
            page.set_content(localized_fixture(case))
            page.add_style_tag(path=ROOT / "dist/syntyr.all.css")
            for _, width, height in CANONICAL_VIEWPORTS:
                page.set_viewport_size({"width": width, "height": height})
                for scale in (1, 1.5, 2):
                    page.evaluate("(s) => document.documentElement.style.fontSize = (16*s)+'px'", scale)
                    check(f"{case[0]} {width}px {scale}x", lambda: assert_localized(page, case[1]))
    finally:
        page.close()
    print(f"{engine} total: {passed} passed, {failed} failed", flush=True)
    return passed, failed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browsers", nargs="+", choices=("chromium","firefox","webkit"), default=["chromium"])
    args = parser.parse_args()
    passed = failed = blocked = 0
    with sync_playwright() as pw:
        for engine in args.browsers:
            try:
                browser = getattr(pw, engine).launch(headless=True)
            except Exception as exc:
                blocked += 1
                print(f"BLOCKED {engine}: {exc}", flush=True)
                continue
            try:
                p, f = run_engine(browser, engine)
                passed += p
                failed += f
            finally:
                browser.close()
    print(f"Stress checks: {passed} passed, {failed} failed, {blocked} blocked engines", flush=True)
    return int(bool(failed or blocked))


if __name__ == "__main__":
    raise SystemExit(main())
