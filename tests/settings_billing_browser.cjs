/* Optional browser regression: uses a developer-installed Playwright package.
   No application JavaScript or browser dependency ships with Syntyr CSS. */
const assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
const { resolve } = require('node:path');
const { chromium } = require(process.env.SYNTYR_PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const executablePath = process.env.SYNTYR_CHROMIUM || undefined;
  const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
  const url = pathToFileURL(resolve(__dirname, '../examples/settings-billing.html')).href;
  try {
    for (const width of [320, 390, 768, 1120, 1440, 1680]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, javaScriptEnabled: false });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.goto(url);
      assert.equal(await page.locator('main').count(), 1);
      assert.equal(await page.locator('.settings-price-card').count(), 3);
      assert.equal(await page.locator('script').count(), 0);
      assert.equal(await page.locator('#cycle-yearly').isChecked(), true);
      assert.equal(await page.locator('.settings-price-card:first-child .settings-price--yearly').first().isVisible(), true);
      assert.equal(await page.locator('.settings-price-card:first-child .settings-price--monthly').first().isVisible(), false);
      await page.locator('#cycle-monthly').check();
      assert.equal(await page.locator('.settings-price-card:first-child .settings-price--monthly').first().isVisible(), true);
      assert.equal(await page.locator('.settings-price-card:first-child .settings-price--yearly').first().isVisible(), false);
      await page.locator('#cycle-yearly').check();
      assert.equal(await page.locator('.settings-price-card:first-child .settings-price--yearly').first().isVisible(), true);
      const noOverflow = async () => page.evaluate(() =>
        ({ content: document.documentElement.scrollWidth, viewport: window.innerWidth }));
      let size = await noOverflow();
      assert.ok(size.content <= size.viewport, `width ${width}: ${JSON.stringify(size)}`);
      const clippedControls = async () => page.evaluate(() => [...document.querySelectorAll('a, button, input')]
        .filter(el => {
          const rect = el.getBoundingClientRect(), style = getComputedStyle(el);
          return style.display !== 'none' && rect.width > 0 && !el.closest('.syn-table-wrap') &&
            (rect.left < -1 || rect.right > innerWidth + 1);
        }).map(el => el.textContent.trim().slice(0, 40)));
      assert.deepEqual(await clippedControls(), [], `width ${width}: interactive controls remain visible`);
      if (width === 1440) {
        const tops = await page.locator('.settings-price-card').evaluateAll(nodes =>
          nodes.map(node => Math.round(node.getBoundingClientRect().top)));
        assert.equal(new Set(tops).size, 1, 'pricing cards should align in three columns on desktop');
      }
      if (width === 320) {
        for (const fontSize of [32, 64]) {
          await page.evaluate(size => { document.documentElement.style.fontSize = size + 'px'; }, fontSize);
          size = await noOverflow();
          assert.ok(size.content <= size.viewport, `320px, ${fontSize}px root text: ${JSON.stringify(size)}`);
          assert.deepEqual(await clippedControls(), [], `320px, ${fontSize}px: links and controls must reflow`);
        }
        await page.emulateMedia({ forcedColors: 'active', reducedMotion: 'reduce' });
        size = await noOverflow();
        assert.ok(size.content <= size.viewport, 'forced-color and reduced-motion layout should not overflow');
      }
      assert.deepEqual(errors, []);
      await context.close();
    }
    console.log('Settings and billing: no-JS price selection, reflow, 400% text stress, forced colors PASS');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
