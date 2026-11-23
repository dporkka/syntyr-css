"""Optional browser contract for the docs-only palette editor.

Run with the developer-only Playwright dependency:
  uv run --no-project --with playwright==1.64.1 python tests/theme_editor_browser.py
"""
from pathlib import Path
import os
import shutil

ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / 'docs/theme-editor.html').as_uri()


def chromium_launch_options():
    opts = {"headless": True}
    executable = (os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
                  or shutil.which("chromium")
                  or shutil.which("chromium-browser"))
    if executable:
        opts.update(executable_path=executable, args=["--no-sandbox"])
    return opts


def check(browser, viewport):
    context = browser.new_context(viewport={'width': viewport, 'height': 800})
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(URL)
    preview = page.locator('#preview')
    assert page.locator('script').count() == 1
    assert preview.get_attribute('data-syn-theme') == 'grid'
    assert preview.get_attribute('data-syn-intensity') == 'standard'
    feature_card = preview.locator('.syn-glow')
    default_shadow = feature_card.evaluate("e => getComputedStyle(e).boxShadow")
    page.locator('#intensity').select_option('quiet')
    assert preview.get_attribute('data-syn-intensity') == 'quiet'
    quiet_shadow = feature_card.evaluate("e => getComputedStyle(e).boxShadow")
    assert default_shadow != quiet_shadow, (default_shadow, quiet_shadow)
    page.locator('#intensity').select_option('cinematic')
    assert preview.get_attribute('data-syn-intensity') == 'cinematic'
    assert 'data-syn-intensity="cinematic"' in page.locator('#generated-css').inner_text()
    page.locator('#intensity').select_option('standard')
    assert page.locator('#accent').input_value() == '#76e7f7'
    assert page.locator('#contrast-result').get_attribute('data-result') == 'pass'
    assert '--syn-accent: #76e7f7' in page.locator('#generated-css').inner_text()

    for variant in ('grid', 'noir', 'studio', 'industrial', 'terminal', 'corporate', 'minimal'):
        page.locator('#theme').select_option(variant)
        assert preview.get_attribute('data-syn-theme') == variant
        assert page.locator('#contrast-result').get_attribute('data-result') == 'pass'

    # The full-page sample must apply typography, rhythm and semantic colors.
    page.locator('#theme').select_option('grid')
    assert page.locator('#surface').input_value() == '#111f2c'
    assert page.locator('#body-text').input_value() == '#edf9ff'
    page.locator('#typography').select_option('editorial')
    page.locator('#spacing').select_option('airy')
    assert 'Georgia' in preview.locator('.syn-heading').first.evaluate(
        "e => getComputedStyle(e).fontFamily")
    assert preview.evaluate("e => getComputedStyle(e).getPropertyValue('--syn-space-3').trim()") == '1.5rem'
    preset = page.locator('#generated-preset').inner_text()
    assert '"typography": "editorial"' in preset
    assert '"spacing": "airy"' in preset
    assert '--syn-space-3: 1.5rem' in page.locator('#generated-css').inner_text()
    page.locator('#body-text').fill('#111f2c')
    assert page.locator('#contrast-surface-result').get_attribute('data-result') == 'fail'
    page.locator('#page-bg').fill('#111f2c')
    assert page.locator('#contrast-background-result').get_attribute('data-result') == 'fail'
    page.locator('#reset-theme').click()
    assert page.locator('#contrast-surface-result').get_attribute('data-result') == 'pass'
    assert page.locator('#typography').input_value() == 'editorial'
    assert page.locator('#spacing').input_value() == 'airy'

    page.locator('#theme').select_option('noir')
    assert preview.get_attribute('data-syn-theme') == 'noir'
    assert page.locator('#accent').input_value() == '#f1b574'
    assert page.locator('#on-accent').input_value() == '#1c100b'

    # Changing accent must also update the derived soft background tint.
    original_soft = preview.evaluate("e => getComputedStyle(e).getPropertyValue('--syn-accent-soft').trim()")
    page.locator('#accent').fill('#00ff00')
    updated_soft = preview.evaluate("e => getComputedStyle(e).getPropertyValue('--syn-accent-soft').trim()")
    assert updated_soft != original_soft, (original_soft, updated_soft)
    assert '.syn-root [data-syn-theme="noir"]' in page.locator('#generated-css').inner_text()

    # Apply the generated CSS as a host would. It must theme nested scopes.
    css = page.locator('#generated-css').inner_text()
    override = page.add_style_tag(content=css)
    preview.evaluate("e => e.style.removeProperty('--syn-accent')")
    assert preview.evaluate("e => getComputedStyle(e).getPropertyValue('--syn-accent').trim()") == '#00ff00'
    override.evaluate("e => e.remove()")
    preview.evaluate("e => e.style.setProperty('--syn-accent', '#00ff00')")

    page.locator('#accent').fill('#ffffff')
    page.locator('#on-accent').fill('#ffffff')
    assert page.locator('#contrast-result').get_attribute('data-result') == 'fail'
    assert '1.00:1' in page.locator('#contrast-result').inner_text()
    assert '--syn-accent: #ffffff' in page.locator('#generated-css').inner_text()
    assert page.locator('body').evaluate("e => getComputedStyle(e).getPropertyValue('--syn-accent').trim()") == '#2458c6'

    page.locator('#reset-theme').click()
    assert page.locator('#contrast-result').get_attribute('data-result') == 'pass'
    assert page.locator('#accent').input_value() == '#f1b574'
    overflow = page.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')
    assert overflow <= 1, (viewport, overflow)
    assert not errors, errors
    context.close()


if __name__ == '__main__':
    from playwright.sync_api import sync_playwright  # dev-only
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(**chromium_launch_options())
        for width in (320, 390, 1280):
            check(browser, width)
        browser.close()
    print('PASS theme editor: 3 viewports, theme switching, contrast failures, reset, scoped overrides')
