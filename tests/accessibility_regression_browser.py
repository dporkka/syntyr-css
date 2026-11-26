"""Opt-in browser tests for accessibility regressions in shipped examples.

Runs against the actual CSS without adding runtime dependencies. Example:
  python tests/accessibility_regression_browser.py --browsers chromium firefox
"""
import argparse
import os
from pathlib import Path
from contrast_pixel_triage import contrast_ratio, parse_rgb

ROOT = Path(__file__).resolve().parents[1]


def check_document_semantics(browser, engine):
    """Browser accessibility snapshots and native keyboard paths, not AT speech."""
    page = browser.new_page(viewport={"width": 320, "height": 850})
    try:
        page.goto((ROOT / "examples/document-starter.html").as_uri())
        snapshot = page.locator("main").aria_snapshot()
        for expected in (
            'heading "Portable project notes" [level=1]',
            'heading "Layout and commands" [level=2]',
            'checkbox "Review document" [checked] [disabled]',
            'checkbox "Publish assets" [disabled]',
            'region "Configuration code"', 'region "Inventory"',
            'table "Inventory"', 'columnheader "Name"', 'columnheader "Value"',
            'rowheader "Long identifier"', 'region "References"',
            'link "Return to reference"', 'img "Fictional status bar"',
            'region "Embedded component"', 'button "Action"',
        ):
            assert expected in snapshot, (engine, expected, snapshot)
        page.get_by_role("link", name="reference", exact=True).focus()
        # Real tab navigation skips disabled task-list controls and follows
        # the authored order through local scrolling regions and footnotes.
        for target in (
            page.get_by_role("link", name="Layout and commands"),
            page.get_by_role("region", name="Configuration code"),
            page.get_by_role("region", name="Inventory"),
            page.get_by_role("link", name="Return to reference"),
            page.get_by_role("button", name="Action"),
        ):
            page.keyboard.press("Tab")
            assert target.evaluate("e => document.activeElement === e"), (engine, target)

        page.goto((ROOT / "examples/native-apis.html").as_uri())
        main = page.locator("main")
        assert 'textbox "NOTES"' in main.aria_snapshot()
        assert 'heading "Native command menu"' not in main.aria_snapshot()
        assert 'dialog "System status"' not in main.aria_snapshot()
        trigger = page.get_by_role("button", name="OPEN POPOVER")
        trigger.focus()
        page.keyboard.press("Enter")
        popover = page.locator("#native-popover")
        assert popover.evaluate('e => e.matches(":popover-open")'), engine
        assert 'heading "Native command menu"' in popover.aria_snapshot()
        assert 'button "CLOSE"' in popover.aria_snapshot()
        page.keyboard.press("Escape")
        assert not popover.evaluate('e => e.matches(":popover-open")'), engine
        assert trigger.evaluate("e => document.activeElement === e"), engine

        modal_trigger = page.get_by_role("button", name="OPEN MODAL")
        if modal_trigger.evaluate("e => 'commandForElement' in e"):
            modal_trigger.focus()
            page.keyboard.press("Enter")
            dialog = page.get_by_role("dialog", name="System status")
            assert dialog.is_visible(), engine
            assert 'button "ACKNOWLEDGE"' in dialog.aria_snapshot()
            page.keyboard.press("Escape")
            assert not dialog.is_visible(), engine
            assert modal_trigger.evaluate("e => document.activeElement === e"), engine
        # The fallback is available both with and without native invokers.
        disclosure = page.locator("#overlays details")
        fallback = "System status: operational."
        assert fallback not in disclosure.aria_snapshot()
        disclosure.locator("summary").focus()
        page.keyboard.press("Enter")
        assert disclosure.evaluate("e => e.open"), engine
        assert fallback in disclosure.aria_snapshot()
        page.keyboard.press("Enter")
        assert not disclosure.evaluate("e => e.open"), engine
        assert fallback not in disclosure.aria_snapshot()
        print(f"PASS {engine}: document AX roles, authored Tab order, popover, dialog/fallback disclosure", flush=True)
    finally:
        page.close()


def check(browser, engine):
    check_document_semantics(browser, engine)
    # All shipping palettes, including focus/filled states. Test 2x/4x root text
    # enlargement rather than claiming to emulate browser-UI zoom.
    for theme in ('studio', 'grid', 'noir', 'industrial', 'terminal', 'corporate', 'minimal'):
        for size in (32, 64):
            page = browser.new_page(viewport={"width": 320, "height": 800})
            try:
                page.goto((ROOT / "examples/native-recipes.html").as_uri())
                page.locator('.syn-root').first.evaluate("(root, theme) => root.setAttribute('data-syn-theme', theme)", theme)
                page.evaluate("size => { document.documentElement.style.fontSize = size + 'px' }", size)
                field = page.locator('#example-email')
                label = page.locator('label[for="example-email"]')

                def check_layout(state):
                    layout = label.evaluate('''label => {
                        const field = document.querySelector('#example-email');
                        const l = label.getBoundingClientRect();
                        const f = field.getBoundingClientRect();
                        return {
                            readable: label.scrollWidth <= label.clientWidth + 1,
                            stackedAbove: l.bottom <= f.top + 1,
                            fieldOverflow: field.parentElement.scrollWidth > field.parentElement.clientWidth + 1
                        };
                    }''')
                    assert layout['readable'], f"{engine} {theme} {size}px {state}: clipped label: {layout}"
                    assert layout['stackedAbove'], f"{engine} {theme} {size}px {state}: overlap: {layout}"
                    assert not layout['fieldOverflow'], f"{engine} {theme} {size}px {state}: overflow: {layout}"

                check_layout('empty')
                field.focus()
                check_layout('focused')
                field.fill('dev@example.com')
                check_layout('filled')
            finally:
                page.close()

    # Wide layouts should retain the opt-in floating effect.
    page = browser.new_page(viewport={"width": 1100, "height": 820})
    try:
        page.goto((ROOT / 'examples/native-recipes.html').as_uri())
        label = page.locator('label[for="example-email"]')
        field = page.locator('#example-email')
        field.fill('dev@example.com')
        assert label.evaluate('e => getComputedStyle(e).transform') != 'none', (
            f"{engine}: floating enhancement unexpectedly disabled on wide fields")
        page.locator('body').evaluate("e => e.setAttribute('dir', 'rtl')")
        field.fill('')
        field.blur()
        before = label.bounding_box()
        field.fill('dev@example.com')
        after = label.bounding_box()
        right_before = before['x'] + before['width']
        right_after = after['x'] + after['width']
        assert abs(right_before - right_after) <= 2, (
            f"{engine}: RTL floating label must shrink toward inline-start, "
            f"not move away from its right edge", before, after)
    finally:
        page.close()

    page = browser.new_page(viewport={"width": 320, "height": 800})
    try:
        page.goto((ROOT / "examples/resources.html").as_uri())
        table = page.locator('.syn-table-wrap.resource-table')
        assert table.count() == 1
        attrs = table.evaluate('''e => ({
            hasOverflow: e.scrollWidth > e.clientWidth + 2,
            name: e.getAttribute('aria-label'),
            role: e.getAttribute('role'),
            tabindex: e.getAttribute('tabindex')
        })''')
        assert attrs['hasOverflow'], f"{engine}: expected overflow for keyboard scroll test: {attrs}"
        assert attrs['role'] == 'region' and attrs['name'] and attrs['tabindex'] == '0', (
            f"{engine}: scrolling table lacks explicit keyboard/region semantics: {attrs}")
        table.focus()
        assert table.evaluate('e => document.activeElement === e'), f"{engine}: table cannot receive focus"
        page.keyboard.press('ArrowRight')
        page.wait_for_function("document.querySelector('.resource-table').scrollLeft > 0", timeout=2000)
    finally:
        page.close()

    # Generated documentation code may scroll horizontally. Verify a real
    # keyboard user can focus and scroll each overflowing pre element.
    for width in (320, 1280):
        page = browser.new_page(viewport={"width": width, "height": 800})
        try:
            page.goto((ROOT / "docs/design-principles.html").as_uri())
            code_blocks = page.locator('.docs-prose pre')
            assert code_blocks.count() == 4, (engine, width, "missing guide code")
            scrollable = 0
            for i in range(code_blocks.count()):
                block = code_blocks.nth(i)
                info = block.evaluate("e => ({tab:e.tabIndex, overflow:e.scrollWidth>e.clientWidth+1})")
                assert info['tab'] == 0, (engine, width, i, info)
                if info['overflow']:
                    scrollable += 1
                    block.focus()
                    assert block.evaluate("e => document.activeElement === e")
                    assert block.evaluate("e => getComputedStyle(e).outlineStyle !== 'none'")
                    block.press('ArrowRight')
                    page.wait_for_function(
                        "(index) => document.querySelectorAll('.docs-prose pre')[index].scrollLeft > 0",
                        arg=i, timeout=2000)
            if width < 768:
                assert scrollable >= 2, (engine, width, "expected keyboard-scrollable samples")
        finally:
            page.close()

    # Public integration guides need keyboard-scrollable code examples,\n    # not only the design-principles page already covered above.
    for guide in ("docs/accessibility.html", "docs/components.html"):
        page = browser.new_page(viewport={"width": 320, "height": 800})
        try:
            page.goto((ROOT / guide).as_uri())
            blocks = page.locator(".docs-prose pre")
            assert blocks.count() >= 2, (engine, guide, "missing code examples")
            for idx in range(blocks.count()):
                block = blocks.nth(idx)
                assert block.evaluate("e => e.tabIndex === 0"), (engine, guide, idx)
            first_scrollable = next((
                idx for idx in range(blocks.count())
                if blocks.nth(idx).evaluate("e => e.scrollWidth > e.clientWidth + 1")
            ), None)
            assert first_scrollable is not None, (engine, guide)
            block = blocks.nth(first_scrollable)
            block.focus()
            assert block.evaluate("e => document.activeElement === e")
            block.press("ArrowRight")
            page.wait_for_function(
                "(idx) => document.querySelectorAll('.docs-prose pre')[idx].scrollLeft > 0",
                arg=first_scrollable, timeout=2000)
        finally:
            page.close()

    for path, selectors in [
        ('index.html', ['.site-brand', '.site-nav a', '.site-hero-resources a',
                        '.site-showcase-card > .site-secondary-link', '.site-footer a']),
        ('docs/index.html', ['.docs-header .syn-logo', '.docs-flagship-links a', 'footer.syn-header a']),
    ]:
        page = browser.new_page(viewport={"width": 1280, "height": 820})
        try:
            page.goto((ROOT / path).as_uri())
            for selector in selectors:
                matches = page.locator(selector)
                assert matches.count(), f"{engine}: missing tested target {selector} on {path}"
                for idx in range(matches.count()):
                    height = matches.nth(idx).bounding_box()['height']
                    assert height >= 24, f"{engine}: undersized {path} {selector} [{idx}]: {height}px"
        finally:
            page.close()
    # Decorative line placement must never change caption contrast: the
    # fine-grid caption has an opaque surface in every named theme.
    for width in (320, 390, 1280):
        page = browser.new_page(viewport={"width": width, "height": 820},
                                reduced_motion='reduce')
        try:
            page.goto((ROOT / "docs/blocks.html").as_uri())
            for theme in ('studio', 'grid', 'noir', 'industrial',
                          'terminal', 'corporate', 'minimal'):
                page.locator('body').evaluate(
                    '(e, theme) => e.setAttribute("data-syn-theme", theme)', theme)
                caption = page.locator('.syn-block-asset--fine-grid > span')
                colors = caption.evaluate("""e => {
                    const c = getComputedStyle(e);
                    return {foreground: c.color, background: c.backgroundColor,
                            backgroundImage: c.backgroundImage, opacity: c.opacity};
                }""")
                fg, bg = parse_rgb(colors['foreground']), parse_rgb(colors['background'])
                assert fg is not None and bg is not None, (engine, theme, colors)
                assert colors['backgroundImage'] == 'none' and colors['opacity'] == '1', colors
                assert contrast_ratio(fg, bg) >= 5.0, (
                    engine, width, theme, contrast_ratio(fg, bg), colors)
        finally:
            page.close()

    # Actual placeholders are painted by the UA, not text nodes. Verify the
    # real reference pages display opaque, above-threshold computed pairs.
    for path, selector in (('docs/index.html', '#dispatch'),
                           ('examples/native-apis.html', '#native-notes')):
        page = browser.new_page(viewport={"width": 320, "height": 820})
        try:
            page.goto((ROOT / path).as_uri())
            field = page.locator(selector)
            colors = field.evaluate("""e => {
                const c = getComputedStyle(e), p = getComputedStyle(e, '::placeholder');
                return {foreground: p.color, background: c.backgroundColor,
                        backgroundImage: c.backgroundImage, opacity: p.opacity,
                        elementOpacity: c.opacity,
                        visible: e.matches(':placeholder-shown'),
                        text: e.placeholder};
            }""")
            fg, bg = parse_rgb(colors['foreground']), parse_rgb(colors['background'])
            assert colors['visible'] and colors['text'], (engine, path, colors)
            assert fg is not None and bg is not None, (engine, path, colors)
            assert colors['backgroundImage'] == 'none', colors
            assert colors['opacity'] == '1' and colors['elementOpacity'] == '1', colors
            assert contrast_ratio(fg, bg) >= 4.5, (engine, path, colors)
            # Populate a native input. The placeholder must no longer be treated
            # as displayed; the triage must leave it unresolved.
            field.fill('Existing response')
            assert not field.evaluate("e => e.matches(':placeholder-shown')"), (engine, path)
        finally:
            page.close()

    # Browser forced-colors *emulation* is useful regression coverage, but it
    # does not stand in for a native OS high-contrast screen-reader review.
    for path, selector in (
        ('docs/blocks.html', '.syn-block-asset--fine-grid > span'),
        ('docs/blocks.html', '.syn-block-asset--dot-field > span'),
        ('docs/blocks.html', '.syn-block-asset--diagonal > span'),
        ('examples/flagship-grid.html', '.flagship-lede'),
    ):
        page = browser.new_page(viewport={"width": 390, "height": 820},
                                forced_colors='active', reduced_motion='reduce')
        try:
            page.goto((ROOT / path).as_uri())
            assert page.evaluate("matchMedia('(forced-colors: active)').matches"), (
                f"{engine}: forced-colors emulation not applied")
            assert page.get_by_role('main').count() == 1, path
            target = page.locator(selector)
            assert target.is_visible(), f"{engine}: forced-colors target hidden: {path} {selector}"
            colors = target.evaluate('''e => ({foreground: getComputedStyle(e).color,
                background: getComputedStyle(e).backgroundColor})''')
            assert colors['foreground'] != colors['background'], (
                f"{engine}: forced-colors collapsed text and background: {path} {colors}")
            if path == 'docs/blocks.html':
                beam = page.locator('.syn-block-asset--beam')
                assert beam.evaluate("e => getComputedStyle(e).animationDuration") == '0s', (
                    f"{engine}: reduced-motion beam animation still active")
        finally:
            page.close()

    print(f"{engine}: floating labels, keyboard-scrollable table, and site link targets, forced-color emulation passed")


def main():
    from playwright.sync_api import sync_playwright
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--browsers', nargs='+', choices=('chromium', 'firefox', 'webkit'),
                        default=['chromium', 'firefox'])
    args = parser.parse_args()
    with sync_playwright() as playwright:
        for engine in args.browsers:
            options = {"headless": True}
            if engine == "webkit" and os.environ.get("SYNTYR_WEBKIT_EXECUTABLE"):
                options["executable_path"] = os.environ["SYNTYR_WEBKIT_EXECUTABLE"]
            browser = getattr(playwright, engine).launch(**options)
            try:
                check(browser, engine)
            finally:
                browser.close()


if __name__ == '__main__':
    main()
