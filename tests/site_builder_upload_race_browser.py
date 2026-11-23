"""Ensure delayed image hashing cannot replace an asset on another site page."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import base64
import json
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WlJnE8AAAAASUVORK5CYII=')
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def log_message(self,*_args):pass

def verify(browser,url):
    ctx=browser.new_context(viewport={'width':1280,'height':850},accept_downloads=True)
    page=ctx.new_page()
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(url+'/docs/page-builder.html',wait_until='load')
    expect(page.locator('#builder-section-count')).to_contain_text('85',timeout=15000)
    page.locator('[data-block-type="section:image-gallery"]').click()
    home_id=page.locator('#builder-outline > li').last.get_attribute('data-block-id')
    page.locator('#builder-site-new-slug').fill('about')
    page.locator('#builder-site-add-page').click()
    page.locator('[data-block-type="section:image-gallery"]').click()
    page.evaluate('''() => {const old=URL.createObjectURL.bind(URL);URL.createObjectURL=blob=>{window.__captured=blob;return old(blob);};}''')
    with page.expect_download():page.locator('#builder-export-json').click()
    site=json.loads(page.evaluate('async()=>await window.__captured.text()'))
    gallery=next(block for block in site['pages'][1]['document']['blocks'] if block['type']=='section:image-gallery')
    gallery['id']=home_id  # Valid across separate pages; was vulnerable to wrong-page writes.
    page.locator('#builder-import').set_input_files({'name':'site.json','mimeType':'application/json','buffer':json.dumps(site).encode()})
    expect(page.locator('#builder-status')).to_contain_text('Site project opened')
    page.locator('#builder-outline > li').last.locator('[data-action="select"]').click()
    page.evaluate('''() => {
      const read=File.prototype.arrayBuffer;
      File.prototype.arrayBuffer=function(){
        const file=this;
        return new Promise((resolve,reject)=>{
          window.__releaseImage=()=>read.call(file).then(resolve,reject);
        });
      };
    }''')
    page.locator('#builder-inspector input[type="file"][data-field="src1"]').set_input_files({
        'name':'test.png','mimeType':'image/png','buffer':PNG,
    })
    page.wait_for_function('typeof window.__releaseImage === "function"')
    page.locator('#builder-site-page-select').select_option('about')
    page.evaluate('window.__releaseImage()')
    expect(page.locator('#builder-status')).to_contain_text('page changed during image processing',timeout=10000)
    with page.expect_download():page.locator('#builder-export-json').click()
    after=json.loads(page.evaluate('async()=>await window.__captured.text()'))
    for entry in after['pages']:
        assert not entry['document']['media']
        original=next(p for p in site['pages'] if p['slug']==entry['slug'])
        block=next(b for b in entry['document']['blocks'] if b['id']==home_id)
        expected=next(b for b in original['document']['blocks'] if b['id']==home_id)
        assert block['props']['src1']==expected['props']['src1']
    assert not errors,errors
    ctx.close()

def main():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            try:
                verify(browser,'http://127.0.0.1:'+str(server.server_port))
                print('PASS image upload stays owned by its starting page')
            finally:browser.close()
    finally:server.shutdown();server.server_close()
if __name__=='__main__':main()
