/* Optional, real-browser regression for the Syntyr HTMX documentation demo.
   Not part of the CSS build or mandatory test suite; no npm dependency is added.

   Install Playwright separately and its Chromium browser, then run:
     SYNTYR_LIVE_SITE_URL=https://syntyr-css.pages.dev node tests/htmx_live_browser.cjs

   To reuse an already installed Playwright and browser binary:
     SYNTYR_PLAYWRIGHT_MODULE=/path/to/node_modules/playwright \
     PLAYWRIGHT_CHROMIUM_EXECUTABLE=/path/to/chrome-headless-shell \
     node tests/htmx_live_browser.cjs

   Set SYNTYR_LIVE_SITE_URL to a Cloudflare branch preview before merging.
   All API requests are read-only GETs against fictional, deterministic data.
*/
'use strict';
const assert = require('node:assert/strict');
const { test, before, after } = require('node:test');

const moduleName = process.env.SYNTYR_PLAYWRIGHT_MODULE || 'playwright';
const { chromium } = require(moduleName);
const base = (process.env.SYNTYR_LIVE_SITE_URL || 'https://syntyr-css.pages.dev').replace(/\/$/, '');
let browser;

before(async () => {
  const launch = { headless: true };
  if (process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE) {
    launch.executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE;
    launch.args = ['--no-sandbox'];
  }
  browser = await chromium.launch(launch);
});
after(async () => {
  await browser?.close();
});

async function visit(path, { javaScriptEnabled = true, width = 1365 } = {}) {
  const context = await browser.newContext({
    javaScriptEnabled,
    viewport: { width, height: 900 },
    reducedMotion: 'reduce',
  });
  const page = await context.newPage();
  page.setDefaultTimeout(12000);
  await page.goto(base + path, { waitUntil: 'domcontentloaded', timeout: 25000 });
  return { context, page };
}

test('typing uses HTMX fragments and leaves no browser errors', async () => {
  const { context, page } = await visit('/docs/htmx-playground');
  const errors = [];
  const requests = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('request', (request) => {
    if (request.url().includes('/api/htmx-demo/customers')) requests.push(request.headers());
  });
  try {
    await page.waitForFunction(() => typeof window.htmx === 'object');
    await page.locator('#demo-query').fill('Northstar');
    await page.locator('#customer-results').getByText('Northstar Media').waitFor();
    assert.match(page.url(), /q=Northstar/);
    assert.ok(requests.some((headers) => headers['hx-request'] === 'true'));
    assert.equal(errors.length, 0, errors.join('\n'));
  } finally {
    await context.close();
  }
});

test('sort, pagination, history and bookmarked full-page reload all work', async () => {
  const { context, page } = await visit('/docs/htmx-playground');
  try {
    await page.waitForFunction(() => typeof window.htmx === 'object');
    await page.locator('#demo-query').fill('');
    await page.locator('#demo-sort').selectOption('name_desc');
    await page.locator('#customer-results [aria-sort="descending"]').waitFor();
    assert.equal(await page.locator('#customer-results tbody tr:first-child th').innerText(), 'Summit Signworks');
    await page.locator('#customer-results').getByRole('link', { name: 'Next' }).click();
    await page.locator('#customer-results').getByText('Page 2 of 3').waitFor();
    const pageTwo = page.url();
    await page.goBack({ waitUntil: 'domcontentloaded' });
    await page.locator('#customer-results').getByText('Page 1 of 3').waitFor();
    await page.goForward({ waitUntil: 'domcontentloaded' });
    await page.locator('#customer-results').getByText('Page 2 of 3').waitFor();
    assert.equal(page.url(), pageTwo);
    await page.reload({ waitUntil: 'domcontentloaded' });
    assert.match(await page.locator('h1').innerText(), /HTMX customer explorer/);
    await page.locator('#customer-results').getByText('Page 2 of 3').waitFor();
  } finally {
    await context.close();
  }
});

test('narrow screens contain readable table overflow in a keyboard-scrollable region', async () => {
  const { context, page } = await visit('/api/htmx-demo/customers', { width: 320 });
  try {
    const region = page.getByRole('region', { name: 'Scrollable customer table' });
    await region.waitFor();
    const measurements = await region.evaluate((element) => ({
      clientWidth: element.clientWidth,
      scrollWidth: element.scrollWidth,
      tableMinWidth: getComputedStyle(element.querySelector('table')).minWidth,
      documentWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
    }));
    assert.ok(measurements.scrollWidth > measurements.clientWidth + 100, JSON.stringify(measurements));
    assert.ok(parseFloat(measurements.tableMinWidth) >= 500, JSON.stringify(measurements));
    assert.ok(measurements.documentWidth <= measurements.viewportWidth + 2, JSON.stringify(measurements));
    await region.focus();
    await page.keyboard.press('ArrowRight');
    await page.waitForFunction(() => document.querySelector('.syn-table-wrap').scrollLeft > 0);
  } finally {
    await context.close();
  }
});

test('native form still navigates and renders results without JavaScript', async () => {
  const { context, page } = await visit('/docs/htmx-playground', { javaScriptEnabled: false });
  try {
    await page.locator('#demo-query').fill('Acme');
    await Promise.all([
      page.waitForURL(/\/api\/htmx-demo\/customers\?/),
      page.locator('form#customer-search button[type=submit]').click(),
    ]);
    await page.getByText('Acme Displays').waitFor();
    assert.match(await page.locator('h1').innerText(), /HTMX customer explorer/);
  } finally {
    await context.close();
  }
});
