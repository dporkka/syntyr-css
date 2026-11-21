"""Optional Chromium checks for the responsive two-row CSS-only logo marquee.

PYTHONPATH=/tmp/syntyr-icons-playwright python3 tests/logo_marquee_browser.py
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def require(truth, label):
    if not truth:
        raise AssertionError(label)


def metrics(page):
    return page.evaluate(r"""() => {
      const rows = [...document.querySelectorAll('.syn-logo-marquee__row')];
      return rows.map(row => {
        const track = row.querySelector('.syn-logo-marquee__track');
        const groups = [...track.querySelectorAll('.syn-logo-marquee__group')];
        const style = getComputedStyle(track);
        return {
          direction: row.dataset.synLogoDirection,
          duration: parseFloat(style.animationDuration),
          name: style.animationName,
          iterationCount: style.animationIterationCount,
          animationDirection: style.animationDirection,
          rowWidth: row.getBoundingClientRect().width,
          groupWidths: groups.map(group => group.getBoundingClientRect().width),
          trackWidth: track.getBoundingClientRect().width,
          copies: groups.map(group => ({
            hidden: group.getAttribute('aria-hidden'),
            inert: group.inert,
            display: getComputedStyle(group).display,
            text: group.textContent.trim().replace(/\s+/g, ' '),
          })),
        };
      });
    }""")


def originals_fit(row):
    return row.evaluate("""row => {
      const bounds = row.getBoundingClientRect();
      const logos = [...row.querySelector('.syn-logo-marquee__group').children];
      return logos.every(logo => {
        const box = logo.firstElementChild.getBoundingClientRect();
        return box.width > 0 && box.left >= bounds.left - 1 && box.right <= bounds.right + 1;
      });
    }""")


def main():
    server = ThreadingHTTPServer(
        ('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
    Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/examples/animation.html'
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                for width in (320, 390, 768, 1280, 1920):
                    page = browser.new_page(viewport={'width': width, 'height': 800})
                    page.goto(url)
                    rows = metrics(page)
                    require(len(rows) == 2, f'{width}: expected two logo rows')
                    for index, row in enumerate(rows):
                        require(row['direction'] == ('left' if index == 0 else 'right'),
                                f'{width}: opposite directions')
                        require(row['name'] == 'syn-logo-marquee-scroll',
                                f'{width}: animation not active: {row}')
                        require(row['iterationCount'] == 'infinite',
                                f'{width}: must repeat indefinitely')
                        require(row['animationDirection'] == ('normal' if index == 0 else 'reverse'),
                                f'{width}: incorrect travel direction {row}')
                        first, second = row['groupWidths']
                        require(abs(first-second) < 0.5,
                                f'{width}: repeating groups must match: {row}')
                        require(first >= row['rowWidth'] - 1,
                                f'{width}: too few logos to cover full visible row: {row}')
                        require(abs(row['trackWidth']-first-second) < 1,
                                f'{width}: track not exactly two groups')
                        require(row['copies'][1]['hidden'] == 'true' and row['copies'][1]['inert'],
                                f'{width}: duplicated logos must be inert/AT-hidden')
                        require(row['copies'][0]['text'] == row['copies'][1]['text'],
                                f'{width}: duplicate set must match first set')
                    require(page.evaluate(
                        "() => document.documentElement.scrollWidth <= innerWidth + 1"),
                        f'{width}: document overflowing horizontally')
                    page.close()

                page = browser.new_page(viewport={'width': 390, 'height': 800})
                page.goto(url)
                first = page.locator('.syn-logo-marquee__row').first
                track = first.locator('.syn-logo-marquee__track')
                # Check displacement is precisely one group width, not a visible jump.
                seam = track.evaluate("""node => {
                    const animation = node.getAnimations()[0];
                    animation.pause();
                    const duration = animation.effect.getTiming().duration;
                    animation.currentTime = 0;
                    const startX = node.getBoundingClientRect().x;
                    animation.currentTime = duration - 1;
                    const endX = node.getBoundingClientRect().x;
                    return {delta: startX - endX, groupWidth:
                        node.querySelector('.syn-logo-marquee__group').getBoundingClientRect().width};
                }""")
                require(abs(seam['delta'] - seam['groupWidth']) < 1,
                        f'loop must translate exactly one group: {seam}')
                first.hover()
                require(track.evaluate(
                    "node => getComputedStyle(node).animationPlayState") == 'paused',
                    'hover must pause logo marquee')
                page.locator('h1').hover()
                require(track.evaluate(
                    "node => getComputedStyle(node).animationPlayState") == 'running',
                    'mouseleave must resume logo marquee')
                # Tab from the preceding control to each named demo row.
                page.locator('#website-animation-controls button').last.focus()
                page.keyboard.press('Tab')
                require(page.get_by_role('group', name='Customer logos, row 1').evaluate(
                    'row => row === document.activeElement'), 'first row must be reachable by Tab')
                require(metrics(page)[0]['name'] == 'none' and
                        metrics(page)[0]['copies'][1]['display'] == 'none' and
                        metrics(page)[1]['name'] == 'syn-logo-marquee-scroll',
                        'only the focused row shows static originals')
                page.keyboard.press('Tab')
                require(page.get_by_role('group', name='Customer logos, row 2').evaluate(
                    'row => row === document.activeElement'), 'second row must be reachable by Tab')
                require(metrics(page)[0]['name'] == 'syn-logo-marquee-scroll',
                        'first row must animate again after focus leaves')

                # At the start of the loop the final original is clipped.
                # Keyboard navigation into that link must expose every original.
                first.evaluate("""row => {
                    const group = row.querySelector('.syn-logo-marquee__group');
                    for (const li of group.children) {
                        const link = document.createElement('a');
                        link.href = '#logo-marquee-title';
                        link.textContent = li.textContent;
                        li.replaceChildren(link);
                    }
                    const animation = row.querySelector('.syn-logo-marquee__track').getAnimations()[0];
                    animation.pause();
                    animation.currentTime = 0;
                }""")
                require(not originals_fit(first), 'fixture must begin with clipped links')
                page.keyboard.press('Shift+Tab')
                require(first.get_by_role('link', name='HORIZON').evaluate(
                    'link => link === document.activeElement'), 'Tab must reach the last original link')
                require(originals_fit(first) and metrics(page)[0]['name'] == 'none' and
                        metrics(page)[0]['copies'][1]['display'] == 'none',
                        'keyboard focus must expose every original link and hide the copy')
                page.locator('#website-animation-controls button').last.focus()
                first.evaluate("""row => {
                    row.style.setProperty('--syn-logo-speed', '2');
                }""")
                require(abs(metrics(page)[0]['duration'] - 12) < .01,
                        '2x speed must halve 24s to 12s on supported CSS')
                # Demo controls can edit either row without altering the
                # CSS-only embed contract or the other row's playback.
                require(page.locator('#logo-marquee-controls').is_visible(),
                        'interactive marquee controls should be available with JS')
                page.locator('#logo-row-1-direction').select_option('right')
                page.locator('#logo-row-2-direction').select_option('left')
                require([r['animationDirection'] for r in metrics(page)] ==
                        ['reverse', 'normal'], 'each direction selector works independently')
                page.locator('#logo-row-1-speed').evaluate("""el => {
                    el.value = "2";
                    el.dispatchEvent(new Event('input', {bubbles: true}));
                }""")
                require(abs(metrics(page)[0]['duration'] - 12) < .01 and
                        page.locator('#logo-row-1-speed-value').inner_text() == '2×',
                        'speed slider should update CSS timing and readable output')
                page.locator('#logo-row-2-speed').evaluate("""el => {
                    el.value = "0.5";
                    el.dispatchEvent(new Event('input', {bubbles: true}));
                }""")
                require(abs(metrics(page)[1]['duration'] - 56) < .01 and
                        abs(metrics(page)[0]['duration'] - 12) < .01,
                        'second speed slider should not change first row speed')
                pause_button = page.locator('#logo-marquee-pause')
                pause_button.click()
                require(pause_button.get_attribute('aria-pressed') == 'true' and all(
                    row.locator('.syn-logo-marquee__track').evaluate(
                        "el => getComputedStyle(el).animationPlayState") == 'paused'
                    for row in page.locator('.syn-logo-marquee__row').all()
                ), 'global pause must stop both CSS loops')
                pause_button.click()
                require(pause_button.get_attribute('aria-pressed') == 'false' and all(
                    row.locator('.syn-logo-marquee__track').evaluate(
                        "el => getComputedStyle(el).animationPlayState") == 'running'
                    for row in page.locator('.syn-logo-marquee__row').all()
                ), 'global resume must restart both CSS loops')
                page.close()

                # No-JS mode still animates, while reduced motion displays every
                # original logo and removes repeated decorative copies.
                plain = browser.new_page(
                    java_script_enabled=False, viewport={'width': 320, 'height': 720})
                plain.goto(url)
                require(plain.locator('#logo-marquee-controls').is_hidden(),
                        'showcase controls must not be visible without JavaScript')
                require(metrics(plain)[0]['name'] == 'syn-logo-marquee-scroll',
                        'no JS required for animation')
                plain.close()
                reduced = browser.new_page(
                    reduced_motion='reduce', java_script_enabled=False,
                    viewport={'width': 320, 'height': 720})
                reduced.goto(url)
                require(reduced.locator('#logo-marquee-controls').is_hidden(),
                        'reduced-motion no-JS fallback must keep inert controls hidden')
                for row in metrics(reduced):
                    require(row['name'] == 'none', 'reduced motion must stop loop')
                    require(row['copies'][1]['display'] == 'none',
                            'decorative duplicate should be hidden under reduced motion')
                    require(row['copies'][0]['display'] == 'flex',
                            'original logos remain visible under reduced motion')
                require(reduced.evaluate(
                    "() => document.documentElement.scrollWidth <= innerWidth + 1"),
                    'reduced-motion layout must not overflow mobile viewport')
                reduced.close()

                # Missing duplicate: no empty-space animation.
                missing = browser.new_page(viewport={'width': 390, 'height': 720})
                missing.goto(url)
                missing.locator('.syn-logo-marquee__row').first.evaluate(
                    "row => row.querySelectorAll('.syn-logo-marquee__group')[1].remove()"
                )
                require(metrics(missing)[0]['name'] == 'none' and
                        originals_fit(missing.locator('.syn-logo-marquee__row').first),
                        'single group should stay visible and static')
                # Optional one-list progressive enhancer activates CSS-only
                # motion after cloning, without duplicate accessibility names.
                missing.locator('.syn-logo-marquee__row').first.evaluate("""row => {
                    const track = row.querySelector(':scope > .syn-logo-marquee__track');
                    const source = track?.querySelector(':scope > .syn-logo-marquee__group:only-child');
                    if (!source) return;
                    const copy = source.cloneNode(true);
                    copy.setAttribute('aria-hidden', 'true');
                    copy.inert = true;
                    copy.querySelectorAll('[id]').forEach(node => node.removeAttribute('id'));
                    copy.querySelectorAll('img').forEach(image => { image.alt = ''; });
                    track.append(copy);
                }""")
                require(metrics(missing)[0]['name'] == 'syn-logo-marquee-scroll' and
                        metrics(missing)[0]['copies'][1]['hidden'] == 'true',
                        'optional progressive duplication must safely enable looping')
                missing.close()
                print('PASS: two seamless responsive rows, opposite directions, speed, pause, reduced motion and no-JS')
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
