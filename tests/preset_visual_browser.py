"""Optional browser/PNG regression for standalone CSS presets.

Development dependencies ONLY: playwright + pillow and a Chromium browser.
No Node, JS, screenshot service or browser is required by CSS consumers.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import io
import os
from pathlib import Path
import threading
import unittest

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASELINES = ROOT / 'tests' / 'visual-baselines' / 'presets'
PRESETS = ('minimal', 'saas', 'cinematic')
WIDTHS = (390, 1280)
UPDATE = False


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@contextmanager
def serve():
    handler = partial(QuietHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}'
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()


class PresetVisualRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        binary = os.environ.get('SYNTYR_CHROMIUM_EXECUTABLE')
        opts = {'headless': True}
        if binary:
            opts.update({'executable_path': binary, 'args': ['--no-sandbox']})
        try:
            cls.browser = cls.pw.chromium.launch(**opts)
        except Exception:
            cls.pw.stop()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def test_each_preset_across_viewports(self):
        with serve() as server:
            for preset in PRESETS:
                for width in WIDTHS:
                    with self.subTest(preset=preset, width=width):
                        self.assert_preview(server, preset, width)

    def assert_preview(self, server, preset, width):
        page = self.browser.new_page(viewport={'width': width, 'height': 800},
                                     device_scale_factor=1, reduced_motion='reduce',
                                     color_scheme='light')
        errors = []
        page.on('pageerror', lambda exc: errors.append(str(exc)))
        page.on('response', lambda resp: errors.append(f'{resp.status}: {resp.url}') if resp.status >= 400 else None)
        page.goto(server + '/examples/preset-preview.html', wait_until='load')
        # Only the test runner changes the stylesheet; the example itself has no JS.
        page.locator('link[rel="stylesheet"]').evaluate(
            '''(link, preset) => new Promise((resolve, reject) => {
                link.onload = resolve;
                link.onerror = reject;
                link.href = '/dist/presets/' + preset + '.css';
            })''', preset)
        self.assertEqual(page.locator('link[rel="stylesheet"]').count(), 1)
        filter_layout = page.locator('.syn-filter-bar').evaluate('e => getComputedStyle(e).display')
        self.assertEqual(filter_layout == 'flex', preset != 'minimal',
                         f'{preset}/{width}: expected recipes isolation')
        self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'),
                         f'{preset}/{width}: horizontal overflow')
        self.assertEqual(errors, [], f'{preset}/{width}: browser errors')
        self.assertEqual(page.locator('main').evaluate(
            "e => getComputedStyle(e).getPropertyValue('--syn-accent').trim()"), '#2458c6')
        self.assertEqual(page.locator('#host-outside').evaluate(
            "e => getComputedStyle(e).getPropertyValue('--syn-accent').trim()"), '')
        self.assertNotEqual(page.locator('#email').evaluate(
            'e => getComputedStyle(e).borderTopWidth'), '0px')
        page.locator('details summary').click()
        self.assertTrue(page.locator('details').evaluate('e => e.open'))
        page.locator('details summary').click()
        page.locator('[popovertarget="preset-popover"]').click()
        self.assertTrue(page.locator('#preset-popover').evaluate('e => e.matches(":popover-open")'))
        self.assertNotEqual(page.locator('#preset-popover').evaluate(
            'e => getComputedStyle(e).borderTopWidth'), '0px')
        page.locator('[popovertarget="preset-popover"]').click()
        page.locator('[commandfor="preset-dialog"]').click()
        self.assertTrue(page.locator('#preset-dialog').evaluate('e => e.open'))
        page.locator('#preset-dialog button').click()
        self.assertFalse(page.locator('#preset-dialog').evaluate('e => e.open'))
        self.assertNotEqual(page.locator('progress').evaluate(
            'e => getComputedStyle(e).accentColor'), 'auto')
        button = page.locator('.syn-button--primary')
        page.keyboard.press('Tab')  # Keyboard modality activates :focus-visible.
        button.focus()
        self.assertNotEqual(button.evaluate('e => getComputedStyle(e).outlineStyle'), 'none')
        button.evaluate('e => e.blur()')
        page.evaluate('document.fonts.ready')
        screenshot = page.locator('main').screenshot(animations='disabled')
        page.close()
        output = BASELINES / f'{preset}-{width}.png'
        if UPDATE:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(screenshot)
            return
        self.assertTrue(output.is_file(), f'Missing visual baseline: {output}')
        with Image.open(output) as expected, Image.open(io.BytesIO(screenshot)) as got:
            original, actual = expected.convert('RGB'), got.convert('RGB')
            self.assertEqual(original.size, actual.size, f'{preset}/{width}: dimensions drift')
            diff = ImageChops.difference(original, actual)
            changed = sum(max(pixel) > 24 for pixel in diff.get_flattened_data())
            fraction = changed / (actual.width * actual.height)
            self.assertLessEqual(fraction, .02, f'{preset}/{width}: {fraction:.2%} visual drift')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--update-baselines', action='store_true', help='regenerate intentionally and manually review PNGs')
    args = parser.parse_args()
    UPDATE = args.update_baselines
    unittest.main(argv=[__file__], verbosity=2)
