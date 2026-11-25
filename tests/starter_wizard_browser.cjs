/* Optional developer-only browser smoke. Requires local Playwright and Chromium. */
'use strict';
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.SYNTYR_CHROMIUM || undefined,
    headless: true,
    args: ['--no-sandbox'],
  });
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    const errors = [];
    page.on('pageerror', err => errors.push(err.message));
    const url = process.env.SYNTYR_WIZARD_URL || 'http://127.0.0.1:48177/docs/starter-wizard.html';
    const response = await page.goto(url, { waitUntil: 'networkidle' });
    assert.equal(response.status(), 200);
    await page.locator('.site-mobile-menu summary').click();
    assert.equal(await page.locator('.site-mobile-menu nav a[href="playground.html"]').isVisible(), true);
    await page.keyboard.press('Escape');
    await page.getByLabel('What are you building?').selectOption('admin');
    await page.getByLabel('Select a published theme').selectOption('grid');
    await page.getByLabel('Where will it run?').selectOption('go');
    await page.getByRole('button', { name: 'Generate starter' }).click();
    assert.equal(await page.locator('#starter-result').isVisible(), true);
    assert.equal(await page.getByRole('button', { name: 'Copy HTML' }).isEnabled(), true);
    const markup = await page.locator('#starter-code').inputValue();
    assert.match(markup, /Operations console/);
    assert.match(markup, /data-syn-theme="grid"/);
    assert.match(markup, /href="#tasks"/);
    assert.match(await page.locator('#starter-instructions').innerText(), /html\/template/);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
    assert.equal(overflow, false, 'mobile viewport must not overflow horizontally');
    // The handoff should carry the user's chosen starter into the live playground.
    await page.locator('#starter-edit').click();
    await page.waitForURL(/playground\.html#starter=admin&theme=grid&stack=go/);
    await page.waitForFunction(() => document.querySelector('#playground-markup')?.value.includes('Operations console'));
    assert.equal(await page.locator('#playground-theme').inputValue(), 'grid');
    assert.match(await page.locator('#playground-markup').inputValue(), /href="#tasks"/);
    assert.match(await page.locator('#playground-status').innerText(), /Preview updated/);
        assert.deepEqual(errors, [], 'no browser JavaScript errors');
    console.log('Starter wizard Chromium mobile smoke passed');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
