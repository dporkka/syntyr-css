"""Syntyr reusable component browser smoke; local Chromium only, no published JS."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from zipfile import ZipFile
import json
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT),**kwargs)
    def log_message(self,*_args): pass

def verify(browser,url):
    context=browser.new_context(viewport={'width':1280,'height':900},accept_downloads=True)
    page=context.new_page()
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(url+'/docs/page-builder.html',wait_until='load')
    preview=page.frame_locator('#builder-preview')
    expect(preview.locator('.syn-stage h1')).to_have_text('Build your next website visually.')
    page.locator('#builder-outline [data-index="2"] [data-action="select"]').click()
    page.locator('#builder-reusable-name').fill('Main CTA')
    page.locator('#builder-reusable-save').click()
    expect(page.locator('#builder-reusable-hint')).to_contain_text('Main CTA')
    page.locator('#builder-inspector [data-field="heading"]').fill('Globally shared heading')
    expect(preview.locator('#contact h2')).to_have_text('Globally shared heading')

    page.locator('#builder-site-new-slug').fill('about')
    page.locator('#builder-site-add-page').click()
    page.locator('#builder-reusable-select').select_option('main-cta')
    page.locator('#builder-reusable-insert').click()
    expect(preview.locator('.syn-region h2').last).to_have_text('Globally shared heading')
    about_id=page.locator('#builder-outline > li').last.get_attribute('data-block-id')
    assert about_id
    page.locator('#builder-inspector [data-override-field="heading"]').check()
    page.locator('#builder-inspector [data-field="heading"]').fill('Only on About')
    expect(preview.locator('.syn-region h2').last).to_have_text('Only on About')

    page.locator('#builder-site-page-select').select_option('')
    page.locator('#builder-outline [data-index="2"] [data-action="select"]').click()
    page.locator('#builder-inspector [data-field="heading"]').fill('Global headline two')
    expect(preview.locator('#contact h2')).to_have_text('Global headline two')
    page.locator('#builder-site-page-select').select_option('about')
    expect(preview.locator('.syn-region h2').last).to_have_text('Only on About')

    page.evaluate('''() => {const original=URL.createObjectURL.bind(URL);URL.createObjectURL=blob=>{window.__lastSaved=blob;return original(blob);};}''')
    with page.expect_download() as info: page.locator('#builder-export-json').click()
    assert info.value.suggested_filename=='syntyr-site.json'
    site=json.loads(page.evaluate('async()=>await window.__lastSaved.text()'))
    assert len(site['components'])==1 and len(site['instances'])==2
    assert site['instances'][1]['overrides']['heading']=='Only on About'

    with page.expect_download() as info: page.locator('#builder-export-zip').click()
    assert info.value.suggested_filename=='syntyr-static-site.zip'
    with ZipFile(info.value.path()) as archive:
        home=archive.read('index.html').decode()
        about=archive.read('about/index.html').decode()
        assert 'Global headline two' in home
        assert 'Only on About' in about
        assert 'Global headline two' not in about
        assert '<script' not in home and '<script' not in about

    page.locator('#builder-import').set_input_files({'name':'site.json','mimeType':'application/json','buffer':json.dumps(site).encode()})
    expect(page.locator('#builder-status')).to_contain_text('Site project opened')
    page.locator('#builder-site-page-select').select_option('about')
    expect(preview.locator('.syn-region h2').last).to_have_text('Only on About')
    page.locator('#builder-outline > li').last.locator('[data-action="select"]').click()
    expect(page.locator('#builder-reusable-detach')).to_be_enabled()
    page.locator('#builder-reusable-detach').click()
    expect(page.locator('#builder-reusable-hint')).to_contain_text('Select a native section')
    assert not errors,errors
    context.close()

def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            try:
                verify(browser,'http://127.0.0.1:'+str(server.server_port))
                print('PASS Syntyr reusable component editor and static export')
            finally: browser.close()
    finally:
        server.shutdown();server.server_close()

if __name__=='__main__':main()
