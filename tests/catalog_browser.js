/* Optional maintainer-only Playwright test; not part of Syntyr CSS runtime. */
'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium, firefox, webkit} = require('playwright');
const catalog = pathToFileURL(path.resolve(__dirname, '../docs/catalog.html')).href;
const engines = {chromium, firefox, webkit};

(async () => {
  const names = process.argv.slice(2).length ? process.argv.slice(2) : ['chromium'];
  for (const name of names) {
    if (!engines[name]) throw Error(`Unknown browser ${name}`);
    const custom = {
      chromium: process.env.SYNTYR_CHROMIUM_EXECUTABLE,
      firefox: process.env.SYNTYR_FIREFOX_EXECUTABLE,
      webkit: process.env.SYNTYR_WEBKIT_EXECUTABLE,
    }[name];
    const browser = await engines[name].launch({headless: true, ...(custom ? {executablePath: custom} : {})});
    try {
      for (const width of [390, 1280]) {
        const page = await browser.newPage({viewport: {width, height: 800}});
        await page.goto(catalog, {waitUntil: 'load'});
        await page.waitForFunction(() => document.getElementById('catalog-controls').hidden === false);
        const total = await page.locator('.catalog-card').count();
        assert.ok(total >= 32);
        for (const id of ['catalog-input-group-title', 'catalog-crm-filters-title',
          'catalog-recovery-state-title', 'catalog-geometry-frame-title', 'catalog-viz-bars-title']) {
          assert.equal(await page.locator(`.catalog-card[aria-labelledby="${id}"]`).count(), 1);
        }
        assert.equal(await page.locator(".catalog-edit").count(), total);
        const links = page.locator('#catalog-index .catalog-index-link');
        assert.equal(await links.count(), total);
        const labels = (await links.allTextContents()).map((label) => label.trim());
        assert.deepEqual(labels, [...labels].sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase())));
        assert.equal(await page.locator('.catalog-actions').count(), total);
        assert.equal(await page.locator('.catalog-live').count(), total);
        assert.equal(await page.locator('.catalog-actions').first().evaluate(el => getComputedStyle(el).display), 'flex');
        if (width === 1280) {
          const positions = await page.locator('.catalog-actions').first().evaluate(el => [...el.children].map(child => child.getBoundingClientRect().top));
          assert.ok(positions.every(top => Math.abs(top - positions[0]) < 2), `Actions should be inline at desktop width: ${positions}`);
          assert.equal(await page.locator('.catalog-sidebar').evaluate(el => getComputedStyle(el).position), 'sticky');
        }
        await page.locator('#catalog-search').fill('buttons');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), 1);
        await page.locator('#catalog-index a[href="#catalog-alerts-title"]').click();
        await page.waitForFunction(() => location.hash === '#catalog-alerts-title' && document.querySelector('#catalog-search').value === '');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), total);
        await page.waitForFunction(() => document.querySelector('#catalog-index a[href="#catalog-alerts-title"]').classList.contains('is-in-view'));
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), total);
        assert.equal(await page.locator('.catalog-copy:not([hidden])').count(), total);
        await page.locator('#catalog-category').selectOption('media');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), 1);
        await page.locator('#catalog-search').fill('image');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), 1);
        await page.locator('#catalog-search').fill('buttons');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), 0);
        await page.locator('#catalog-category').selectOption('all');
        await page.locator('#catalog-search').fill('');
        await page.locator('#catalog-theme').selectOption('noir');
        assert.equal(await page.locator('body').getAttribute('data-syn-theme'), 'noir');
        await page.locator('#catalog-preview-size').selectOption('compact');
        assert.equal(await page.locator('#catalog-items').getAttribute('data-catalog-preview'), 'compact');
        const previewWidth = await page.locator('.catalog-preview').first().evaluate(el => el.getBoundingClientRect().width);
        assert.ok(previewWidth <= 23 * 16 + 1, 'Compact preview should not exceed 23rem');
        await page.locator('#catalog-search').fill('table');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), 3);
        assert.equal(await page.locator('#catalog-results').innerText(), `Showing 3 of ${total} examples.`);
        await page.locator('#catalog-search').fill('no-such-component');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), 0);
        assert.equal(await page.locator('#catalog-empty').isVisible(), true);
        await page.locator('#catalog-search').fill('buttons');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), 1);
        await page.evaluate(() => {
          Object.defineProperty(navigator, 'clipboard', {
            configurable: true, value: {writeText: async (value) => { window.__catalogCopied = value; }}
          });
        });
        await page.locator('.catalog-card:not([hidden]) [data-catalog-copy]').click();
        const copied = await page.evaluate(() => window.__catalogCopied);
        assert.ok(copied.includes('syn-button--primary'));
        assert.equal(await page.locator('#catalog-feedback').innerText(), 'Buttons HTML copied.');
        assert.equal(await page.locator('#catalog-results').innerText(), `Showing 1 of ${total} examples.`);
        await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', {configurable: true, value: undefined}));
        await page.locator('.catalog-card:not([hidden]) [data-catalog-copy]').click();
        assert.equal(await page.locator('.catalog-card:not([hidden]) .catalog-code-details').evaluate(el => el.open), true);
        assert.ok((await page.evaluate(() => window.getSelection()?.toString() || '')).includes('syn-button--primary'));
        assert.equal(await page.locator('#catalog-feedback').innerText(), 'HTML selected. Use your keyboard to copy it.');
        assert.equal(await page.locator('#catalog-results').innerText(), `Showing 1 of ${total} examples.`);
        // A native popover must stay within the viewport after scrolling.
        await page.locator('#catalog-search').fill('popover');
        const popoverInvoker = page.locator('button[popovertarget="catalog-help-popover"]').first();
        await popoverInvoker.scrollIntoViewIfNeeded();
        await popoverInvoker.click();
        const popover = page.locator('#catalog-help-popover');
        assert.equal(await popover.evaluate(el => el.matches(':popover-open')), true);
        const bounds = await popover.boundingBox();
        assert.ok(bounds && bounds.y >= -1 && bounds.y + bounds.height <= 801,
          `Popover should open within the viewport at ${width}px: ${JSON.stringify(bounds)}`);
        await popover.locator('button[popovertargetaction="hide"]').click();
        assert.equal(await popover.evaluate(el => el.matches(':popover-open')), false);
        await page.locator('#catalog-search').fill('');

        const dimensions = await page.evaluate(() => ({scroll: document.documentElement.scrollWidth, inner: window.innerWidth}));
        assert.ok(dimensions.scroll <= dimensions.inner + 1, `Unexpected horizontal overflow at ${width}: ${JSON.stringify(dimensions)}`);
        await page.close();

        const noJs = await browser.newContext({viewport: {width, height: 800}, javaScriptEnabled: false});
        const noJsPage = await noJs.newPage();
        await noJsPage.goto(catalog, {waitUntil: 'load'});
        assert.equal(await noJsPage.locator('.catalog-card:not([hidden])').count(), total);
        assert.equal(await noJsPage.locator('#catalog-results').innerText(), `${total} examples available.`);
        assert.equal(await noJsPage.locator('.catalog-source code').count(), total);
        assert.equal(await noJsPage.locator('#catalog-index a').count(), total);
        assert.equal(await noJsPage.locator('.catalog-live').count(), total);
        assert.equal(await noJsPage.locator('#catalog-controls').isVisible(), false);
        assert.equal(await noJsPage.locator('[data-catalog-copy]:visible').count(), 0);
        await noJs.close();
        process.stdout.write(`${name} ${width}px: search, clipboard, empty state, reflow and no-JS pass\n`);
      }
    } finally { await browser.close(); }
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
