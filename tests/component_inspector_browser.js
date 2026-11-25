/* Real-browser acceptance for the docs-only inspector. */
'use strict';
const assert = require('node:assert/strict');
const {pathToFileURL} = require('node:url');
const path = require('node:path');
const {chromium} = require('playwright');
(async () => {
  const browser = await chromium.launch({headless: true,
    ...(process.env.SYNTYR_CHROMIUM_EXECUTABLE ? {executablePath: process.env.SYNTYR_CHROMIUM_EXECUTABLE} : {})});
  try {
    for (const width of [390, 1280]) {
      const page = await browser.newPage({viewport: {width, height: 850}});
      const errors = [];
      page.on('pageerror', error => errors.push(String(error)));
      await page.goto(pathToFileURL(path.resolve(__dirname, '../docs/playground.html')).href + '#component=catalog-buttons-title');
      const inspector = page.locator('#playground-inspector');
      await inspector.locator(':scope > summary').click({timeout: 3000});
      assert.match(await page.locator('#playground-inspector-sources').innerText(), /components\/buttons.css/);
      const target = page.locator('#playground-inspector-target');
      await target.locator('option').filter({hasText: 'syn-button--primary'}).first().waitFor({state:'attached'});
      const value = await target.locator('option').filter({hasText: 'syn-button--primary'}).first().getAttribute('value');
      await target.selectOption(value);
      assert.match(await page.locator('#playground-inspector-values').innerText(), /display:/);
      assert.match(await page.locator('#playground-inspector-values').innerText(), /--syn-accent: #2458c6/i);
      await inspector.locator('summary').filter({hasText: 'Token dependencies'}).click();
      const token = page.locator('#playground-inspector-token');
      await token.selectOption('--syn-focus-ring', {timeout: 3000});
      assert.match(await page.locator('#playground-inspector-dependencies').innerText(), /Depends on: --syn-accent/);
      assert.match(await page.locator('#playground-inspector-dependencies').innerText(), /Referenced by tokens: --syn-grid-focus/);
      await inspector.locator('summary').filter({hasText: 'Curated component variants'}).click();
      const variant = page.locator('#playground-inspector-variant');
      await variant.selectOption('syn-button--danger');
      const link = page.locator('#playground-inspector-variant-links a').first();
      assert.match(await link.getAttribute('href'), /catalog-buttons-title/);
      const [examplePage] = await Promise.all([page.waitForEvent('popup'), link.click()]);
      await examplePage.locator('#playground-example').waitFor();
      await examplePage.waitForFunction(() => document.querySelector('#playground-markup').value.includes('syn-button--danger'));
      await examplePage.close();
      await page.locator('#playground-theme').selectOption('grid');
      await page.waitForFunction(() => document.querySelector('#playground-inspector-values').textContent.includes('#76e7f7'));
      await page.locator('#playground-example').selectOption('catalog-definition-list-title');
      assert.match(await page.locator('#playground-inspector-sources').innerText(), /No Syntyr-class source files/);
      await page.locator('#playground-example').selectOption('actions');
      assert.match(await page.locator('#playground-inspector-sources').innerText(), /Starter/);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true);
      assert.deepEqual(errors, []);
      await page.close();
      console.log('PASS inspector ' + width + 'px');
    }
  } finally { await browser.close(); }
})().catch(error => {console.error(error); process.exitCode = 1;});
