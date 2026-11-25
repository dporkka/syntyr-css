"""Opt-in Playwright browser smoke and interaction tests against real Chromium.

Run: python3 tests/browser_test.py
Browser infrastructure is developer-only, never a Syntyr runtime dependency.
"""
from pathlib import Path
import os
import shutil
import unittest

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
# Inlining local CSS avoids network/file:// navigation blocked by some hardened CI browsers.

class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = sync_playwright().start()
        kwargs = dict(headless=True)
        executable = (os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE')
                      or shutil.which('chromium')
                      or shutil.which('chromium-browser'))
        if executable:
            kwargs['executable_path'] = executable
            kwargs['args'] = ['--no-sandbox']
        cls.browser = cls.p.chromium.launch(**kwargs)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.p.stop()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 1280, 'height': 900}, device_scale_factor=1)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        html = (ROOT / 'docs/index.html').read_text(encoding='utf-8')
        css = (ROOT / 'dist/syntyr.all.css').read_text(encoding='utf-8')
        docs_css = (ROOT / 'docs/docs.css').read_text(encoding='utf-8')
        html = html.replace('<link rel="stylesheet" href="../dist/syntyr.all.css">', f'<style>{css}</style>')
        html = html.replace('<link rel="stylesheet" href="docs.css">', f'<style>{docs_css}</style>')
        self.page.set_content(html, wait_until='load')

    def tearDown(self):
        self.assertFalse(self.errors, self.errors)
        self.context.close()

    def test_theme_tokens_are_applied_and_nested(self):
        root = self.page.locator('body')
        grid = self.page.locator('#themes [data-syn-theme="grid"]')
        noir = self.page.locator('#themes [data-syn-theme="noir"]')
        self.assertEqual(root.evaluate("e => getComputedStyle(e).getPropertyValue('--syn-accent').trim()"), '#76e7f7')
        self.assertEqual(grid.evaluate("e => getComputedStyle(e).getPropertyValue('--syn-accent').trim()"), '#76e7f7')
        self.assertEqual(noir.evaluate("e => getComputedStyle(e).getPropertyValue('--syn-accent').trim()"), '#f1b574')
        self.assertEqual(grid.locator('.syn-panel').count(), 0) # this panel *is* the theme root

    def test_explicit_and_optional_css_never_escape_root(self):
        """CSS class names on a host page must not trigger Syntyr styling."""
        all_css = (ROOT / 'dist/syntyr.all.css').read_text(encoding='utf-8')
        self.page.set_content(f"""<style>{all_css}</style>
          <button id="host-button" class="syn-button">Host action</button>
          <article id="host-panel" class="syn-panel">Host article</article>
          <div id="host-shell" class="syn-app-shell">Unrelated grid</div>
          <section id="host-glow" class="syn-glow">Host glow</section>
          <div id="host-frame" class="syn-frame syn-frame--precision">Host frame</div>
          <section class="syn-root" data-syn-theme="studio">
            <button id="inside-button" class="syn-button syn-button--primary">Inside action</button>
            <article id="inside-panel" class="syn-panel">Inside article</article>
            <div id="inside-shell" class="syn-app-shell">Inside grid</div>
            <section id="inside-glow" class="syn-glow">Inside glow</section>
            <div id="inside-frame" class="syn-frame syn-frame--precision">Inside frame</div>
          </section>
          <article id="self-panel" class="syn-root syn-panel" data-syn-theme="studio">Root is panel</article>
          <section id="self-region" class="syn-root syn-region" data-syn-theme="studio">
            <div id="region-child" class="syn-stats"><article class="syn-stat">Stat</article></div>
          </section>""")
        get = lambda selector, prop: self.page.locator(selector).evaluate(
            "(e, p) => getComputedStyle(e).getPropertyValue(p).trim()", prop)
        self.assertNotEqual(get('#host-button', 'display'), 'inline-flex')
        self.assertNotEqual(get('#host-panel', 'position'), 'relative')
        self.assertNotEqual(get('#host-shell', 'display'), 'grid')
        self.assertEqual(get('#host-glow', 'box-shadow'), 'none')
        self.assertEqual(get('#host-frame', 'border-top-style'), 'none')
        self.assertEqual(get('#inside-button', 'display'), 'inline-flex')
        self.assertEqual(get('#inside-panel', 'position'), 'relative')
        self.assertEqual(get('#inside-shell', 'display'), 'grid')
        self.assertNotEqual(get('#inside-glow', 'box-shadow'), 'none')
        self.assertNotEqual(self.page.locator('#inside-frame').evaluate(
            "e => getComputedStyle(e, '::before').content"), 'none')
        self.assertEqual(get('#self-panel', 'position'), 'relative')
        self.assertEqual(get('#self-region', 'container-name'), 'syn-region')

    def test_explicit_checkbox_and_radio_are_at_least_24_css_pixels(self):
        core = (ROOT / 'dist/syntyr.core.css').read_text(encoding='utf-8')
        self.page.set_content(f"""<style>{core}</style>
          <main class="syn-root" data-syn-theme="studio">
            <label class="syn-check"><input id="box" class="syn-input" type="checkbox"> Checkbox</label>
            <label class="syn-check"><input id="radio" class="syn-input" type="radio"> Radio</label>
            <section data-syn-density="compact">
              <label class="syn-check"><input id="compact-box" class="syn-input" type="checkbox"> Compact</label>
            </section>
          </main>""")
        for control in ('box', 'radio', 'compact-box'):
            with self.subTest(control=control):
                size = self.page.locator('#' + control).bounding_box()
                self.assertGreaterEqual(size['width'], 24)
                self.assertGreaterEqual(size['height'], 24)

    def test_semantic_mode_is_scoped_and_styled(self):
        semantic_button = self.page.locator('#semantic .syn-semantic button')
        self.assertEqual(semantic_button.count(), 1)
        self.assertEqual(semantic_button.evaluate('e => getComputedStyle(e).minHeight'), '44px')
        semantic_article = self.page.locator('#semantic .syn-semantic article')
        self.assertEqual(semantic_article.evaluate('e => getComputedStyle(e).backgroundColor'), 'rgb(17, 31, 44)')
        self.page.evaluate("""() => {
          const b = document.createElement('button');
          b.id = 'unstyled-external';
          b.textContent = 'Outside';
          document.body.appendChild(b);
        }""")
        external = self.page.locator('#unstyled-external')
        self.assertNotEqual(external.evaluate('e => getComputedStyle(e).minHeight'), '44px')

    def test_semantic_optin_survives_ephemeral_host_classes(self):
        """An HTMX/Alpine class toggle must not drop semantic styles."""
        core = (ROOT / 'dist/syntyr.core.css').read_text(encoding='utf-8')
        semantic = (ROOT / 'dist/syntyr.semantic.css').read_text(encoding='utf-8')
        self.page.set_content(f"""<style>{core}</style><style>{semantic}</style>
          <section class="syn-root syn-semantic" data-syn-theme="grid">
            <button id="stable" data-syn-semantic type="button">Search</button>
            <button id="unstyled-host" class="framework-control">Other library</button>
            <input id="field" data-syn-semantic aria-invalid="true" value="broken">
            <button id="class-free">Class free</button>
          </section>
          <button id="outside" data-syn-semantic class="htmx-request">Outside</button>""")
        stable = self.page.locator('#stable')
        measure = lambda el: el.evaluate("""e => ({
          height: getComputedStyle(e).minHeight,
          background: getComputedStyle(e).backgroundColor,
          color: getComputedStyle(e).color,
        })""")
        before = measure(stable)
        self.assertEqual(before['height'], '44px')
        stable.evaluate("e => e.classList.add('htmx-request', 'htmx-swapping')")
        self.assertEqual(measure(stable), before)
        self.assertEqual(self.page.locator('#field').evaluate(
            'e => getComputedStyle(e).borderTopColor'), 'rgb(255, 170, 164)')
        self.page.locator('#field').evaluate("e => e.classList.add('htmx-request')")
        self.assertEqual(self.page.locator('#field').evaluate(
            'e => getComputedStyle(e).borderTopColor'), 'rgb(255, 170, 164)')
        self.assertNotEqual(measure(self.page.locator('#unstyled-host'))['height'], '44px')
        self.assertNotEqual(measure(self.page.locator('#outside'))['height'], '44px')
        self.assertEqual(measure(self.page.locator('#class-free'))['height'], '44px')

    def test_opt_in_surface_polish_is_theme_aware_and_accessible(self):
        core = (ROOT / 'dist/syntyr.core.css').read_text(encoding='utf-8')
        recipes = (ROOT / 'dist/syntyr.recipes.css').read_text(encoding='utf-8')
        self.page.set_content(f"""<style>{core}</style><style>{recipes}</style>
          <section class="syn-root" data-syn-theme="noir">
            <article id="polish" class="syn-app-card syn-surface--accent syn-surface--lift">
              <label for="polish-input">Search</label>
              <input id="polish-input" class="syn-input">
            </article>
            <article id="plain" class="syn-app-card">Plain</article>
          </section>""")
        accent = self.page.locator('#polish')
        plain = self.page.locator('#plain')
        before = accent.evaluate("e => getComputedStyle(e).boxShadow")
        self.assertIn("241, 181, 116", before)
        # Newer neutral cards have a subtle default shadow; the accent treatment
        # must remain opt-in and visibly distinct from that baseline.
        plain_shadow = plain.evaluate('e => getComputedStyle(e).boxShadow')
        self.assertNotEqual(plain_shadow, before)
        self.assertNotIn("241, 181, 116", plain_shadow)
        self.page.emulate_media(reduced_motion='reduce')
        accent.locator('input').focus()
        focused_border = accent.evaluate('e => getComputedStyle(e).borderTopColor')
        self.assertEqual(focused_border, 'rgb(241, 181, 116)')
        self.assertIn("241, 181, 116", accent.evaluate("e => getComputedStyle(e).boxShadow"))
        self.page.emulate_media(reduced_motion='reduce')
        self.assertIn(accent.evaluate("e => getComputedStyle(e).transitionDuration"), ("0s", "0s, 0s"))
        self.page.emulate_media(forced_colors='active')
        self.assertEqual(accent.evaluate("e => getComputedStyle(e).boxShadow"), "none")
        self.assertEqual(accent.evaluate("e => getComputedStyle(e).borderTopWidth"), "3px")

    def test_optional_content_visibility_respects_print_media(self):
        core = (ROOT / 'dist/syntyr.core.css').read_text(encoding='utf-8')
        recipes = (ROOT / 'dist/syntyr.recipes.css').read_text(encoding='utf-8')
        self.page.set_content(f"""<style>{core}</style><style>{recipes}</style>
          <main class="syn-root">
            <div id="deferred" class="syn-defer-section" style="--syn-defer-size: 25rem">
              <p>Long below-fold section</p>
            </div>
          </main>""")
        section = self.page.locator('#deferred')
        self.assertEqual(section.evaluate("e => getComputedStyle(e).contentVisibility"), "auto")
        self.assertIn("400px", section.evaluate("e => getComputedStyle(e).containIntrinsicSize"))
        self.page.emulate_media(media="print")
        self.assertEqual(section.evaluate("e => getComputedStyle(e).contentVisibility"), "visible")

    def test_semantic_mode_leaves_range_input_native(self):
        self.page.evaluate("""() => {
          const range = document.createElement('input');
          range.id = 'range-audit';
          range.type = 'range';
          document.querySelector('.syn-semantic article').appendChild(range);
        }""")
        range_border = self.page.locator('#range-audit').evaluate('e => getComputedStyle(e).borderTopWidth')
        self.assertEqual(range_border, '0px')

    def test_nested_themes_and_compact_density_render_independently(self):
        self.page.evaluate("""() => {
            const region = document.createElement('section');
            region.className = 'syn-root';
            region.setAttribute('data-syn-theme', 'studio');
            region.innerHTML = `
                <button id="comfortable" class="syn-button">Comfortable</button>
                <div id="compact" data-syn-density="compact">
                  <button id="compact-button" class="syn-button">Compact</button>
                </div>
                <section id="grid-nested" data-syn-theme="grid">
                  <button id="grid-button" class="syn-button">Telemetry</button>
                </section>`;
            document.body.appendChild(region);
        }""")
        normal_height = self.page.locator("#comfortable").evaluate(
            "e => getComputedStyle(e).minHeight")
        compact_height = self.page.locator("#compact-button").evaluate(
            "e => getComputedStyle(e).minHeight")
        self.assertEqual(normal_height, "44px")
        self.assertEqual(compact_height, "36px")
        studio_font = self.page.locator("#comfortable").evaluate(
            "e => getComputedStyle(e).fontFamily")
        grid_font = self.page.locator("#grid-button").evaluate(
            "e => getComputedStyle(e).fontFamily")
        self.assertNotEqual(studio_font, grid_font)
        self.assertIn("mono", grid_font.lower())
        surface_light = self.page.locator("#comfortable").evaluate(
            "e => getComputedStyle(e.parentElement).getPropertyValue('--syn-surface-recessed').trim()")
        surface_dark = self.page.locator("#grid-nested").evaluate(
            "e => getComputedStyle(e).getPropertyValue('--syn-surface-recessed').trim()")
        self.assertNotEqual(surface_light, surface_dark)

    def test_selected_table_row_retains_state_on_hover(self):
        css = (ROOT / "dist/syntyr.core.css").read_text()
        self.page.set_content(f"""<style>{css}</style>
        <section class="syn-root" data-syn-theme="studio">
          <table class="syn-table"><tbody>
            <tr data-syn-state="selected" id="selected"><td>Selected</td></tr>
            <tr id="other"><td>Other</td></tr>
          </tbody></table>
        </section>""")
        row = self.page.locator("#selected")
        base = row.evaluate("e => getComputedStyle(e).backgroundColor")
        row.hover()
        hover = row.evaluate("e => getComputedStyle(e).backgroundColor")
        self.assertEqual(hover, base, "Selection highlight must survive hover")
        self.page.locator("#other").hover()
        non_selected = self.page.locator("#other").evaluate(
            "e => getComputedStyle(e).backgroundColor")
        self.assertNotEqual(non_selected, base)

    def test_aria_selected_does_not_invent_selection_on_static_table(self):
        css = (ROOT / "dist/syntyr.core.css").read_text()
        self.page.set_content(f"""<style>{css}</style>
          <main class="syn-root" data-syn-theme="studio">
            <table class="syn-table"><tbody>
              <tr id="ordinary-aria" aria-selected="true"><td>Ordinary</td></tr>
              <tr id="ordinary-data" data-syn-state="selected"><td>Highlighted</td></tr>
            </tbody></table>
            <table role="grid" class="syn-table"><tbody>
              <tr id="grid-aria" aria-selected="true"><td>Grid row</td></tr>
            </tbody></table>
          </main>""")
        color = lambda selector: self.page.locator(selector).evaluate(
            "e => getComputedStyle(e).backgroundColor")
        self.assertNotEqual(color("#ordinary-aria"), color("#ordinary-data"))
        self.assertEqual(color("#grid-aria"), color("#ordinary-data"))
        ordinary = self.page.locator("#ordinary-aria")
        base = color("#ordinary-aria")
        ordinary.hover()
        self.assertNotEqual(color("#ordinary-aria"), base)

    def test_compact_density_shortens_actual_text_controls(self):
        css = (ROOT / "dist/syntyr.core.css").read_text()
        self.page.set_content(f"""<style>{css}</style>
        <section class="syn-root" data-syn-theme="studio">
          <label for="normal">Normal</label><input class="syn-input" id="normal">
          <label for="normal-select">Select</label>
          <select class="syn-select" id="normal-select"><option>One</option></select>
          <section data-syn-density="compact">
            <label for="compact">Compact</label><input class="syn-input" id="compact">
            <label for="compact-select">Select</label>
            <select class="syn-select" id="compact-select"><option>One</option></select>
          </section>
        </section>""")
        for normal_id, compact_id in (("normal", "compact"),
                                       ("normal-select", "compact-select")):
            with self.subTest(normal=normal_id, compact=compact_id):
                normal = self.page.locator(f"#{normal_id}").evaluate(
                    "e => e.getBoundingClientRect().height")
                compact = self.page.locator(f"#{compact_id}").evaluate(
                    "e => e.getBoundingClientRect().height")
                self.assertLess(compact, normal - 4,
                    "Compact density must affect measured height, not only min-height")
                self.assertGreaterEqual(compact, 36,
                    "Compact controls must retain a reasonable interactive target")

    def test_embedded_root_does_not_force_viewport_height(self):
        self.page.evaluate("""() => {
          const section = document.createElement('section');
          section.id = 'embedded-root';
          section.className = 'syn-root';
          section.innerHTML = '<span>Small widget</span>';
          document.body.appendChild(section);
        }""")
        min_height = self.page.locator('#embedded-root').evaluate('e => getComputedStyle(e).minHeight')
        self.assertNotEqual(min_height, '900px')

    def test_popover_opens_and_escape_dismisses(self):
        popover = self.page.locator('#command-popover')
        self.assertFalse(popover.evaluate('e => e.matches(":popover-open")'))
        self.page.get_by_role('button', name='OPEN COMMAND').click()
        self.assertTrue(popover.evaluate('e => e.matches(":popover-open")'))
        self.page.keyboard.press('Escape')
        self.assertFalse(popover.evaluate('e => e.matches(":popover-open")'))

    def test_invoker_dialog_opens_and_closes(self):
        dialog = self.page.locator('#diagnostic-dialog')
        self.page.get_by_role('button', name='OPEN DIALOG').click()
        self.assertTrue(dialog.evaluate('e => e.open'))
        self.assertTrue(dialog.evaluate('e => e.matches(":modal")'))
        self.page.get_by_role('button', name='ACKNOWLEDGE').click()
        self.assertFalse(dialog.evaluate('e => e.open'))

    def test_disclosure_and_keyboard_focus(self):
        disclosure = self.page.locator('#components details').first
        self.assertFalse(disclosure.evaluate('e => e.open'))
        disclosure.locator('summary').click()
        self.assertTrue(disclosure.evaluate('e => e.open'))
        self.page.keyboard.press('Tab')
        # Focus styles should never be set to none by the framework.
        focus_color = self.page.locator(':focus').evaluate('e => getComputedStyle(e).outlineStyle')
        self.assertNotEqual(focus_color, 'none')

    def test_mobile_has_no_document_horizontal_overflow(self):
        self.page.set_viewport_size({'width': 375, 'height': 812})
        values = self.page.evaluate('() => ({sw:document.documentElement.scrollWidth, cw:document.documentElement.clientWidth})')
        self.assertLessEqual(values['sw'], values['cw'] + 1, values)

    def test_reduced_motion_disables_transitions(self):
        self.page.emulate_media(reduced_motion='reduce')
        duration = self.page.locator('.syn-button--primary').first.evaluate('e => getComputedStyle(e).transitionDuration')
        self.assertIn(duration, ('0s', '0s, 0s, 0s'), duration)

    def test_container_query_cards_adapt_to_parent_not_viewport(self):
        region = self.page.locator('#recipes .syn-region').first
        stats = region.locator('.syn-stats')
        def columns():
            return len(stats.evaluate('e => getComputedStyle(e).gridTemplateColumns').split())
        region.evaluate('e => e.style.width = "380px"')
        self.assertEqual(columns(), 1)
        region.evaluate('e => e.style.width = "550px"')
        self.assertEqual(columns(), 2)
        region.evaluate('e => e.style.width = "950px"')
        self.assertEqual(columns(), 3)

    def test_attribute_variants_preserve_semantics(self):
        self.page.emulate_media(reduced_motion='reduce')
        self.page.evaluate("""() => {
          const button = document.createElement('button');
          button.id = 'v03-state';
          button.className = 'syn-button';
          button.textContent = 'Toggle';
          document.querySelector('#recipes').appendChild(button);
        }""")
        b = self.page.locator('#v03-state')
        base = b.evaluate('e => getComputedStyle(e).color')
        b.evaluate('e => e.setAttribute("aria-pressed", "true")')
        pressed = b.evaluate('e => getComputedStyle(e).color')
        self.assertNotEqual(base, pressed)
        self.assertEqual(b.get_attribute('aria-pressed'), 'true')
        b.evaluate('e => e.setAttribute("aria-busy", "true")')
        self.assertEqual(b.evaluate('e => getComputedStyle(e).cursor'), 'progress')

    def test_unlayered_host_theme_overrides_token(self):
        self.page.add_style_tag(content='.syn-root[data-syn-theme="grid"] { --syn-accent: #99ffcc; }')
        self.assertEqual(self.page.locator('body').evaluate(
            'e => getComputedStyle(e).getPropertyValue("--syn-accent").trim()'), '#99ffcc')

    def test_noir_pricing_example_is_responsive_and_local(self):
        html = (ROOT / 'examples/pricing.html').read_text(encoding='utf-8')
        core = (ROOT / 'dist/syntyr.core.css').read_text(encoding='utf-8')
        effects = (ROOT / 'dist/syntyr.effects.css').read_text(encoding='utf-8')
        html = html.replace('<link rel="stylesheet" href="../dist/syntyr.core.css">', f'<style>{core}</style>')
        html = html.replace('<link rel="stylesheet" href="../dist/syntyr.effects.css">', f'<style>{effects}</style>')
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.page.set_content(html)
        pricing = self.page.locator('.syn-pricing')
        self.assertEqual(len(pricing.evaluate('e => getComputedStyle(e).gridTemplateColumns').split()), 1)
        self.assertLessEqual(self.page.evaluate('document.documentElement.scrollWidth'), 391)
        self.page.set_viewport_size({'width': 1280, 'height': 900})
        self.assertEqual(len(pricing.evaluate('e => getComputedStyle(e).gridTemplateColumns').split()), 3)
        self.assertEqual(self.page.locator('.syn-price-card').count(), 3)

    def test_forced_colors_still_has_visible_control_border(self):
        self.page.emulate_media(forced_colors='active')
        color = self.page.get_by_role('button', name='OPEN COMMAND').evaluate('e => getComputedStyle(e).borderTopStyle')
        self.assertEqual(color, 'solid')

    def test_studio_theme_is_scoped_and_uses_light_controls(self):
        studio = self.page.locator('#themes [data-syn-theme="studio"]')
        self.assertEqual(studio.count(), 1)
        self.assertEqual(studio.evaluate(
            "e => getComputedStyle(e).getPropertyValue('--syn-accent').trim()"), '#2458c6')
        self.assertEqual(studio.evaluate("e => getComputedStyle(e).colorScheme"), 'light')
        self.assertEqual(self.page.locator('body').evaluate(
            "e => getComputedStyle(e).colorScheme"), 'dark')

    def test_nested_studio_recipe_surfaces_have_matching_foreground_and_background(self):
        core = (ROOT / "dist/syntyr.core.css").read_text()
        recipes = (ROOT / "dist/syntyr.recipes.css").read_text()
        self.page.set_content(f"""<style>{core}{recipes}</style>
        <main class="syn-root" data-syn-theme="grid">
            <section data-syn-theme="studio">
                <aside class="syn-app-rail" id="nested-rail">Studio rail</aside>
                <article class="syn-app-card" id="nested-card">Studio card</article>
                <section class="syn-site-hero" id="nested-hero">Studio hero</section>
                <section class="syn-feature-card" id="nested-feature">Studio feature</section>
            </section>
        </main>""")
        for selector in ("#nested-rail", "#nested-card", "#nested-hero", "#nested-feature"):
            with self.subTest(selector=selector):
                computed = self.page.locator(selector).evaluate(
                    "e => ({fg: getComputedStyle(e).color, bg: getComputedStyle(e).backgroundColor})")
                self.assertEqual(computed["fg"], "rgb(21, 35, 58)")
                if selector == "#nested-rail":
                    # Navigation recedes from the pure-white working surface.
                    self.assertNotEqual(computed["bg"], "rgb(255, 255, 255)")
                    self.assertNotEqual(computed["bg"], "rgba(0, 0, 0, 0)")
                else:
                    self.assertEqual(computed["bg"], "rgb(255, 255, 255)")

    def test_new_recipes_have_no_mobile_overflow_and_work_at_desktop_width(self):
        core = (ROOT / 'dist/syntyr.core.css').read_text()
        recipes = (ROOT / 'dist/syntyr.recipes.css').read_text()
        for example in ('saas.html', 'business.html', 'terminal.html'):
            with self.subTest(example=example):
                html = (ROOT / 'examples' / example).read_text()
                html = html.replace('<link rel="stylesheet" href="../dist/syntyr.core.css">',
                                    f'<style>{core}</style>')
                html = html.replace('<link rel="stylesheet" href="../dist/syntyr.recipes.css">',
                                    f'<style>{recipes}</style>')
                for width in (360, 1280):
                    with self.subTest(width=width):
                        self.page.set_viewport_size({'width': width, 'height': 900})
                        self.page.set_content(html)
                        metrics = self.page.evaluate(
                            "() => ({scrollWidth: document.documentElement.scrollWidth, "
                            "clientWidth: document.documentElement.clientWidth})")
                        self.assertLessEqual(metrics['scrollWidth'],
                                             metrics['clientWidth'] + 1, metrics)
                        self.assertEqual(self.page.locator('main').count(), 1)
                if example == 'saas.html':
                    self.assertEqual(self.page.locator('.syn-app-shell').count(), 1)
                    self.assertEqual(self.page.locator('.syn-table .syn-status').count(), 3)
                if example == 'business.html':
                    self.assertGreater(
                        self.page.locator('.business-visual').bounding_box()['x'], 600)
                if example == 'terminal.html':
                    self.assertEqual(self.page.locator('.syn-terminal').evaluate(
                        'e => getComputedStyle(e).backgroundColor'), 'rgb(11, 22, 37)')
                    positions = self.page.locator('.syn-terminal-line').evaluate_all(
                        'els => els.map(e => e.getBoundingClientRect().top)')
                    self.assertLessEqual(positions[1] - positions[0], 30)
                    studio_chip = self.page.locator('.cli-options [data-syn-theme="studio"]')
                    self.assertEqual(studio_chip.evaluate(
                        'e => getComputedStyle(e).backgroundColor'), 'rgb(255, 255, 255)')



    def test_progressive_semantic_styles_do_not_escape_syn_root(self):
        core = (ROOT / 'dist/syntyr.core.css').read_text()
        semantic = (ROOT / 'dist/syntyr.semantic.css').read_text()
        self.page.set_content(f"""<style>{core}</style><style>{semantic}</style>
          <section class="syn-semantic" style="--syn-control-height:2.75rem">
            <button id="outside" data-syn-semantic>Outside</button>
          </section>
          <section class="syn-root syn-semantic" data-syn-theme="grid">
            <button id="inside" data-syn-semantic>Inside</button>
          </section>""")
        get_height = lambda selector: self.page.locator(selector).evaluate(
            "e => getComputedStyle(e).minHeight")
        self.assertEqual(get_height('#inside'), '44px')
        self.assertNotEqual(get_height('#outside'), '44px')

    def test_progressive_auto_theme_honors_system_and_nested_explicit_palettes(self):
        core = (ROOT / 'dist/syntyr.core.css').read_text()
        self.page.set_content(f"""<style>{core}</style>
          <main class="syn-root" id="auto-root" data-syn-theme="auto">
            <section id="explicit-noir" data-syn-theme="noir">
              <article id="nested-auto" data-syn-theme="auto">Nested</article>
            </section>
          </main>""")
        accent = lambda ident: self.page.locator(ident).evaluate("""e => {
            const probe = document.createElement('span');
            probe.style.color = 'var(--syn-accent)';
            e.append(probe);
            const resolved = getComputedStyle(probe).color;
            probe.remove();
            return resolved;
        }""")
        self.page.emulate_media(color_scheme='light')
        self.assertEqual(accent('#auto-root'), 'rgb(36, 88, 198)')
        self.assertEqual(accent('#explicit-noir'), 'rgb(241, 181, 116)')
        self.assertEqual(accent('#nested-auto'), 'rgb(36, 88, 198)')
        self.page.emulate_media(color_scheme='dark')
        self.assertEqual(accent('#auto-root'), 'rgb(118, 231, 247)')
        self.assertEqual(accent('#explicit-noir'), 'rgb(241, 181, 116)')
        self.assertEqual(accent('#nested-auto'), 'rgb(118, 231, 247)')

    def test_progressive_intrinsic_layout_follows_embedding_width(self):
        core = (ROOT / 'dist/syntyr.core.css').read_text()
        self.page.set_content(f"""<style>{core}</style>
          <main class="syn-root" data-syn-theme="studio">
            <section id="host" style="width: 310px; max-width: 100%">
              <div class="syn-layout">
                <article id="first">First region</article>
                <article id="second">Second region</article>
              </div>
            </section>
          </main>""")
        coord = lambda selector: self.page.locator(selector).bounding_box()
        self.assertGreater(coord('#second')['y'], coord('#first')['y'])
        self.page.locator('#host').evaluate("e => e.style.width = '900px'")
        self.assertAlmostEqual(coord('#second')['y'], coord('#first')['y'], delta=1)
        self.assertGreater(coord('#second')['x'], coord('#first')['x'])

    def test_progressive_print_styles_keep_data_readable(self):
        core = (ROOT / 'dist/syntyr.core.css').read_text()
        print_css = (ROOT / 'dist/syntyr.print.css').read_text()
        self.page.set_content(f"""<style>{core}</style><style>{print_css}</style>
          <main class="syn-root" id="page" data-syn-theme="noir">
            <nav class="syn-app-nav" id="nav"><a href="#">Navigation</a></nav>
            <section class="syn-table-wrap" id="table">
              <table><tr><td id="data">Invoice row</td></tr></table>
            </section>
            <button id="action" class="syn-button syn-button--primary">Export</button>
          </main>""")
        self.page.emulate_media(media='print')
        css = lambda selector, prop: self.page.locator(selector).evaluate(
            "(e, p) => getComputedStyle(e).getPropertyValue(p).trim()", prop)
        self.assertEqual(css('#page', 'background-color'), 'rgb(255, 255, 255)')
        self.assertEqual(css('#page', 'color'), 'rgb(17, 17, 17)')
        self.assertEqual(css('#nav', 'display'), 'none')
        self.assertEqual(css('#table', 'overflow-x'), 'visible')
        self.assertEqual(css('#data', 'visibility'), 'visible')
        self.assertEqual(css('#action', 'color'), 'rgb(17, 17, 17)')


    def test_neutral_first_palette_tables_and_opt_in_cinematic_styling(self):
        core = (ROOT / 'dist/syntyr.core.css').read_text(encoding='utf-8')
        recipes = (ROOT / 'dist/syntyr.recipes.css').read_text(encoding='utf-8')
        self.page.set_content(f"""<style>{core}</style><style>{recipes}</style>
          <main class="syn-root" id="default">
            <h2 class="syn-section-heading" id="section-title">Customer records</h2>
            <h3 class="syn-heading" id="card-title">Overview</h3>
            <section class="syn-stage" id="stage">Neutral stage</section>
            <article class="syn-panel" id="panel">
              <span class="syn-badge" id="badge">Draft</span>
            </article>
            <table class="syn-table"><tbody>
              <tr id="row" data-syn-state="selected"><th scope="row">Selected</th>
                <td class="syn-cell--wrap" id="wrap">This description should wrap across multiple lines when needed.</td>
                <td class="syn-cell--numeric" id="numeric">1,250</td>
              </tr>
            </tbody></table>
            <section id="technical" data-syn-theme="grid">
              <article id="accent-card" class="syn-app-card syn-surface--accent">
                <span id="accent-badge" class="syn-badge syn-badge--accent">Active</span>
              </article>
            </section>
          </main>""")
        style = lambda sel, prop: self.page.locator(sel).evaluate(
            "(e, property) => getComputedStyle(e).getPropertyValue(property).trim()", prop)
        self.assertEqual(style('#default', 'background-color'), 'rgb(245, 247, 251)')
        self.assertEqual(style('#technical', 'background-color'), 'rgb(8, 15, 25)')
        self.assertNotIn('mono', style('#default', 'font-family').lower())
        self.assertGreater(float(style('#section-title', 'font-size').removesuffix('px')),
                           float(style('#card-title', 'font-size').removesuffix('px')))
        self.assertEqual(style('#panel', 'background-image'), 'none')
        self.assertEqual(style('#stage', 'background-image'), 'none')
        self.assertEqual(self.page.locator('#badge').evaluate(
            "e => getComputedStyle(e, '::before').content"), 'none')
        self.assertEqual(style('#wrap', 'white-space'), 'normal')
        self.assertEqual(style('#numeric', 'white-space'), 'nowrap')
        self.assertEqual(style('#numeric', 'text-align'), 'right')
        self.assertEqual(style('#row > :first-child', 'border-inline-start-width'), '3px')
        self.assertEqual(style('#row > :first-child', 'border-inline-start-color'),
                         'rgb(36, 88, 198)')
        self.assertNotEqual(style('#accent-card', 'background-image'), 'none')
        self.assertEqual(style('#accent-badge', 'color'), 'rgb(118, 231, 247)')
        self.page.locator('#row').hover()
        self.assertEqual(style('#row > :first-child', 'border-inline-start-width'), '3px')
        self.page.emulate_media(forced_colors='active')
        self.assertNotEqual(style('#row > :first-child', 'border-inline-start-color'),
                            'rgb(36, 88, 198)')

if __name__ == '__main__':
    unittest.main(verbosity=2)
