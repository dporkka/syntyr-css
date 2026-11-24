"""Optional real-browser verification of the interactive ASCII companion."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=ROOT/'.cloudflare-public'))
Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE'),args=['--no-sandbox'])
        url=f'http://127.0.0.1:{server.server_port}/tools/ascii-interactive.html'
        for width in (320,1280):
            page=browser.new_page(viewport={'width':width,'height':900})
            errors=[]; requests=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('request',lambda r:requests.append(r.url))
            page.goto(url)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
            cards=page.locator('[data-ascii-effect]')
            assert cards.count()==5
            for kind in ('orbit','particles','distortion','radar'):
                root=page.locator(f'[data-ascii-effect="{kind}"]')
                pre=root.locator('pre'); button=root.locator('button')
                fallback=pre.text_content()
                button.click()
                assert button.get_attribute('aria-pressed')=='true'
                page.wait_for_timeout(150)
                root.evaluate("""el=>el.dispatchEvent(new PointerEvent('pointermove',{clientX:el.getBoundingClientRect().left+5,clientY:el.getBoundingClientRect().top+5,pointerType:'mouse'}))""")
                page.wait_for_function("([kind,fallback])=>document.querySelector('[data-ascii-effect='+kind+'] pre').textContent!==fallback",arg=[kind,fallback])
                button.click()
                assert pre.text_content()==fallback
                assert button.get_attribute('aria-pressed')=='false'
            root=page.locator('[data-ascii-effect=scroll]')
            button=root.locator('button');pre=root.locator('pre');fallback=pre.text_content()
            button.click()
            page.wait_for_timeout(150)
            frame=pre.text_content()
            page.evaluate('window.scrollTo(0,0)')
            page.wait_for_function("(frame)=>document.querySelector('[data-ascii-effect=scroll] pre').textContent!==frame",arg=frame)
            page.emulate_media(reduced_motion='reduce')
            page.wait_for_function("document.querySelector('[data-ascii-effect=scroll] button').disabled")
            assert pre.text_content()==fallback
            assert button.get_attribute('aria-pressed')=='false'
            assert not errors,errors
            assert all(r.startswith(f'http://127.0.0.1:{server.server_port}/') for r in requests)
            page.close()
        page=browser.new_page(java_script_enabled=False)
        page.goto(url)
        assert page.locator('[data-ascii-effect] pre').count()==5
        assert page.locator('[data-ascii-effect] button').first.is_disabled()
        browser.close()
finally:
    server.shutdown()
print('PASS interactive ASCII: five modes, pointer/scroll, opt-in, restore, reduced motion, no-script and responsive layout')
