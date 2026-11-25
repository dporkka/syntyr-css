'use strict';
// Developer-only browser smoke. No JS or Playwright reaches the CSS runtime.
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const path = require('node:path');
const {chromium} = require(process.env.SYNTYR_PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');

async function open(page, relative) {
  const response = await page.goto(pathToFileURL(path.join(root, relative)).href, {waitUntil:'load'});
  assert.ok(response || page.url().startsWith('file:'), 'static local page loaded');
}

(async () => {
  const browser = await chromium.launch({
    headless: true, executablePath: process.env.SYNTYR_CHROME_BIN || undefined
  });
  try {
    for (const width of [320, 390, 1280]) {
      const context = await browser.newContext({viewport:{width,height:900},javaScriptEnabled:false});
      const page = await context.newPage();
      await open(page, 'examples/form-state-contracts.html');
      assert.equal(await page.locator('script').count(),0);
      assert.equal(await page.locator('#account[aria-invalid=true]').count(),1);
      const style = await page.evaluate(() => {
        const color = (selector,property) => getComputedStyle(document.querySelector(selector))[property];
        return {
          invalid:color('#account','borderTopColor'),
          valid:color('#valid-name','borderTopColor'),
          disabled:color('#disabled-name','backgroundColor'),
          customButton:color('button[style*="--syn-button-bg"]','backgroundColor'),
          normalButton:color('.syn-button:not([style])','backgroundColor'),
          scroll:document.documentElement.scrollWidth,
          width:document.documentElement.clientWidth
        };
      });
      assert.notEqual(style.invalid, style.valid,'invalid and server-confirmed valid are visibly distinct');
      assert.notEqual(style.customButton, style.normalButton,'local button token changes paint');
      assert.equal(style.customButton,'rgb(35, 84, 161)','custom primary token paints exactly');
      assert.ok(style.scroll <= style.width + 1, 'form-state page reflows at '+width+': '+JSON.stringify(style));
      await open(page,'docs/blocks.html');
      assert.equal(await page.locator('[data-block-id]').count(),23);
      for (const id of ['resource-workspace','crm-workspace','billing-workspace']) {
        assert.equal(await page.locator('[data-block-id="'+id+'"]').count(),1,'missing '+id);
      }
      const gallery = await page.evaluate(() => ({
        width:document.documentElement.clientWidth, scroll:document.documentElement.scrollWidth
      }));
      assert.ok(gallery.scroll <= gallery.width + 1,'gallery overflow '+width+': '+JSON.stringify(gallery));
      await context.close();
      console.log('PASS chromium '+width+'px: form states/tokens and 23 independent blocks');
    }
    const context = await browser.newContext({forcedColors:'active',viewport:{width:390,height:800}});
    const page = await context.newPage();
    await open(page,'examples/form-state-contracts.html');
    assert.equal(await page.locator('.syn-error-summary[role=alert]').count(),1);
    const border = await page.locator('#account').evaluate(el=>getComputedStyle(el).borderTopStyle);
    assert.notEqual(border,'none','invalid input must retain forced-colors border');
    await context.close();
    console.log('PASS chromium forced-colors: labeled error summary and visible field border');
  } finally {
    await browser.close();
  }
})().catch(error=>{console.error(error.stack || error);process.exitCode=1;});
