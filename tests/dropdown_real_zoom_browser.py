"""Opt-in X11 browser-UI zoom regression (not a screen-reader certification).

Requires Playwright Python, headed browsers, DISPLAY and xdotool.
Run under a virtual display: xvfb-run -a python tests/dropdown_real_zoom_browser.py
WebKit MiniBrowser is checked against a 640px CSS-viewport threshold;
its zoom steps can overshoot the nominal 200% target and did not reach the
320px threshold. This is not a precise 200%/400% measurement or Safari
assistive-technology certification.
"""
from pathlib import Path
from subprocess import run
from shutil import which
from playwright.sync_api import sync_playwright

EXAMPLE = (Path(__file__).resolve().parents[1] / 'examples/dropdowns.html').as_uri()


def os_key(*args):
    result = run(['xdotool', *args], capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(f'xdotool {args!r}: {result.stderr.strip()}')
    return result.stdout.strip()


def app_window():
    windows = os_key('search', '--onlyvisible', '--name', '.').splitlines()
    windows = [wid for wid in windows if 'Syntyr' in os_key('getwindowname', wid)]
    assert len(windows) == 1, f'Expected one Syntyr browser window: {windows!r}'
    return windows[0]


def check_popover(page, engine, zoom):
    button = page.locator('#actions-trigger')
    button.focus()  # Scroll a deep trigger into the reduced-height viewport.
    assert page.evaluate('document.activeElement.id') == 'actions-trigger'
    page.keyboard.press('Enter')
    popover = page.locator('#actions-panel')
    assert popover.evaluate('e => e.matches(":popover-open")'), (engine, zoom)
    bounds = popover.bounding_box()
    viewport = page.evaluate('({width: innerWidth, height: innerHeight})')
    assert bounds and bounds['x'] >= -1 and bounds['x'] + bounds['width'] <= viewport['width'] + 1, (
        engine, zoom, bounds, viewport)
    assert bounds['y'] >= -1 and bounds['y'] + bounds['height'] <= viewport['height'] + 1, (
        engine, zoom, bounds, viewport)
    assert page.evaluate(
        'document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1'
    ), (engine, zoom, 'horizontal page overflow')
    page.keyboard.press('Escape')
    assert not popover.evaluate('e => e.matches(":popover-open")'), (engine, zoom)


def main():
    if not which('xdotool'):
        raise SystemExit('Install xdotool for this opt-in browser-UI zoom test.')
    with sync_playwright() as p:
        for name in ('chromium', 'firefox', 'webkit'):
            browser = getattr(p, name).launch(headless=False)
            try:
                page = browser.new_page(viewport={'width': 1280, 'height': 800})
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(EXAMPLE)
                assert page.evaluate('innerWidth') == 1280
                assert page.evaluate('parseFloat(getComputedStyle(document.documentElement).fontSize)') == 16
                win = app_window()
                os_key('windowfocus', win)
                # These are browser-UI keyboard shortcuts, not DOM CSS zoom.
                # Different engines use different zoom step sizes.
                targets = ((200, 640),) if name == 'webkit' else ((200, 640), (400, 320))
                steps = 0
                for zoom, target in targets:
                    while page.evaluate('innerWidth') > target and steps < 24:
                        os_key('key', '--window', win, 'ctrl+plus')
                        page.wait_for_timeout(120)
                        steps += 1
                    width = page.evaluate('innerWidth')
                    assert width <= target, (name, zoom, width)
                    check_popover(page, name, zoom)
                    print(
                        f'PASS {name}: measured CSS viewport {width}px <= {target}px '
                        f'(nominal {zoom}% target; browser zoom steps may overshoot)',
                        flush=True,
                    )
                assert not errors, (name, errors)
            finally:
                browser.close()


if __name__ == '__main__':
    main()
