"""Opt-in browser matrix: no runtime JS or CSS dependency introduced.

Requires developer-only Playwright + browsers:
  python3 tests/browser_matrix.py --browsers chromium firefox webkit
  PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/chromium-browser python3 ...
Run on a machine with the native browser dependencies installed. A missing
browser is reported as BLOCKED and never counted as PASS.
"""
import argparse
from pathlib import Path
import os
import shutil
import sys
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("index.html", "docs/index.html", "docs/catalog.html", "docs/blocks.html", "docs/guides.html", "docs/design-principles.html", "examples/console.html",
         "examples/resources.html", "examples/pricing.html",
         "docs/console-kit.html", "examples/saas.html", "examples/settings-billing.html",
         "examples/business.html", "examples/terminal.html", "examples/geometry-terminal.html",
         "examples/operations-console.html", "examples/themes.html",
         "examples/vertigo-admin.html", "examples/vertigo-resource-workflow.html", "examples/saas-workflows.html", "examples/crm.html", "examples/minimalist-patterns.html", "examples/design-states.html", "examples/symbols.html", "examples/native-elements.html",
         "examples/native-apis.html", "examples/dropdowns.html", "examples/flagship-studio.html", "examples/flagship-noir.html", "examples/flagship-grid.html",
         "examples/semantic-starter.html", "examples/workflow-steps.html", "examples/enterprise-compositions.html", "examples/premium-compositions.html", "examples/operation-revisions.html",
)

def assert_page(browser, name: str, viewport: int) -> None:
    context = browser.new_context(viewport={"width": viewport, "height": 820},
                                  reduced_motion="reduce")
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    url = (ROOT / name).as_uri()
    response = page.goto(url, wait_until="load")
    assert page.url == url, (url, page.url)
    assert response is None or response.ok, (url, response.status)
    if name == "docs/catalog.html":
        # Existing catalog script remains isolated from consumer CSS.
        assert page.locator('script[src="catalog.js"]').count() == 1
        assert page.locator("script").count() == 1
    elif name == "docs/blocks.html":
        # New Blocks gallery script is documentation-only as well.
        assert page.locator('script[src="blocks.js"]').count() == 1
        assert page.locator("script").count() == 1
    else:
        assert page.locator("script").count() == 0, name
    assert page.get_by_role("main").count() == 1, name
    assert page.locator('link[rel="stylesheet"]').count() >= 1
    css = page.locator("body").evaluate("e => getComputedStyle(e).getPropertyValue('--syn-accent').trim()")
    if name == "examples/minimalist-patterns.html":
        assert "light-dark(" in css, (name, css)
    else:
        assert css in ("#76e7f7", "#f1b574", "#2458c6", "#ffb36b", "#65e8a0", "#155ac8", "#313a45"), (name, css)
    if name == "examples/native-elements.html" and viewport == 320:
        # A native file input must not force a semantic fieldset grid track
        # wider than the viewport. Check the offending region, not only body.
        fieldset = page.get_by_role("group", name="Native inputs")
        bounds = fieldset.evaluate("e => ({client: e.clientWidth, scroll: e.scrollWidth})")
        assert bounds["scroll"] <= bounds["client"] + 1, (name, viewport, bounds)
    overflow = page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
    assert overflow <= 1, (name, viewport, overflow)
    assert not errors, (name, errors)
    if name == "examples/crm.html":
        board = page.locator(".syn-pipeline")
        assert board.get_attribute("tabindex") == "0"
        assert board.get_attribute("role") == "group"
        assert board.evaluate("e => getComputedStyle(e).overflowX") == "auto"
        assert page.locator(".syn-pipeline-lane").count() == 2
        assert page.locator(".syn-record-fields dt").count() == 4
        compact = page.locator(".syn-app-card").first.evaluate(
            "e => parseFloat(getComputedStyle(e).paddingTop)")
        comfortable = page.locator("#account-details").evaluate(
            "e => parseFloat(getComputedStyle(e).paddingTop)")
        assert comfortable > compact, (compact, comfortable)
        if viewport == 320:
            assert board.evaluate("e => e.scrollWidth > e.clientWidth")
    if name == "examples/workflow-steps.html":
        assert page.get_by_role("list", name="Workspace setup progress").count() == 1
        assert page.locator(".syn-steps").count() == 2
        assert page.locator('.syn-steps:not(.syn-steps--vertical) > [aria-current="step"]').count() == 1
        assert page.locator(".syn-steps--vertical > .syn-step").count() == 3
        flow = page.locator(".syn-steps").first.evaluate("e => getComputedStyle(e).gridAutoFlow")
        forced_flow = page.locator(".syn-steps--vertical").evaluate("e => getComputedStyle(e).gridAutoFlow")
        assert flow == ("column" if viewport >= 1280 else "row"), (viewport, flow)
        assert forced_flow == "row", (viewport, forced_flow)
        assert page.locator(".syn-step").first.evaluate("e => getComputedStyle(e, '::before').content") != "none"
    if name == "examples/semantic-starter.html":
        assert page.locator('link[rel="stylesheet"]').count() == 1
        assert page.locator('body.syn-root.syn-semantic').count() == 1
        control = page.get_by_role("textbox", name="Project name")
        assert control.is_visible()
        assert control.evaluate('e => getComputedStyle(e).borderWidth') != '0px'
        button = page.get_by_role('button', name='Preview query URL')
        assert button.is_visible()
        assert button.evaluate('e => getComputedStyle(e).display') in ('flex', 'inline-flex')
        assert page.locator('script').count() == 0
        assert page.locator('form:not([class])').evaluate(
            "e => getComputedStyle(e).display") == "grid"
        assert page.locator('fieldset:not([class])').evaluate(
            "e => getComputedStyle(e).display") == "grid"
        assert page.locator('table caption').inner_text() == "Example project inventory"
        assert page.get_by_role("navigation", name="Page sections").is_visible()
        summary = page.locator('details > summary').first
        assert summary.evaluate("e => e.getBoundingClientRect().height") >= 44
        summary.click()
        assert page.locator("details").first.get_attribute("open") is not None
        # Hidden must beat classed/semantic display rules; find-in-page reveal stays intact.
        visibility = page.evaluate("""() => {
          const root = document.querySelector('body.syn-root.syn-semantic');
          const make = (tag, name, hidden) => {
            const element = document.createElement(tag);
            element.className = name;
            element.setAttribute('hidden', hidden);
            root.append(element);
            return element;
          };
          const button = make('button', 'syn-button', '');
          const semantic = make('button', '', '');
          const grid = make('div', 'syn-grid', '');
          const findable = make('div', 'syn-grid', 'until-found');
          const display = element => getComputedStyle(element).display;
          const initial = [display(button), display(semantic), display(grid),
                           display(findable), getComputedStyle(findable).contentVisibility];
          button.removeAttribute('hidden');
          const shown = display(button);
          root.setAttribute('hidden', '');
          const rootHidden = display(root);
          root.removeAttribute('hidden');
          for (const element of [button, semantic, grid, findable]) element.remove();
          return { initial, shown, rootHidden };
        }""")
        assert visibility["initial"][:3] == ["none"] * 3, visibility
        assert visibility["initial"][3] != "none", visibility
        assert visibility["initial"][4] == "hidden", visibility
        assert visibility["shown"] == "inline-flex", visibility
        assert visibility["rootHidden"] == "none", visibility
    if name == "docs/catalog.html":
        cards = page.locator(".catalog-card")
        total = cards.count()
        assert total >= 8, total
        assert all(cards.nth(i).is_visible() for i in range(total))
        search = page.get_by_role("searchbox", name="Find a component")
        assert search.is_visible()
        search.fill("buttons")
        assert page.locator(".catalog-card:visible").count() == 1, "search must hide unmatched cards"
        assert f"Showing 1 of {total}" in page.locator("#catalog-results").inner_text()
        search.fill("no-matching-syntyr-component-123456")
        assert page.locator(".catalog-card:visible").count() == 0
        assert page.locator("#catalog-empty").is_visible()
        search.fill("")
        assert page.locator(".catalog-card:visible").count() == total
        if viewport == 1280:
            button = page.get_by_role("button", name="Copy HTML").first
            assert button.is_visible()
            button.click()
            # Clipboard permission handling is async; await the observable live
            # region update rather than asserting synchronously after a click.
            page.wait_for_function("""() => {
                const message = document.getElementById('catalog-results')?.textContent || '';
                return message.includes('HTML copied.') || message.includes('HTML selected.');
            }""", timeout=3000)
            status = page.locator("#catalog-results").inner_text()
            assert ("HTML copied." in status or "HTML selected." in status), status
            # Without documentation JavaScript, actual components and HTML source
            # must still be usable; do not ship a JS-only catalog by accident.
            fallback = browser.new_context(viewport={"width": 1280, "height": 850},
                                           java_script_enabled=False)
            try:
                static = fallback.new_page()
                static.goto(url, wait_until="load")
                assert static.locator("#catalog-controls").is_hidden()
                assert static.locator(".catalog-card:visible").count() == total
                assert static.locator(".catalog-copy:visible").count() == 0
                summary = static.locator(".catalog-code-details summary").first
                summary.click()
                assert static.locator(".catalog-code-details").first.get_attribute("open") is not None
            finally:
                fallback.close()
    if name == "index.html":
        assert page.locator('body').get_attribute('data-syn-theme') == 'studio'
        assert page.get_by_role('heading', level=1).count() == 1
        assert page.locator('.site-showcase-card').count() == 3
        assert page.locator('.site-theme-swatch').count() == 7
        preview = page.get_by_role('img', name='Illustrative Grid-themed SaaS dashboard with navigation, key metrics and a chart. No live data.')
        assert preview.count() == 1
        assert preview.evaluate('e => getComputedStyle(e).colorScheme') == 'dark'
        palette_nav = page.get_by_role('navigation', name='Explore published themes')
        assert palette_nav.count() == 1
        for theme, expected_scheme in (('studio', 'light'), ('grid', 'dark'), ('noir', 'dark')):
            link = palette_nav.locator(f'.site-palette-link[data-syn-theme="{theme}"]')
            assert link.get_attribute('href') == '#theme-comparison'
            assert link.evaluate('e => getComputedStyle(e).colorScheme') == expected_scheme
            assert link.is_visible()
        assert page.locator('#grid').evaluate('e => getComputedStyle(e).colorScheme') == 'dark'
        assert page.locator('#business').evaluate('e => getComputedStyle(e).colorScheme') == 'light'
        for path in ('examples/saas-workflows.html', 'examples/business.html',
                     'examples/console.html', 'examples/landing.html'):
            assert page.locator(f'a[href="{path}"]').count() >= 1, (name, path)
        cards = [page.locator('.site-showcase-card').nth(i).bounding_box() for i in range(3)]
        if viewport < 700:
            assert cards[0]['y'] < cards[1]['y'] < cards[2]['y'], cards
        else:
            assert cards[0]['x'] < cards[1]['x'] < cards[2]['x'], cards
        code_styles = page.locator('.site-code code').evaluate_all(
            'elements => elements.map(e => getComputedStyle(e).whiteSpace)'
        )
        assert code_styles and all(style == 'pre-wrap' for style in code_styles), code_styles
        page.keyboard.press('Tab')
        assert page.evaluate("document.activeElement.classList.contains('site-skip')"), 'skip link first in tab order'
        assert page.locator('.site-skip').bounding_box()['y'] >= 0, 'skip link must become visible'
        if viewport == 1280:
            trigger = page.get_by_role('button', name='Try native popover')
            trigger.click()
            assert page.locator('#grid-popover').evaluate('e => e.matches(":popover-open")')
            page.keyboard.press('Escape')
            assert not page.locator('#grid-popover').evaluate('e => e.matches(":popover-open")')
    if name == "examples/flagship-grid.html" and viewport == 320:
        page.evaluate("document.documentElement.style.fontSize = '32px'")
        output = page.get_by_role("region", name="Simulated command output")
        output.scroll_into_view_if_needed()
        page.keyboard.press("Tab")
        output.focus()
        assert output.evaluate("e => document.activeElement === e")
        assert output.evaluate("e => getComputedStyle(e).outlineStyle") != "none"
        measures = output.evaluate("e => ({client:e.clientWidth, scroll:e.scrollWidth})")
        assert measures["scroll"] > measures["client"], measures
        output.evaluate("e => {e.scrollLeft = e.scrollWidth;}")
        assert output.evaluate("e => e.scrollLeft") > 0
    if name == "examples/flagship-noir.html" and viewport == 320:
        page.emulate_media(forced_colors="active")
        pillar = page.locator(".flagship-pillar").first
        colors = pillar.evaluate("""e => ({
            background: getComputedStyle(e).backgroundColor,
            foreground: getComputedStyle(e.querySelector('h3')).color
        })""")
        assert colors["background"] != colors["foreground"], colors
    if name == "docs/index.html" and viewport == 1280:
        button = page.get_by_role("button", name="OPEN COMMAND")
        button.focus()
        outline = button.evaluate("e => getComputedStyle(e).outlineStyle")
        assert outline != "none", outline
        page.keyboard.press("Enter")
        popover = page.locator("#command-popover")
        assert popover.evaluate('e => e.matches(":popover-open")'), "popover cannot open"
        page.keyboard.press("Escape")
        assert not popover.evaluate('e => e.matches(":popover-open")'), "popover cannot dismiss"
        details = page.locator("#components details").first
        details.locator("summary").click()
        assert details.evaluate("e => e.open"), "disclosure cannot open"
        # New HTML-first navigation and static loading states must render in-browser.
        breadcrumb = page.get_by_role("navigation", name="Breadcrumb")
        assert breadcrumb.get_by_text("Component gallery").get_attribute("aria-current") == "page"
        pages = page.get_by_role("navigation", name="Gallery sections")
        assert pages.get_by_role("link").count() == 3
        first_page_link = pages.get_by_role("link").first
        assert first_page_link.evaluate("e => e.getBoundingClientRect().height") >= 44
        # Match keyboard modality before programmatic focus: focus-visible is
        # intentionally not required after a pointer-originated interaction.
        page.keyboard.press("Tab")
        first_page_link.focus()
        assert first_page_link.evaluate("e => getComputedStyle(e).outlineStyle") != "none"
        skeleton = page.locator(".syn-skeleton").first
        assert skeleton.get_attribute("aria-hidden") == "true"
        assert skeleton.evaluate("e => getComputedStyle(e).animationName") == "none"
        assert skeleton.evaluate("e => getComputedStyle(e).backgroundColor") != "rgba(0, 0, 0, 0)"
    if name == "examples/native-apis.html":
        assert page.locator("script").count() == 0
        progress = page.locator(".syn-reading-progress")
        assert progress.get_attribute("aria-hidden") == "true"
        # Browser matrix defaults to reduced motion; visual-only effects are hidden.
        assert progress.evaluate("e => getComputedStyle(e).display") == "none"
        if viewport == 1280:
            notes = page.locator("#native-notes")
            original_height = notes.evaluate("e => e.getBoundingClientRect().height")
            notes.fill("\n".join("Line of content" for _ in range(18)))
            grown_height = notes.evaluate("e => e.getBoundingClientRect().height")
            supports_field_sizing = page.evaluate("CSS.supports('field-sizing', 'content')")
            if supports_field_sizing:
                assert grown_height > original_height, (original_height, grown_height)
            else:
                assert grown_height >= original_height
            popup_button = page.get_by_role("button", name="OPEN POPOVER")
            popup_button.click()
            popup = page.locator("#native-popover")
            assert popup.evaluate('e => e.matches(":popover-open")'), "popover did not open"
            supports_anchor = page.evaluate("CSS.supports('position-area', 'bottom')")
            if supports_anchor:
                placement_before_close = popup.evaluate("e => getComputedStyle(e).positionArea")
                assert placement_before_close not in ("normal", "none", ""), placement_before_close
            page.keyboard.press("Escape")
            assert not popup.evaluate('e => e.matches(":popover-open")')
            # Position-area must remain configured after :popover-open stops matching.
            # Engines can recompute a flipped position when the element is hidden;
            # comparing exact before/after positions would reject valid behavior.
            if supports_anchor:
                placement_after_close = popup.evaluate("e => getComputedStyle(e).positionArea")
                assert placement_after_close not in ("normal", "none", ""), (
                    placement_before_close, placement_after_close)
            dialog_opener = page.get_by_role("button", name="OPEN MODAL")
            dialog_opener.click()
            modal = page.locator("#native-dialog")
            supports_commands = page.evaluate("'commandForElement' in HTMLButtonElement.prototype")
            if supports_commands:
                assert modal.evaluate("e => e.open"), "dialog command did not open modal"
                modal.get_by_role("button", name="ACKNOWLEDGE").click()
                assert not modal.evaluate("e => e.open"), "dialog form failed to close modal"
            else:
                assert page.locator("details").count() >= 1, "legacy command fallback missing"
    if name == "examples/resources.html":
        assert page.get_by_role("search").count() == 1
        assert page.get_by_role("table").count() == 1
        assert page.get_by_role("searchbox", name="SEARCH BY NAME").count() == 1
    if name == "examples/themes.html":
        expected = {
            "grid": ("#76e7f7", "dark"),
            "noir": ("#f1b574", "dark"),
            "studio": ("#2458c6", "light"),
            "industrial": ("#ffb36b", "dark"),
            "terminal": ("#65e8a0", "dark"),
            "corporate": ("#155ac8", "light"),
            "minimal": ("#313a45", "light"),
        }
        assert page.locator(".theme-tile").count() == len(expected)
        for theme, (accent, scheme) in expected.items():
            tile = page.locator(f'.theme-tile[data-syn-theme="{theme}"]')
            assert tile.count() == 1, theme
            values = tile.evaluate("""e => ({
                accent: getComputedStyle(e).getPropertyValue('--syn-accent').trim(),
                colorScheme: getComputedStyle(e).colorScheme
            })""")
            assert values["accent"] == accent, (theme, values)
            assert values["colorScheme"] == scheme, (theme, values)
            button = tile.locator(".syn-button--primary")
            assert button.is_visible(), (theme, "primary button hidden")
        if viewport == 1280:
            nested = page.evaluate("""() => {
                function create(parent, name, classes) {
                    const node = document.createElement('section');
                    node.className = classes;
                    node.dataset.synTheme = name;
                    node.innerHTML = '<h3>Nested theme heading</h3>';
                    parent.append(node);
                    const style = getComputedStyle(node);
                    return {
                        text: getComputedStyle(node.querySelector('h3')).color,
                        colorScheme: style.colorScheme,
                        radius: style.getPropertyValue('--syn-radius').trim(),
                        cut: style.getPropertyValue('--syn-cut').trim()
                    };
                }
                const grid = document.querySelector('.theme-tile[data-syn-theme="grid"]');
                const corporate = document.querySelector('.theme-tile[data-syn-theme="corporate"]');
                const terminal = document.querySelector('.theme-tile[data-syn-theme="terminal"]');
                const minimal = document.querySelector('.theme-tile[data-syn-theme="minimal"]');
                const plain = document.createElement('section');
                plain.dataset.synTheme = 'grid';
                plain.innerHTML = '<h3>Plain nested theme</h3>';
                minimal.append(plain);
                const plainStyles = getComputedStyle(plain);
                const plainBoundary = {
                    background: plainStyles.backgroundColor,
                    text: getComputedStyle(plain.querySelector('h3')).color
                };
                const lightInDark = create(grid, 'corporate', 'syn-price-card');
                const darkInLight = create(corporate, 'grid', 'syn-price-card');
                const gridInTerminal = create(terminal, 'grid', 'syn-panel syn-panel--cut');
                const flex = document.createElement('div');
                flex.className = 'syn-u-flex syn-u-between syn-u-center';
                corporate.append(flex);
                return {lightInDark, darkInLight, gridInTerminal, plainBoundary,
                        justify: getComputedStyle(flex).justifyContent,
                        align: getComputedStyle(flex).alignItems};
            }""")
            assert nested["lightInDark"]["text"] == "rgb(24, 39, 60)", nested
            assert nested["lightInDark"]["colorScheme"] == "light", nested
            assert nested["darkInLight"]["text"] == "rgb(237, 249, 255)", nested
            assert nested["darkInLight"]["colorScheme"] == "dark", nested
            assert nested["plainBoundary"]["background"] == "rgb(8, 15, 25)", nested
            assert nested["plainBoundary"]["text"] == "rgb(237, 249, 255)", nested
            assert nested["gridInTerminal"]["radius"] == ".25rem", nested
            assert nested["gridInTerminal"]["cut"] == ".9rem", nested
            assert nested["justify"] == "space-between", nested
            assert nested["align"] == "center", nested
    if name == "examples/operations-console.html":
        assert page.get_by_role("heading", name="An operations console built on HTML.").count() == 1
        assert page.locator(".syn-kpi-grid article").count() == 4
        assert page.get_by_role("table").count() == 1
        assert page.locator("progress").count() == 4
        assert page.locator(".syn-terminal").count() == 1
        noir = page.locator(".ops-metric[data-syn-theme='noir']")
        assert noir.evaluate("e => getComputedStyle(e).getPropertyValue('--syn-accent').trim()") == "#f1b574"
        if viewport == 1280:
            page.get_by_role("link", name="Skip to content").focus()
            assert page.locator(":focus").evaluate("e => getComputedStyle(e).outlineStyle") != "none"
            details = page.locator("#integration details").first
            details.locator("summary").click()
            assert details.evaluate("e => e.open"), "native disclosure should work without JS"
    if name == "examples/geometry-terminal.html":
        frames = page.locator(".syn-frame")
        # The geometry gallery now includes bevel/notch/step/facet/bracket/inset/circuit.
        assert frames.count() == 7, "all seven frame profiles must render"
        assert page.locator(".syn-frame--step").count() == 1
        assert page.locator(".syn-frame--facet").count() == 1
        bevel = frames.first
        clip = bevel.evaluate("e => getComputedStyle(e, '::before').clipPath")
        assert clip.startswith("polygon("), (name, viewport, clip)
        fill = bevel.evaluate("e => getComputedStyle(e, '::after').backgroundColor")
        assert fill not in ("rgba(0, 0, 0, 0)", "transparent"), fill
        assert page.locator(".syn-terminal-error").count() == 1
        assert page.locator(".syn-terminal-warning").count() == 1
        numeric = page.locator(".syn-cell--numeric").first
        assert numeric.evaluate("e => getComputedStyle(e).textAlign") == "right"
        if viewport == 1280:
            panel_group = page.locator("#geometry .syn-grid")
            panel_group.evaluate("e => e.style.setProperty('--syn-frame-fill', '#225533')")
            inherited_fill = bevel.evaluate("e => getComputedStyle(e, '::after').backgroundColor")
            assert inherited_fill == "rgb(34, 85, 51)", inherited_fill

            page.evaluate("""() => {
                const controls = document.createElement('div');
                controls.innerHTML = '<button class="syn-button syn-button--primary" aria-disabled="true" id="syn-aria-disabled">ARIA disabled</button>'
                    + '<button class="syn-button syn-button--primary" disabled id="syn-native-disabled">Native disabled</button>';
                document.querySelector('main').append(controls);
            }""")
            aria_button = page.locator("#syn-aria-disabled")
            original_background = aria_button.evaluate("e => getComputedStyle(e).backgroundColor")
            aria_button.hover()
            assert aria_button.evaluate("e => getComputedStyle(e).backgroundColor") == original_background
            assert aria_button.evaluate("e => getComputedStyle(e).cursor") == "not-allowed"
            assert aria_button.evaluate("e => getComputedStyle(e).pointerEvents") != "none"
            native_button = page.locator("#syn-native-disabled")
            assert native_button.evaluate("e => getComputedStyle(e).cursor") == "not-allowed"

            page.emulate_media(forced_colors="active")
            assert bevel.evaluate("e => getComputedStyle(e).borderTopStyle") == "solid"
            assert bevel.evaluate("e => getComputedStyle(e, '::before').display") == "none"
    if name == "examples/design-states.html":
        assert page.get_by_role("heading", name="Clarity in every state.").count() == 1
        assert page.get_by_role("button", name="Disabled native button").is_disabled()
        if viewport == 1280:
            field_bottom = page.locator("#classless-name").evaluate("e => e.getBoundingClientRect().bottom")
            button_top = page.get_by_role("button", name="Native button", exact=True).evaluate("e => e.getBoundingClientRect().top")
            assert button_top - field_bottom >= 8, "semantic example controls need vertical rhythm"
            grid = page.locator('[data-syn-theme="grid"]')
            studio = page.locator("body")
            token = "e => getComputedStyle(e).getPropertyValue('--syn-focus-ring').trim()"
            assert grid.evaluate(token) != studio.evaluate(token), "nested focus color failed"
            regular = page.get_by_role("button", name="Execute")
            compact = page.get_by_role("button", name="Review")
            measure = "e => e.getBoundingClientRect().height"
            assert compact.evaluate(measure) < regular.evaluate(measure), "compact control height failed"
            selected = page.get_by_role("button", name="Selected")
            background = "e => getComputedStyle(e).backgroundColor"
            selected_color = selected.evaluate(background)
            selected.hover()
            assert selected.evaluate(background) == selected_color, "pressed state lost on hover"
            invalid = page.locator("#email")
            border = "e => getComputedStyle(e).borderTopColor"
            invalid.hover()
            invalid_color = invalid.evaluate(border)
            invalid.focus()
            assert invalid.evaluate(border) == invalid_color, "invalid state lost on focus"
            page.keyboard.press("Tab")
            selected.focus()
            assert selected.evaluate("e => getComputedStyle(e).outlineStyle") != "none"
            page.emulate_media(forced_colors="active")
            assert selected.evaluate("e => getComputedStyle(e).outlineStyle") != "none"
    if name == "examples/symbols.html":
        icons = page.locator(".syn-icon")
        assert icons.count() == 2
        for icon in icons.all():
            values = icon.evaluate("""e => ({
                width: e.getBoundingClientRect().width,
                height: e.getBoundingClientRect().height,
                color: getComputedStyle(e).color,
            })""")
            assert values["width"] >= 12 and abs(values["width"] - values["height"]) <= 1, values
        ascii = page.locator(".syn-ascii").first
        styles = ascii.evaluate("""e => ({
            whiteSpace: getComputedStyle(e).whiteSpace,
            overflowX: getComputedStyle(e).overflowX,
            fontVariantLigatures: getComputedStyle(e).fontVariantLigatures,
        })""")
        assert styles == {"whiteSpace": "pre", "overflowX": "auto",
                          "fontVariantLigatures": "none"}, styles
        # The long line must scroll *inside* the pre, not expand the document.
        ascii.evaluate("e => e.style.inlineSize = '10ch'")
        assert ascii.evaluate("e => e.scrollWidth > e.clientWidth")
        assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1")
        assert page.locator(".syn-symbol[aria-hidden='true']").count() >= 5
        if viewport == 1280:
            accessible = page.locator('main').aria_snapshot()
            # Decorative glyphs and text-art disappear from the accessibility
            # tree; visible equivalents remain.
            for phrase in ('API online and jobs online',
                           'Gateway healthy and queue connected',
                           'Search example (disabled)', 'Network healthy'):
                assert phrase in accessible, (phrase, accessible)
            for hidden in ('JOBS [OK]', 'Queue: connected', 'SYNTYR / CONTROLLER'):
                assert hidden not in accessible, (hidden, accessible)
            # Check actual cascade scoping, not only the CSS source strings:
            # unrelated pages using the same class names must remain untouched.
            result = page.evaluate("""() => {
                document.body.classList.remove('syn-root');
                document.body.innerHTML = [
                  '<div id="outside"><span class="syn-icon"></span>',
                  '<pre class="syn-ascii">xy</pre>',
                  '<span class="syn-symbol">◇</span></div>',
                  '<div id="inside" class="syn-root">',
                  '<span class="syn-icon"></span><pre class="syn-ascii">xy</pre>',
                  '<span class="syn-symbol">◇</span></div>',
                  '<pre id="self" class="syn-root syn-ascii">xy</pre>'
                ].join('');
                function measure(selector) {
                  const el = document.querySelector(selector);
                  const cs = getComputedStyle(el);
                  return {display: cs.display, whitespace: cs.whiteSpace,
                    ligatures: cs.fontVariantLigatures, lineHeight: cs.lineHeight};
                }
                return {
                  outsideIcon: measure('#outside .syn-icon'),
                  insideIcon: measure('#inside .syn-icon'),
                  outsideText: measure('#outside .syn-ascii'),
                  insideText: measure('#inside .syn-ascii'),
                  rootSelf: measure('#self'),
                  outsideSymbol: measure('#outside .syn-symbol'),
                  insideSymbol: measure('#inside .syn-symbol')
                };
            }""")
            assert result['outsideIcon']['display'] == 'inline', result
            assert result['insideIcon']['display'] == 'inline-block', result
            assert result['outsideText']['ligatures'] != 'none', result
            assert result['insideText']['ligatures'] == 'none', result
            assert result['rootSelf']['ligatures'] == 'none', result
            assert result['outsideSymbol']['display'] == 'inline', result
            assert result['insideSymbol']['display'] == 'inline-block', result
    if name == "examples/saas-workflows.html":
        assert page.get_by_role("search").count() == 1, name
        assert page.get_by_role("table").count() == 1, name
        assert page.get_by_role("navigation", name="Breadcrumb").count() == 1, name
        assert page.get_by_role("navigation", name="Pagination example").get_by_role("link").count() == 3
        assert page.locator("#results tbody tr").count() == 3, name
        assert page.get_by_role("searchbox", name="SEARCH RECORDS").count() == 1
        assert page.locator(".syn-skeleton[aria-hidden='true']").count() == 2
        assert page.get_by_role("navigation", name="Pagination example").get_by_role("link").first.evaluate(
            "e => e.getBoundingClientRect().height") >= 44
        if viewport == 1280:
            page.get_by_text("Display preferences").click()
            assert page.locator("#preferences details").first.evaluate("e => !e.open")
            page.get_by_text("Display preferences").click()
            assert page.locator("#preferences details").first.evaluate("e => e.open")
            compact = page.get_by_role("checkbox", name="Compact record density (local preview)")
            cell = page.locator("#results tbody td").first
            compact_height = cell.evaluate("e => getComputedStyle(e).paddingTop")
            assert compact.is_checked()
            compact.uncheck()
            expanded_height = cell.evaluate("e => getComputedStyle(e).paddingTop")
            assert float(expanded_height.removesuffix("px")) > float(compact_height.removesuffix("px"))
            notifications = page.get_by_role("checkbox", name="Email notifications (requires server)")
            assert notifications.is_disabled()
            searchbox = page.get_by_role("searchbox", name="SEARCH RECORDS")
            searchbox.fill("Atlas")
            assert searchbox.input_value() == "Atlas"

    if name == "examples/vertigo-resource-workflow.html":
        assert page.get_by_role("search", name="Search task resources").count() == 1
        assert page.get_by_role("table").count() == 1
        assert page.locator("#resource-detail").count() == 1
        assert page.locator("#resource-editor fieldset").get_attribute("disabled") is not None
        assert page.get_by_role("button", name="Save (requires backend)", include_hidden=True).is_disabled()
        assert page.locator("script").count() == 0
        assert page.locator('body[data-syn-theme="studio"][data-syn-density="compact"]').count() == 1
        if viewport == 320:
            table = page.locator(".vrw-table-scroll")
            assert table.evaluate("e => getComputedStyle(e).overflowX") in ("auto", "scroll")
    if name == "examples/vertigo-admin.html" and viewport == 1280:
        def styles():
            return page.evaluate("""() => {
                const card = document.querySelector('.syn-vertigo-admin .card');
                const button = document.querySelector('.syn-vertigo-admin button');
                function themeColor(token) {
                    const probe = document.createElement('span');
                    probe.style.backgroundColor = 'var(' + token + ')';
                    document.body.appendChild(probe);
                    const value = getComputedStyle(probe).backgroundColor;
                    probe.remove();
                    return value;
                }
                return {
                    cardBackground: getComputedStyle(card).backgroundColor,
                    surface: themeColor('--syn-surface'),
                    buttonBackground: getComputedStyle(button).backgroundColor,
                    accent: themeColor('--syn-accent')
                };
            }""")
        studio = styles()
        assert studio["cardBackground"] == studio["surface"], studio
        assert studio["buttonBackground"] == studio["accent"], studio
        page.locator("body").evaluate("e => e.setAttribute('data-syn-theme', 'noir')")
        noir = styles()
        assert noir["cardBackground"] == noir["surface"], noir
        assert noir["buttonBackground"] == noir["accent"], noir
        assert noir["accent"] != studio["accent"], "theme override was ignored"
        # Negative control: removing the optional adapter must remove its paint.
        page.locator('link[href="../integrations/vertigo/admin.css"]').evaluate("e => e.remove()")
        without_adapter = styles()
        assert without_adapter["cardBackground"] != without_adapter["surface"], (
            "adapter has no observable opt-in behavior"
        )
    context.close()


def assert_visual_refinement(browser) -> None:
    """Verify interactive state and compact controls in each real rendering engine."""
    context = browser.new_context(viewport={"width": 900, "height": 700})
    try:
        page = context.new_page()
        css = (ROOT / "dist/syntyr.core.css").read_text()
        page.set_content(f"""<style>{css}</style>
        <main class="syn-root" data-syn-theme="studio">
          <label for="ordinary">Ordinary</label><input class="syn-input" id="ordinary">
          <label for="ordinary-choice">Choice</label>
          <select class="syn-select" id="ordinary-choice"><option>One</option></select>
          <div data-syn-density="compact">
            <label for="compact">Compact</label><input class="syn-input" id="compact">
            <label for="compact-choice">Choice</label>
            <select class="syn-select" id="compact-choice"><option>One</option></select>
          </div>
          <table role="grid" class="syn-table"><tbody>
            <tr id="chosen" aria-selected="true"><td>Chosen</td></tr>
            <tr id="available"><td>Available</td></tr>
          </tbody></table>
          <div class="syn-table-wrap" style="width:280px" role="region"
               aria-label="Responsive table demo" tabindex="0">
            <table class="syn-table" style="table-layout:fixed"><tbody>
              <tr><td id="prose">A longer descriptive message with several words must wrap in a compact cell.</td>
                  <td id="identifier" class="syn-cell--nowrap">NODE-ABC-129</td>
                  <td id="quantity" class="syn-cell--numeric">12,450</td></tr>
            </tbody></table>
          </div>
          <article id="custom-cut" class="syn-panel syn-panel--cut"
                   style="--syn-panel-cut-fill: #123456">Cut panel</article>
        </main>""")
        for ordinary, compact in (("ordinary", "compact"),
                                  ("ordinary-choice", "compact-choice")):
            large_height = page.locator(f"#{ordinary}").evaluate(
                "e => e.getBoundingClientRect().height")
            small_height = page.locator(f"#{compact}").evaluate(
                "e => e.getBoundingClientRect().height")
            assert small_height < large_height - 4, (
                "compact height unchanged", ordinary, large_height, small_height)
            assert small_height >= 36, ("compact target too small", compact, small_height)
        row = page.locator("#chosen")
        selected_background = row.evaluate("e => getComputedStyle(e).backgroundColor")
        row.hover()
        assert row.evaluate("e => getComputedStyle(e).backgroundColor") == selected_background, (
            "hover must preserve selected-row emphasis")
        other = page.locator("#available")
        other.hover()
        assert other.evaluate("e => getComputedStyle(e).backgroundColor") != selected_background, (
            "nonselected hover must not look selected")
        prose = page.locator("#prose")
        quantity = page.locator("#quantity")
        assert prose.evaluate("e => getComputedStyle(e).whiteSpace") == "normal"
        for cell in ("#identifier", "#quantity"):
            assert page.locator(cell).evaluate("e => getComputedStyle(e).whiteSpace") == "nowrap", cell
        line_rects = """e => {
            const range = document.createRange();
            range.selectNodeContents(e);
            return range.getClientRects().length;
        }"""
        assert prose.evaluate(line_rects) > quantity.evaluate(line_rects), (
            "prose must actually wrap in the narrow table")
        assert page.locator("#custom-cut").evaluate(
            "e => getComputedStyle(e, '::after').backgroundColor") == "rgb(18, 52, 86)", (
                "corner cut must use the underlying surface override")
    finally:
        context.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browsers", nargs="+",
                        choices=("chromium", "firefox", "webkit"),
                        default=("chromium", "firefox", "webkit"))
    args = parser.parse_args()
    with sync_playwright() as p:
        failed = 0
        for name in args.browsers:
            kwargs = {"headless": True}
            if name == "chromium":
                exe = (os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
                       or shutil.which("chromium") or shutil.which("chromium-browser"))
                if exe:
                    kwargs["executable_path"] = exe
                    kwargs["args"] = ["--no-sandbox"]
            if name == "webkit":
                # Opt-in path for a local compatible WebKit launcher, e.g. on
                # Linux distributions missing Playwright's bundled OS libraries.
                # The default Playwright-managed browser remains unchanged.
                custom_webkit = os.environ.get("SYNTYR_WEBKIT_EXECUTABLE")
                if custom_webkit:
                    kwargs["executable_path"] = custom_webkit
            try:
                browser = getattr(p, name).launch(**kwargs)
            except Exception as exc:
                failed += 1
                print(f"BLOCKED {name}: {str(exc).splitlines()[0]}", flush=True)
                continue
            try:
                for path in PAGES:
                    for width in (320, 390, 1280):
                        try:
                            assert_page(browser, path, width)
                        except Exception as exc:
                            raise AssertionError(f"{path} viewport {width}: {exc}") from exc
                assert_visual_refinement(browser)
                print(f"PASS {name}: {len(PAGES)} pages × 3 viewports + keyboard/popover and design-refinement checks",
                      flush=True)
            except Exception as exc:
                failed += 1
                print(f"FAIL {name}: {type(exc).__name__} {exc}", flush=True)
            finally:
                browser.close()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
