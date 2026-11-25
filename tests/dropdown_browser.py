"""Real Chromium/Firefox/WebKit checks for scriptless and opt-in dropdowns.
Developer-only: run inside pinned Playwright Python container.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{server.server_port}/examples/dropdowns.html'
    try:
        with sync_playwright() as playwright:
            for name in ('chromium', 'firefox', 'webkit'):
                browser = getattr(playwright, name).launch()
                try:
                    for width in (320, 1280):
                        context = browser.new_context(viewport={'width': width, 'height': 800})
                        page = context.new_page()
                        errors = []
                        page.on('pageerror', lambda e: errors.append(str(e)))
                        page.goto(url)
                        assert page.locator('script').count() == 0
                        button = page.get_by_role('button', name='Record actions')
                        button.click()
                        popover = page.locator('#actions-panel')
                        assert popover.evaluate('e => e.matches(":popover-open")')
                        assert popover.get_attribute('role') == 'group'
                        bounds = popover.bounding_box()
                        assert bounds['x'] >= -1 and bounds['x'] + bounds['width'] <= width + 1, (name, width, bounds)
                        height = popover.locator('.syn-dropdown__item').first.evaluate('e => e.getBoundingClientRect().height')
                        assert height >= 44, (name, height)
                        page.keyboard.press('Escape')
                        assert not popover.evaluate('e => e.matches(":popover-open")')
                        page.locator('#demo-theme').select_option('noir')
                        assert page.locator('#demo-theme').input_value() == 'noir'
                        assert not errors, (name, errors)
                        context.close()

                    # This is 400% *text enlargement* at a 320px CSS viewport,
                    # not browser chrome zoom; both cases must be tested separately.
                    context = browser.new_context(viewport={'width': 320, 'height': 800}, reduced_motion='reduce')
                    page = context.new_page()
                    errors = []
                    page.on('pageerror', lambda e: errors.append(str(e)))
                    page.goto(url)
                    page.evaluate("document.documentElement.style.fontSize = '400%'")
                    assert page.evaluate('parseFloat(getComputedStyle(document.documentElement).fontSize)') >= 60
                    page.get_by_role('button', name='Record actions').click()
                    popover = page.locator('#actions-panel')
                    assert popover.evaluate('e => e.matches(":popover-open")')
                    panel = popover.bounding_box()
                    assert panel is not None and panel['x'] >= -1 and panel['x'] + panel['width'] <= 321, (name, panel)
                    for item in popover.locator('.syn-dropdown__item').all():
                        bounds = item.bounding_box()
                        assert bounds is not None and bounds['x'] >= -1 and bounds['x'] + bounds['width'] <= 321, (name, bounds)
                        assert item.evaluate('e => e.scrollWidth <= e.clientWidth + 1'), (name, item.text_content())
                    page.keyboard.press('Escape')
                    assert not popover.evaluate('e => e.matches(":popover-open")')
                    assert not errors, (name, errors)
                    context.close()

                    context = browser.new_context(viewport={'width': 390, 'height': 800})
                    page = context.new_page()
                    page.goto(url)
                    page.evaluate("""async () => {
                      const host = document.createElement('section');
                      host.innerHTML = `
                        <button id="enhanced-trigger" popovertarget="enhanced-panel">Editor actions</button>
                        <div id="enhanced-panel" popover data-syn-menu aria-label="Editor actions"
                             class="syn-popover syn-popover--anchored syn-dropdown">
                          <button type="button" data-syn-menu-item class="syn-dropdown__item">Rename</button>
                          <button type="button" data-syn-menu-item class="syn-dropdown__item">Duplicate</button>
                          <button type="button" data-syn-menu-item class="syn-dropdown__item" disabled>Archive</button>
                          <a href="#disallowed" aria-disabled="true" data-syn-menu-item class="syn-dropdown__item">Unavailable</a>
                        </div>
                      `;
                      document.querySelector('main').append(host);
                      const { enhanceMenu } = await import('/integrations/dropdown/menu.mjs');
                      window.disposeDropdown = enhanceMenu(document.querySelector('#enhanced-panel'));
                    }""")
                    trigger = page.locator('#enhanced-trigger')
                    menu = page.locator('#enhanced-panel')
                    assert menu.get_attribute('role') == 'menu'
                    assert trigger.get_attribute('aria-haspopup') == 'menu'
                    assert trigger.get_attribute('aria-controls') == 'enhanced-panel'
                    trigger.click()
                    page.wait_for_function('document.activeElement.textContent.trim() === "Rename"')
                    assert trigger.get_attribute('aria-expanded') == 'true'
                    page.keyboard.press('ArrowDown')
                    assert page.evaluate('document.activeElement.textContent.trim()') == 'Duplicate'
                    page.keyboard.press('ArrowDown')
                    assert page.evaluate('document.activeElement.textContent.trim()') == 'Rename'
                    page.keyboard.press('End')
                    assert page.evaluate('document.activeElement.textContent.trim()') == 'Duplicate'
                    page.keyboard.press('Home')
                    page.keyboard.press('d')
                    assert page.evaluate('document.activeElement.textContent.trim()') == 'Duplicate'
                    page.keyboard.press('Escape')
                    assert not menu.evaluate('e => e.matches(":popover-open")')
                    page.wait_for_function('document.querySelector("#enhanced-trigger").getAttribute("aria-expanded") === "false"')
                    trigger.click()
                    page.wait_for_function('document.activeElement.textContent.trim() === "Rename"')
                    page.get_by_role('menuitem', name='Duplicate').click()
                    assert not menu.evaluate('e => e.matches(":popover-open")')
                    page.evaluate('window.disposeDropdown()')
                    assert trigger.get_attribute('aria-haspopup') is None
                    assert trigger.get_attribute('aria-controls') is None
                    assert trigger.get_attribute('aria-expanded') is None
                    assert menu.get_attribute('role') is None
                    assert menu.locator('[data-syn-menu-item]').first.get_attribute('tabindex') is None
                    context.close()
                    print(f'PASS {name}: dropdown 320/1280, 400% root text stress and opt-in menu keyboard', flush=True)
                finally:
                    browser.close()
    finally:
        server.shutdown()
        server.server_close()

if __name__ == '__main__':
    main()
