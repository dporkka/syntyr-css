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
        assert.equal(await page.locator('#catalog-release-filter').inputValue(), 'published-alpha4');
        assert.equal((await page.locator('#catalog-release-title').innerText()).trim(), 'Published alpha.4 CSS-covered examples');
        assert.equal(await page.locator('#catalog-release-control').isVisible(), true);
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), 42);
        assert.equal(await page.locator('.catalog-card[aria-labelledby="catalog-viz-bars-title"]:not([hidden])').count(), 0);
        assert.ok((await page.locator('#catalog-framework-stylesheet').getAttribute('href')).includes('site-releases/0.3.0-alpha.4/'));
        await page.locator('#catalog-release-filter').selectOption('source-alpha5');
        assert.equal((await page.locator('#catalog-release-title').innerText()).trim(), 'Unreleased alpha.5 component examples');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), total);
        for (const id of ['catalog-input-group-title', 'catalog-crm-filters-title',
          'catalog-recovery-state-title', 'catalog-geometry-frame-title', 'catalog-viz-bars-title']) {
          assert.equal(await page.locator(`.catalog-card[aria-labelledby="${id}"]`).count(), 1);
        }
        assert.equal(await page.locator(".catalog-edit").count(), total);
        const links = page.locator('#catalog-index .catalog-index-link');
        assert.equal(await links.count(), total);
        const labels = (await links.allTextContents()).map((label) => label.trim());
        assert.deepEqual(labels, [...labels].sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase())));
        // Filter only native interactions with documented feature-specific fallbacks.
        await page.locator('#catalog-browser-filter').selectOption('native-advanced');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), 3);
        const advancedIds = await page.locator('.catalog-card:not([hidden])').evaluateAll(
          cards => cards.map(card => card.getAttribute('aria-labelledby')).sort()
        );
        assert.deepEqual(advancedIds, [
          'catalog-interaction-card-0', 'catalog-interaction-card-2', 'catalog-native-popover-title'
        ]);
        await page.locator('#catalog-category').selectOption('layout');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), 0);
        await page.locator('#catalog-category').selectOption('all');
        await page.locator('#catalog-browser-filter').selectOption('without-advanced');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), total - 3);
        await page.locator('#catalog-browser-filter').selectOption('all');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), total);
        // Module and use-case filters must compose with search, category and
        // native feature requirements without removing no-JS source markup.
        await page.locator('#catalog-module-filter').selectOption('core-only');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), 44);
        await page.locator('#catalog-module-filter').selectOption('syntyr.recipes.css');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), 2);
        await page.locator('#catalog-use-case-filter').selectOption('saas-dashboard');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), 2);
        await page.locator('#catalog-use-case-filter').selectOption('marketing-site');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), 0);
        await page.locator('#catalog-use-case-filter').selectOption('all');
        for (const filename of ['syntyr.geometry.css', 'syntyr.viz.css', 'syntyr.semantic.css']) {
          await page.locator('#catalog-module-filter').selectOption(filename);
          assert.equal(await page.locator('.catalog-card:not([hidden])').count(), 1, filename);
        }
        await page.locator('#catalog-module-filter').selectOption('all');
        await page.locator('#catalog-use-case-filter').selectOption('marketing-site');
        assert.equal(await page.locator('.catalog-card[aria-labelledby="catalog-pricing-title"]:not([hidden])').count(), 1);
        assert.equal(await page.locator('.catalog-card[aria-labelledby="catalog-crm-filters-title"]:not([hidden])').count(), 0);
        await page.locator('#catalog-use-case-filter').selectOption('navigation');
        await page.locator('#catalog-browser-filter').selectOption('native-advanced');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), 1);
        assert.equal(await page.locator('.catalog-card[aria-labelledby="catalog-native-popover-title"]:not([hidden])').count(), 1);
        await page.locator('#catalog-browser-filter').selectOption('all');
        await page.locator('#catalog-use-case-filter').selectOption('all');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), total);
        assert.equal(await page.locator('.catalog-actions').count(), total);
        assert.equal(await page.locator('.catalog-live').count(), total);
        assert.equal(await page.locator('.catalog-actions').first().evaluate(el => getComputedStyle(el).display), 'flex');
        if (width === 1280) {
          const positions = await page.locator('.catalog-actions').first().evaluate(el => [...el.children].map(child => child.getBoundingClientRect().top));
          assert.ok(positions.every(top => Math.abs(top - positions[0]) < 2), `Actions should be inline at desktop width: ${positions}`);
          assert.equal(await page.locator('.catalog-sidebar').evaluate(el => getComputedStyle(el).position), 'sticky');
        }
        await page.locator('#catalog-search').fill('buttons');
        await page.locator('#catalog-module-filter').selectOption('syntyr.recipes.css');
        await page.locator('#catalog-use-case-filter').selectOption('saas-dashboard');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), 0);
        if (width < 1024) {
          await page.locator('.catalog-mobile-index summary').click();
          await page.locator('.catalog-mobile-index a[href="#catalog-alerts-title"]').click();
        } else {
          await page.locator('#catalog-index a[href="#catalog-alerts-title"]').click();
        }
        await page.waitForFunction(() => location.hash === '#catalog-alerts-title' && document.querySelector('#catalog-search').value === '');
        assert.equal(await page.locator('.catalog-card:not([hidden])').count(), total);
        assert.equal(await page.locator('#catalog-module-filter').inputValue(), 'all');
        assert.equal(await page.locator('#catalog-use-case-filter').inputValue(), 'all');
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
        const tableMatches = await page.locator('.catalog-card:not([hidden])').count();
        assert.ok(tableMatches >= 3, 'Table search should find all documented table patterns');
        assert.equal(await page.locator('#catalog-results').innerText(), `Showing ${tableMatches} of ${total} examples.`);
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
        assert.equal(await page.locator('[data-catalog-copy-page]:not([hidden])').count(), total);
        await page.locator('.catalog-card:not([hidden]) .catalog-code-details').evaluate(el => { el.open = true; });
        await page.locator('.catalog-card:not([hidden]) [data-catalog-copy-page]').click();
        const fullPage = await page.evaluate(() => window.__catalogCopied);
        assert.ok(fullPage.startsWith('<!doctype html>'));
        assert.ok(fullPage.includes('<body class="syn-root" data-syn-theme="studio">'));
        assert.ok(fullPage.includes('<link rel="stylesheet" href="/dist/syntyr.core.css">'));
        assert.ok(fullPage.includes('syn-button--primary'));
        assert.equal((fullPage.match(/syntyr.core.css/g) || []).length, 1);
        await page.locator('#catalog-release-filter').selectOption('published-alpha4');
        await page.locator('.catalog-card:not([hidden]) .catalog-code-details').first().evaluate(el => {el.open = true;});
        await page.locator('.catalog-card:not([hidden]) [data-catalog-copy-page]').first().click();
        const pinnedPage = await page.evaluate(() => window.__catalogCopied);
        assert.ok(pinnedPage.includes('https://syntyr-css.pages.dev/v/0.3.0-alpha.4/syntyr.core.css'));
        assert.ok(!pinnedPage.includes('href="/dist/syntyr.core.css"'));
        await page.locator('#catalog-release-filter').selectOption('source-alpha5');
        // Optional stylesheet requirements must be complete, not only the
        // primary CSS badge. The meter demo also uses semantic CSS.
        await page.locator('#catalog-search').fill('meter and output');
        await page.locator('.catalog-card:not([hidden]) .catalog-code-details').evaluate(el => { el.open = true; });
        await page.locator('.catalog-card:not([hidden]) [data-catalog-copy-page]').click();
        const meterPage = await page.evaluate(() => window.__catalogCopied);
        assert.ok(meterPage.includes('/dist/syntyr.semantic.css'));
        await page.locator('#catalog-search').fill('buttons');
        assert.equal(await page.locator('#catalog-results').innerText(), `Showing 1 of ${total} examples.`);
        await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', {configurable: true, value: undefined}));
        await page.locator('.catalog-card:not([hidden]) [data-catalog-copy-page]').click();
        const standaloneFallback = page.locator('.catalog-card:not([hidden]) [data-catalog-page-fallback]');
        assert.equal(await standaloneFallback.evaluate(el => el.open), true);
        assert.ok((await standaloneFallback.locator('code').innerText()).includes('<!doctype html>'));
        assert.equal(await page.locator('#catalog-feedback').innerText(), 'Complete page selected. Use your keyboard to copy it.');
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
        assert.equal(await noJsPage.locator('#catalog-browser-filter').count(), 1);
        assert.equal(await noJsPage.locator('#catalog-module-filter').count(), 1);
        assert.equal(await noJsPage.locator('#catalog-use-case-filter').count(), 1);
        assert.equal(await noJsPage.locator('[data-catalog-copy]:visible').count(), 0);
        assert.equal(await noJsPage.locator('[data-catalog-copy-page]:visible').count(), 0);
        assert.equal(await noJsPage.locator('#catalog-browser-support').count(), 1);
        await noJs.close();
        process.stdout.write(`${name} ${width}px: search, clipboard, empty state, reflow and no-JS pass\n`);
      }
      // A deep link to an experimental-only example must not disappear behind
      // the default published-release filter. Covered examples stay published.
      for (const [targetId, expectedMode] of [
        ['catalog-viz-bars-title', 'source-alpha5'],
        ['catalog-buttons-title', 'published-alpha4']
      ]) {
        const linked = await browser.newPage({viewport: {width: 390, height: 800}});
        await linked.goto(catalog + '#' + targetId, {waitUntil: 'load'});
        await linked.waitForFunction(() => !document.querySelector('#catalog-controls').hidden);
        await linked.waitForFunction(({targetId, expectedMode}) =>
          document.getElementById('catalog-release-filter').value === expectedMode &&
          !document.getElementById(targetId).closest('.catalog-card').hidden,
          {targetId, expectedMode}
        );
        const pos = await linked.locator('#' + targetId).boundingBox();
        assert.ok(pos && pos.y >= -10 && pos.y <= 790, 'Unreachable deep link: ' + targetId);
        await linked.close();
      }
    } finally { await browser.close(); }
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
