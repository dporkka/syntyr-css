"""Check actual dimensional queries at -1, 0, +1 CSS pixels.

Containers are tested inside a fixed 1920px viewport, independent of device
width. Fixtures exercise published CSS, with no added application runtime.
"""
import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright
from responsive_boundaries import MEDIA, CONTAINERS, adjacent_pixels
from published_reflow_browser import INSPECT

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = {
    "workspace": '<div class="syn-resizable-workspace" data-syn-interactive><div class="syn-resizable-workspace__panes"><div class="syn-resizable-workspace__pane">Inventory</div><div class="syn-resizable-workspace__separator"></div><div class="syn-resizable-workspace__pane">Details</div></div></div>',
    "record": '<dl class="syn-record-fields"><div><dt>Account</dt><dd>Example</dd></div><div><dt>Location</dt><dd>Office</dd></div></dl>',
    "bento": '<div class="syn-bento-grid"><article class="syn-bento-card--wide">Wide</article><article>Card</article><article>Card</article></div>',
    "floating": '<div class="syn-field--floating"><input class="syn-input" id="name" placeholder=" "><label class="syn-floating-label" for="name">Name</label></div>',
    "geo": '<div class="syn-geo-shell"><div class="syn-geo-workspace"><aside class="syn-geo-sidebar">Layers</aside><div class="syn-geo-viewport"><div class="syn-geo-bottom">Legend</div></div></div></div>',
    "email": '<div class="syn-email-workspace"><div class="syn-email-layout"><aside class="syn-email-sidebar">Inbox</aside><div class="syn-email-main">Message</div></div></div>',
    "region": '<div class="syn-region"><div class="syn-stats"><div>A</div><div>B</div><div>C</div></div><div class="syn-split"><div>A</div><div>B</div></div><div class="syn-pricing"><div>A</div><div>B</div><div>C</div></div><ol class="syn-steps"><li class="syn-step">One</li><li class="syn-step">Two</li></ol><div class="syn-field-row"><label class="syn-label" for="field">Name</label><div class="syn-field-body"><input id="field" class="syn-input"></div></div></div>',
    "input": '<div class="syn-input-group"><input class="syn-input" aria-label="Search"><button class="syn-button">Go</button></div>',
}


def columns(page, selector):
    return page.locator(selector).evaluate(
        "e => getComputedStyle(e).gridTemplateColumns.trim().split(/\\s+/).length")


def style(page, selector, property_name):
    return page.locator(selector).first.evaluate("(e,p) => getComputedStyle(e)[p]", property_name)


def probe_container(page, fixture, width):
    page.set_content('<!doctype html><html style="font-size:16px"><body class="syn-root" data-syn-theme="studio"><main id="embed" style="width:%dpx;margin:0;padding:0;border:0">%s</main></body></html>' % (width, FIXTURES[fixture]))
    page.add_style_tag(path=ROOT / "dist/syntyr.all.css")
    assert page.evaluate("innerWidth") == 1920
    assert page.locator("#embed").evaluate("e => e.scrollWidth <= e.clientWidth + 1"), fixture
    # A narrow nested region must not accidentally inherit the wide ancestor's query.
    if fixture == "region":
        page.locator("#embed").evaluate("""e => {
          const outer = document.createElement('div');
          outer.className = 'syn-region';
          outer.style.width = '1200px';
          e.before(outer); outer.append(e);
        }""")
        assert page.locator("#embed").evaluate("e => e.clientWidth") == width
    if fixture == "workspace":
        assert style(page, ".syn-resizable-workspace__panes", "display") == ("block" if width <= 704 else "grid")
        assert style(page, ".syn-resizable-workspace__separator", "display") == ("none" if width <= 704 else "flex")
    elif fixture == "record":
        same_row = page.locator(".syn-record-fields > div").first.evaluate(
            "e => Math.abs(e.children[0].getBoundingClientRect().top-e.children[1].getBoundingClientRect().top)<1")
        assert same_row == (width > 384)
    elif fixture == "bento":
        assert style(page, ".syn-bento-card--wide", "gridColumnStart") == ("span 2" if width >= 592 else "auto")
    elif fixture == "floating":
        assert style(page, ".syn-floating-label", "position") == ("static" if width <= 336 else "absolute")
    elif fixture == "geo":
        assert columns(page, ".syn-geo-workspace") == (1 if width <= 768 else 2)
        assert abs(float(style(page, ".syn-geo-bottom", "bottom").removesuffix("px")) - (35.2 if width <= 416 else 29.6)) < .1
    elif fixture == "email":
        assert columns(page, ".syn-email-layout") == (2 if width >= 768 else 1)
    elif fixture == "region":
        assert columns(page, ".syn-stats") == (3 if width >= 880 else 2 if width >= 496 else 1)
        assert columns(page, ".syn-split") == (2 if width >= 688 else 1)
        assert columns(page, ".syn-pricing") == (3 if width >= 688 else 1)
        assert style(page, ".syn-steps", "gridAutoFlow") == ("column" if width >= 688 else "row")
        assert columns(page, ".syn-field-row") == (2 if width >= 672 else 1)
    elif fixture == "input":
        assert style(page, ".syn-input-group > input", "flexBasis") == ("100%" if width <= 192 else "0%")
    else:
        raise AssertionError(f"Unknown fixture {fixture}")


def probe_media(page, example, query, px):
    width, height = (1280, px) if "height" in query else (px, 900)
    page.set_viewport_size({"width": width, "height": height})
    page.goto((ROOT / example).as_uri(), wait_until="load")
    layout = page.evaluate(INSPECT)
    assert layout["scrollWidth"] <= layout["clientWidth"] + 1 and not layout["clipped"] and not layout["missingStyles"], layout
    if example == "examples/semantic-starter.html":
        padding = float(style(page, "article#preferences", "paddingTop").removesuffix("px"))
        assert abs(padding - (16 if px <= 640 else px * .03)) < .1
    if example == "examples/premium-compositions.html":
        assert style(page, ".syn-command-row", "flexWrap") == ("wrap" if px <= 640 else "nowrap")
        padding = float(style(page, ".syn-showcase", "paddingTop").removesuffix("px"))
        assert padding <= 12 if px <= 640 else padding >= 24
    if example == "examples/enterprise-compositions.html":
        first = page.locator(".syn-evidence-meta > div").first
        count = first.evaluate("e => getComputedStyle(e).gridTemplateColumns.trim().split(/\\s+/).length")
        assert count == (1 if px <= 480 else 2)
    if example == "examples/dropdowns.html":
        panel = page.locator("#actions-panel")
        page.locator("#actions-trigger").click()
        rect = panel.bounding_box()
        assert rect and rect["y"] >= -1 and rect["y"] + rect["height"] <= height + 1, rect
        if px <= 480:
            assert style(page, "#actions-panel", "maxHeight") == f"{px - 16}px"
        panel.evaluate("e => e.hidePopover()")
    if example == "examples/saas.html":
        assert columns(page, ".syn-app-shell") == (2 if px >= 848 else 1)
    if example == "examples/media-entertainment.html":
        assert style(page, ".syn-media-navigation__desktop", "display") == ("none" if px <= 768 else "flex")
        assert style(page, ".syn-media-navigation__mobile", "display") == ("flex" if px <= 768 else "none")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browsers", nargs="+", choices=("chromium", "firefox", "webkit"), default=["chromium"])
    args = parser.parse_args()
    failed = passed = blocked = 0
    with sync_playwright() as pw:
        for engine in args.browsers:
            try:
                browser = getattr(pw, engine).launch(headless=True)
            except Exception as exc:
                blocked += 1
                print(f"BLOCKED {engine}: {exc}", flush=True)
                continue
            try:
                page = browser.new_page(viewport={"width": 1920, "height": 1080}, reduced_motion="reduce")
                for kind, registry in (("container", CONTAINERS), ("media", MEDIA)):
                    for source, query, rem, target in registry:
                        for px in adjacent_pixels(rem):
                            try:
                                if kind == "container":
                                    probe_container(page, target, px)
                                else:
                                    probe_media(page, target, query, px)
                            except Exception as exc:
                                failed += 1
                                print(f"FAIL {engine} {kind} {target} {query} {px}: {type(exc).__name__} {exc}", flush=True)
                            else:
                                passed += 1
                page.close()
            finally:
                browser.close()
    print(f"Boundary checks: {passed} passed, {failed} failed, {blocked} blocked engines", flush=True)
    return int(bool(failed or blocked))


if __name__ == "__main__":
    raise SystemExit(main())
