"""Optional developer-only browser checks for Syntyr Blocks gallery.

Run: python tests/blocks_browser.py --browsers chromium firefox --axe-file /tmp/axe.min.js
"""
from __future__ import annotations
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
GALLERY = (ROOT / "docs/blocks.html").as_uri()
BLOCK_COUNT = len(json.loads((ROOT / "blocks/manifest.json").read_text())["blocks"])


def require(value, message):
    if not value:
        raise AssertionError(message)


def layout_check(browser, engine, width, scale):
    context = browser.new_context(viewport={"width": width, "height": 900})
    page = context.new_page()
    try:
        page.goto(GALLERY)
        page.evaluate("(scale) => {document.documentElement.style.fontSize = (16 * scale) + 'px';}", scale)
        metrics = page.evaluate("""() => {
            const d = document.documentElement;
            const controls = [...document.querySelectorAll('a,button,input,select,textarea,summary')]
              .filter(el => {
                if (el.closest('details:not([open])') && el.tagName !== 'SUMMARY') return false;
                const r = el.getBoundingClientRect(), s = getComputedStyle(el);
                if (s.display === 'none' || s.visibility === 'hidden' || !r.width || !r.height) return false;
                if (el.closest('.blocks-source, .blocks-icon-card pre, .syn-table-wrap')) return false;
                // An internally scrollable pipeline is reachable via its own
                // horizontal scroll, without widening the document viewport.
                for (let p = el.parentElement; p; p = p.parentElement) {
                  const overflow = getComputedStyle(p).overflowX;
                  if ((overflow === 'auto' || overflow === 'scroll') &&
                      p.scrollWidth > p.clientWidth + 1) return false;
                }
                return r.left < -1 || r.right > innerWidth + 1;
              }).slice(0, 6).map(el => [
                el.tagName, (el.textContent || el.getAttribute('aria-label') || '').slice(0, 32),
                Math.round(el.getBoundingClientRect().left), Math.round(el.getBoundingClientRect().right)
              ]);
            const cards = [...document.querySelectorAll('[data-block-id]')];
            return {viewport: d.clientWidth, scroll: d.scrollWidth,
                    clipped: controls, cards: cards.length,
                    visible: cards.filter(card => !card.hidden).length};
        }""")
        require(metrics["cards"] == BLOCK_COUNT and metrics["visible"] == BLOCK_COUNT,
                f"{engine} {width}px {scale}x: missing blocks {metrics}")
        require(metrics["scroll"] <= metrics["viewport"] + 1,
                f"{engine} {width}px {scale}x: overflow {metrics}")
        require(not metrics["clipped"],
                f"{engine} {width}px {scale}x: controls clipped {metrics}")
        if width == 390 and scale == 1:
            icons = page.locator("[data-icon-id]")
            expected = len(json.loads((ROOT / "blocks/icons.json").read_text())["icons"])
            require(icons.count() == expected, "Live catalog is missing icons")
            icon_search = page.locator("#blocks-icon-search")
            require(icon_search.is_visible(), "Icon search was not revealed")
            icon_search.fill("moon")
            require(page.locator("[data-icon-id]:visible").count() == 1,
                    "Icon search did not filter to a matching icon")
            icon_search.fill("")
            require(page.locator("[data-icon-id]:visible").count() == expected,
                    "Icon search did not restore the catalog")
            motion_button = page.locator(".blocks-motion-example").first
            motion_icon = motion_button.locator(".syn-icon")
            require(page.locator(".blocks-motion-example").count() == 14,
                    "New animation presets are missing from the gallery")
            resting = motion_icon.evaluate("node => getComputedStyle(node).animationName")
            require(resting == "none", f"Opt-in motion must rest by default, got {resting}")
            motion_button.hover()
            running = motion_icon.evaluate("node => getComputedStyle(node).animationName")
            require(running == "syn-icon-spin", f"Motion should run on hover, got {running}")
            page.mouse.move(0, 0)
            resting_again = motion_icon.evaluate("node => getComputedStyle(node).animationName")
            require(resting_again == "none", f"Motion must reset after hover, got {resting_again}")
            # Check every new preset and accessibility override, not only spinning.
            for icon in page.locator(".blocks-motion-example .syn-icon").all():
                preset = next(cls.removeprefix("syn-icon--") for cls in
                              icon.get_attribute("class").split()
                              if cls.startswith("syn-icon--") and cls != "syn-icon--on-interact")
                button = icon.locator("xpath=..")
                button.hover()
                actual = icon.evaluate("node => getComputedStyle(node).animationName")
                require(actual == "syn-icon-" + preset,
                        f"Preset {preset} did not animate on hover: {actual}")
            page.emulate_media(reduced_motion="reduce")
            for icon in page.locator(".blocks-motion-example .syn-icon").all():
                name = icon.evaluate("node => getComputedStyle(node).animationName")
                require(name == "none", f"Reduced motion must suppress all icons: {name}")
            page.emulate_media(reduced_motion="no-preference")
        if width == 390 and scale == 1:
            # Small text must not inherit the muted token against decorative radar rings.
            radar = page.locator(".syn-block-asset--radar")
            require(radar.count() == 1, f"{engine}: radar preview missing")
            for theme in ("studio", "grid", "noir", "industrial", "terminal", "corporate", "minimal"):
                page.locator("body.syn-root").evaluate("(e, value) => e.setAttribute('data-syn-theme', value)", theme)
                fg = radar.locator("span").evaluate("e => getComputedStyle(e).color")
                label = radar.locator("strong").evaluate("e => getComputedStyle(e).color")
                require(fg == label, f"{engine} {theme}: small radar caption is less legible than its label: {fg} / {label}")

    finally:
        context.close()


def progressive_checks(browser, engine, screenshots):
    context = browser.new_context(java_script_enabled=False,
                                  viewport={"width": 390, "height": 844},
                                  reduced_motion="reduce")
    page = context.new_page()
    page.goto(GALLERY)
    require(page.locator("[data-block-id]").count() == BLOCK_COUNT, "No-JS: blocks missing")
    require(page.locator(".blocks-preview a[href]").count() == 0,
            "No-JS: gallery preview still navigates to placeholder routes")
    icon_count = len(json.loads((ROOT / "blocks/icons.json").read_text())["icons"])
    require(page.locator("[data-icon-id]").count() == icon_count, "No-JS: SVG icons missing")
    require(page.locator(".syn-block-asset").count() == 12, "No-JS: CSS assets missing")
    require(page.locator("#blocks-controls").is_hidden(), "No-JS: controls should be hidden")
    details = page.locator(".blocks-details").first
    details.locator("summary").focus()
    page.keyboard.press("Enter")
    require(details.get_attribute("open") is not None, "No-JS: keyboard disclosure failed")
    header = page.locator('[data-block-id="site-header"] .blocks-preview > .syn-header')
    require(header.count() == 1, f"{engine}: site header preview missing")
    display = header.evaluate("e => getComputedStyle(e).display")
    require(display == "flex", f"{engine}: gallery site-header preview must preserve native flex, got {display}")
    wrap = header.evaluate("e => getComputedStyle(e).flexWrap")
    require(wrap == "wrap", f"{engine}: gallery header must keep mobile flex wrap, got {wrap}")
    mega = page.locator('[data-block-id="mega-navigation"] .blocks-preview details.syn-details')
    require(mega.count() == 1, f"{engine}: native mega-navigation disclosure missing")
    require(mega.get_attribute("open") is not None, f"{engine}: mega-navigation should start open")
    mega.locator("summary").focus()
    page.keyboard.press("Enter")
    require(mega.get_attribute("open") is None,
            f"{engine}: mega-navigation cannot close via keyboard without JS")
    page.keyboard.press("Enter")
    require(mega.get_attribute("open") is not None,
            f"{engine}: mega-navigation cannot reopen via keyboard without JS")
    block_ax = page.locator('[data-block-id="hero-product"]').aria_snapshot()
    icon_ax = page.locator('[data-icon-id="search"]').aria_snapshot()
    require("View HTML source for Product launch hero" in block_ax,
            f"Screen-reader source disclosure lacks block context: {block_ax[-350:]}")
    require("SVG source for Search" in icon_ax,
            f"Screen-reader SVG source disclosure lacks icon context: {icon_ax}")
    # Demo forms must be safely disabled, with the same grid/flex layout as
    # the copyable original forms. The fieldset wrapper is preview-only.
    for ident, layout in (
        ("auth-sign-in", "grid"), ("auth-recovery", "grid"),
        ("newsletter-signup", "grid"), ("resource-workspace", "flex"),
    ):
        fieldset = page.locator(
            f'[data-block-id="{ident}"] .blocks-preview form > fieldset.blocks-preview-disabled'
        )
        require(fieldset.count() == 1, f"{engine}: {ident} missing safe preview fieldset")
        require(fieldset.get_attribute("disabled") is not None,
                f"{engine}: {ident} preview fieldset is not disabled")
        computed = fieldset.evaluate("e => ({display: getComputedStyle(e).display, wrap: getComputedStyle(e).flexWrap})")
        require(computed["display"] == layout,
                f"{engine}: {ident} preview layout {computed}, expected {layout}")
        if layout == "flex":
            require(computed["wrap"] == "wrap",
                    f"{engine}: {ident} fieldset cannot wrap mobile controls: {computed}")
        control = fieldset.locator("input,select,button").first
        require(control.count() == 1 and control.is_disabled(),
                f"{engine}: {ident} demo controls not disabled")
    # The preview intentionally strips hrefs. Verify that its named, scrollable
    # pipeline is reachable via Tab and exposes later lanes using keyboard arrows.
    pipeline = page.locator('[data-block-id="crm-workspace"] .syn-pipeline')
    focused = False
    # Expanded icon galleries add keyboard-reachable source disclosures.
    # Walk the actual page tab-order rather than assuming <=90 focus stops.
    max_stops = page.locator("a,button,input,select,textarea,summary,[tabindex]").count() + 1
    for _ in range(max_stops):
        page.keyboard.press("Tab")
        if pipeline.evaluate("e => e === document.activeElement"):
            focused = True
            break
    require(focused, f"{engine}: pipeline is not keyboard-reachable")
    start_scroll = pipeline.evaluate("e => e.scrollLeft")
    for _ in range(4):
        page.keyboard.press("ArrowRight")
    page.wait_for_timeout(550)
    deal_link = page.locator('[data-block-id="crm-workspace"] .syn-pipeline-card a').filter(has_text="Cedar Labs")
    metric = deal_link.evaluate("""e => {
        const link = e.getBoundingClientRect();
        const pipeline = e.closest('.syn-pipeline');
        const region = pipeline.getBoundingClientRect();
        return {left: link.left, right: link.right, regionLeft: region.left,
                regionRight: region.right, scroll: pipeline.scrollLeft,
                viewport: document.documentElement.clientWidth};
    }""")
    require(metric["scroll"] > start_scroll,
            f"{engine}: arrow keys cannot scroll the focused pipeline: {metric}")
    require(metric["left"] >= max(0, metric["regionLeft"]) - 1 and
            metric["right"] <= min(metric["viewport"], metric["regionRight"]) + 1,
            f"{engine}: Cedar Labs lane is not fully visible after keyboard scrolling: {metric}")
    context.close()

    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    console_errors = []
    page.on("pageerror", lambda error: console_errors.append(str(error)))
    page.goto(GALLERY)
    require(page.locator("#blocks-controls").is_visible(), "JS: controls not revealed")
    require(page.get_by_role("searchbox", name="Search blocks").count() == 1,
            "Accessibility: search input lacks expected accessible name")
    require(page.get_by_role("button", name="Copy HTML for Product launch hero").count() == 1,
            "Accessibility: copy button lacks block context")
    require(f"{BLOCK_COUNT} of {BLOCK_COUNT}" in page.locator("#blocks-results").inner_text(), "JS: count wrong")
    page.locator("#blocks-search").fill("pricing")
    require(page.locator("[data-block-id]:visible").count() == 1, "JS: search wrong")
    page.locator("#blocks-search").fill("no-results-can-match-XYZ")
    require(page.locator("#blocks-empty").is_visible(), "JS: empty state missing")
    page.locator("#blocks-search").fill("")
    category_counts = {}
    for entry in json.loads((ROOT / "blocks/manifest.json").read_text())["blocks"]:
        key = entry["category"]
        category_counts[key] = category_counts.get(key, 0) + 1
    for selected, expected in category_counts.items():
        page.locator("#blocks-category").select_option(selected)
        require(page.locator("[data-block-id]:visible").count() == expected,
                f"JS: category filter {selected} expected {expected}")
    page.locator("#blocks-category").select_option("all")
    page.locator("#blocks-theme").select_option("noir")
    require(page.locator('.blocks-preview > .syn-root[data-syn-theme="noir"]').count() == BLOCK_COUNT,
            "JS: theme did not apply to all previews")
    if screenshots:
        screenshots.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(screenshots / f"blocks-{engine}-desktop.png"))
        page.set_viewport_size({"width": 390, "height": 844})
        page.screenshot(path=str(screenshots / f"blocks-{engine}-mobile.png"))
        page.set_viewport_size({"width": 1280, "height": 900})
    page.locator("[data-block-copy]").first.click()
    page.wait_for_function(
        "() => /copied|selected/i.test(document.querySelector('#blocks-feedback').textContent)",
        timeout=3000
    )
    status = page.locator("#blocks-feedback").inner_text().lower()
    require("copied" in status or "selected" in status, "JS: copy/fallback failed")
    require(f"{BLOCK_COUNT} of {BLOCK_COUNT}" in page.locator("#blocks-results").inner_text(), "JS: count overwritten by copy feedback")
    require(not console_errors, f"{engine}: script errors {console_errors}")
    context.close()


class QuietStaticHandler(SimpleHTTPRequestHandler):
    """Test-server only; avoid polluting browser verification output."""
    def log_message(self, fmt, *args):
        pass


def documentation_sidecar_check(browser, engine):
    """A documentation example must give the article, not its nav, the main track."""
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    try:
        page.goto(GALLERY)
        # Show the entire block card at desktop width to exercise the intended
        # two-column sidecar rather than the gallery's multi-card grid.
        page.add_style_tag(content=".blocks-grid {grid-template-columns:minmax(0,1fr) !important;}")
        region = page.locator('[data-block-id="docs-layout"] .blocks-preview .syn-sidecar')
        metrics = region.evaluate("""root => {
            const article = root.querySelector(':scope > article');
            const navigation = root.querySelector(':scope > nav');
            return {
                first: root.firstElementChild?.tagName,
                article: article?.getBoundingClientRect().width ?? 0,
                aside: navigation?.getBoundingClientRect().width ?? 0,
                layout: getComputedStyle(root).display,
            };
        }""")
        require(metrics["first"] == "ARTICLE" and metrics["layout"] == "flex",
                f"{engine}: documentation main-first sidecar contract broken: {metrics}")
        require(metrics["article"] > metrics["aside"] * 1.5,
                f"{engine}: documentation article squeezed narrower than navigation: {metrics}")
    finally:
        context.close()


def playground_preview_check(browser, engine):
    """Preview destinations are inert while editor and copy preserve real href."""
    context = browser.new_context(viewport={"width": 800, "height": 700})
    page = context.new_page()
    try:
        page.goto((ROOT / "docs/playground.html").as_uri() +
                  "#component=block-error-recovery")
        markup = page.locator("#playground-markup")
        require('/dashboard' in markup.input_value(),
                f"{engine}: editor lost source placeholder route")
        frame = page.frame_locator("#playground-preview")
        frame.get_by_text("Return to dashboard").wait_for()
        require(frame.locator("a[href]").count() == 0,
                f"{engine}: playground preview can navigate to placeholder routes")
        require('/dashboard' in markup.input_value(),
                f"{engine}: inert preview rewrote editable source")
    finally:
        context.close()


def live_clipboard_check(browser):
    """Verify actual clipboard output on a trustworthy localhost HTTP origin."""
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(QuietStaticHandler, directory=str(ROOT))
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        context = browser.new_context(permissions=["clipboard-read", "clipboard-write"])
        page = context.new_page()
        page.goto(f"http://127.0.0.1:{server.server_port}/docs/blocks.html")
        require(page.locator("#blocks-controls").is_visible(),
                "HTTP: controls not available")
        page.get_by_role("button", name="Copy HTML for Product launch hero").click()
        page.wait_for_function(
            "() => document.querySelector('#blocks-feedback').textContent.includes('HTML copied')",
            timeout=3000
        )
        clipboard = page.evaluate("navigator.clipboard.readText()")
        source = page.locator(".blocks-source code").first.text_content().strip()
        require(clipboard == source, "HTTP: clipboard differs from visible source")
        context.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def axe_check(browser, engine, axe_file):
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    page.goto(GALLERY)
    page.add_script_tag(path=str(axe_file))
    result = page.evaluate("""async () => axe.run(document, {
        runOnly: {type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}
    })""")
    violations = []
    for entry in result["violations"]:
        violations.append({"rule": entry["id"], "impact": entry["impact"],
                           "targets": [n["target"] for n in entry["nodes"][:8]],
                           "summary": [n.get("failureSummary") for n in entry["nodes"][:3]]})
    print(f"AXE {engine}: {len(violations)} violations, {len(result['incomplete'])} incomplete")
    for entry in violations:
        print(f"  {entry['impact']} {entry['rule']}: {entry['targets']}")
    context.close()
    return violations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browsers", nargs="+", default=["chromium", "firefox"],
                        choices=["chromium", "firefox", "webkit"])
    parser.add_argument("--axe-file", type=Path)
    parser.add_argument("--screenshots", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    failures = []
    evidence = {"gallery": "docs/blocks.html", "engines": {}, "failures": failures}
    with sync_playwright() as pw:
        for engine in args.browsers:
            try:
                browser = getattr(pw, engine).launch(headless=True, executable_path=os.getenv(f"SYNTYR_{engine.upper()}_EXECUTABLE"))
            except Exception as exc:
                failures.append(f"BLOCKED {engine}: {str(exc)[:240]}")
                continue
            item = {"layout_cases": [], "axe": None}
            evidence["engines"][engine] = item
            for width, scale in ((320, 1), (320, 1.5), (320, 2),
                                 (390, 1), (390, 2), (768, 1.5), (1280, 1)):
                try:
                    layout_check(browser, engine, width, scale)
                    item["layout_cases"].append([width, scale, "pass"])
                except Exception as exc:
                    failures.append(str(exc))
                    item["layout_cases"].append([width, scale, "fail"])
            try:
                progressive_checks(browser, engine, args.screenshots)
                item["progressive"] = "pass"
            except Exception as exc:
                failures.append(f"{engine} progressive: {exc}")
                item["progressive"] = "fail"
            try:
                documentation_sidecar_check(browser, engine)
                item["docs_sidecar"] = "pass"
            except Exception as exc:
                failures.append(f"{engine} documentation layout: {exc}")
                item["docs_sidecar"] = "fail"
            try:
                playground_preview_check(browser, engine)
                item["playground_navigation"] = "pass"
            except Exception as exc:
                failures.append(f"{engine} playground preview: {exc}")
                item["playground_navigation"] = "fail"
            if engine == "chromium":
                try:
                    live_clipboard_check(browser)
                    item["http_clipboard"] = "pass"
                except Exception as exc:
                    failures.append(f"{engine} HTTP clipboard: {exc}")
                    item["http_clipboard"] = "fail"
            if args.axe_file:
                try:
                    violations = axe_check(browser, engine, args.axe_file)
                    item["axe"] = violations
                    if violations:
                        failures.append(f"{engine}: axe violations {len(violations)}")
                except Exception as exc:
                    failures.append(f"{engine} axe blocked: {exc}")
            browser.close()
            print(f"COMPLETE {engine}: {len(item['layout_cases'])} layout cases")
    if args.report:
        args.report.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    for failure in failures:
        print("FAIL:", failure)
    if not failures:
        print("PASS: all requested browser checks")
    return int(bool(failures))


if __name__ == "__main__":
    sys.exit(main())
