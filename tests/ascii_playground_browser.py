"""Optional browser smoke: local image conversion, export, animation and reflow."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=ROOT / '.cloudflare-public'))
Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE'), args=['--no-sandbox'])
        for width in (320, 1280):
            page = browser.new_page(viewport={'width':width, 'height':900}, accept_downloads=True)
            errors, requests = [], []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('request', lambda r: requests.append(r.url))
            page.goto(f'http://127.0.0.1:{server.server_port}/tools/ascii-playground.html')
            page.locator('#copy').wait_for()
            assert page.locator('#export').input_value().strip()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
            original = page.locator('#export').input_value()
            page.select_option('#pattern','plasma')
            assert page.locator('#export').input_value()!=original
            page.select_option('#format','svg')
            assert '<svg' in page.locator('#export').input_value()
            with page.expect_download() as result:
                page.click('#download')
            assert result.value.suggested_filename=='syntyr-ascii.svg'
            page.select_option('#ramp','braille')
            page.select_option('#format','html')
            fragment=page.locator('#export').input_value()
            assert any('\u2800' <= glyph <= '\u28ff' for glyph in fragment)
            with page.expect_download() as result:
                page.click('#download')
            assert result.value.suggested_filename=='syntyr-ascii.html'
            assert result.value.path().read_bytes()==b'\xef\xbb\xbf'+fragment.encode('utf-8')
            page.click('#play')
            assert page.locator('#copy').is_disabled()
            page.click('#stop')
            assert page.locator('#copy').is_enabled()
            page.emulate_media(reduced_motion='reduce')
            page.wait_for_function("document.querySelector('#play').disabled")
            assert page.locator('#play').is_disabled()
            page.select_option('#source','image')
            assert page.locator('#copy').is_disabled()
            png=page.evaluate("""() => {const c=document.createElement('canvas');c.width=32;c.height=16;const x=c.getContext('2d');x.fillStyle='white';x.fillRect(0,0,16,16);return [...Uint8Array.from(atob(c.toDataURL().split(',')[1]),s=>s.charCodeAt(0))]}""")
            page.locator('#image').set_input_files({'name':'sample.png','mimeType':'image/png','buffer':bytes(png)})
            page.wait_for_function("document.querySelector('#status').textContent==='Image converted locally.'")
            assert page.locator('#copy').is_enabled()
            assert page.locator('#dimensions').inner_text()=='64 columns × 16 rows'
            page.select_option('#format','txt')
            art=page.locator('#export').input_value()
            page.check('#invert')
            assert page.locator('#export').input_value()!=art
            page.select_option('#dither','floyd')
            page.select_option('#dither','bayer')
            page.select_option('#ramp','custom')
            page.fill('#custom-ramp',' .#')
            assert set(page.locator('#export').input_value()) <= set(' .#\n')
            page.evaluate("""() => {
                const decode = window.createImageBitmap.bind(window);
                window.createImageBitmap = file => new Promise((resolve, reject) => {
                    window.finishImageDecode = () => {
                        window.createImageBitmap = decode;
                        return decode(file).then(resolve, reject);
                    };
                });
            }""")
            page.locator('#image').set_input_files({'name':'delayed.png','mimeType':'image/png','buffer':bytes(png)})
            page.fill('#custom-ramp','aa')
            page.evaluate('window.finishImageDecode()')
            assert 'Use 2–32 distinct' in page.locator('#status').inner_text()
            assert page.locator('#preview').inner_text()=='No preview'
            assert not page.locator('#export').input_value()
            assert page.locator('#copy').is_disabled()
            assert page.locator('#download').is_disabled()
            page.fill('#custom-ramp',' .#')
            assert page.locator('#copy').is_enabled()
            page.select_option('#source','logo')
            page.fill('#logo-text','TEST')
            page.select_option('#logo-style','hash')
            assert '#' in page.locator('#export').input_value()
            assert len(page.locator('#export').input_value().splitlines())==5
            page.fill('#logo-text','<bad>')
            assert page.locator('#copy').is_disabled()
            page.fill('#logo-text','SYNTYR')
            assert page.locator('#copy').is_enabled()
            page.goto(f'http://127.0.0.1:{server.server_port}/examples/ascii-heroes.html')
            assert page.locator('main textarea').count()==3
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
            assert not errors,errors
            assert all(url.startswith(f'http://127.0.0.1:{server.server_port}/') for url in requests),requests
            page.close()
        browser.close()
finally:
    server.shutdown()
print('PASS Chromium: mobile/desktop, six-pattern controls, local image conversion, SVG and UTF-8 HTML downloads, reduced motion, no external requests')
