/* Optional development-only browser proof. NODE_PATH must include Playwright. */
const assert = require('node:assert/strict');
const { createServer } = require('node:http');
const { readFile } = require('node:fs/promises');
const { resolve, sep, extname } = require('node:path');
const { chromium, firefox } = require('playwright');

const ROOT = resolve(__dirname, '..');
const server = createServer(async (req, res) => {
  const name = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const file = resolve(ROOT, '.' + name);
  if (!file.startsWith(ROOT + sep)) { res.writeHead(403); return res.end(); }
  try {
    const body = await readFile(file);
    const kind = { '.html': 'text/html', '.css': 'text/css', '.mjs': 'text/javascript' };
    res.writeHead(200, { 'Content-Type': kind[extname(file)] || 'text/plain' });
    res.end(body);
  } catch { res.writeHead(404); res.end('Not found'); }
});

(async () => {
  await new Promise((ok) => server.listen(0, '127.0.0.1', ok));
  const url = `http://127.0.0.1:${server.address().port}/examples/command-launcher.html`;
  try {
    for (const engine of [chromium, firefox]) {
      const executable = process.env[engine.name().toUpperCase() + "_EXECUTABLE"];
      const browser = await engine.launch({ headless: true, ...(executable ? { executablePath: executable } : {}) });
      try {
        const context = await browser.newContext({ viewport: { width: 320, height: 740 } });
        const page = await context.newPage();
        const errors = [];
        page.on('pageerror', (error) => errors.push(error.message));
        await page.goto(url);
        const trigger = page.locator('[data-command-open]');
        assert.equal(await trigger.isVisible(), true, `${engine.name()}: enhanced trigger shown`);
        await trigger.click();
        assert.equal(await page.locator('[data-command-dialog]').isVisible(), true);
        assert.equal(await page.locator('[data-command-query]').evaluate((el) => el === document.activeElement), true);
        await page.locator('[data-command-query]').fill('NATIVE hTmL');
        assert.equal(await page.locator('[data-command-item]:visible').count(), 1);
        assert.match(await page.locator('[data-command-status]').textContent(), /1 destination/);
        await page.locator('[data-command-query]').fill('not-a-destination');
        assert.equal(await page.locator('[data-command-empty]').isVisible(), true);
        await page.keyboard.press('Escape');
        assert.equal(await page.locator('[data-command-dialog]').isVisible(), false);
        assert.equal(await trigger.evaluate((el) => el === document.activeElement), true);
        await page.keyboard.press('Control+k');
        assert.equal(await page.locator('[data-command-dialog]').isVisible(), true);
        await page.keyboard.press('Control+k');
        assert.equal(await page.locator('[data-command-dialog]').isVisible(), false);
        await trigger.click();
        const overflow = await page.evaluate(() => ({
          body: document.documentElement.scrollWidth, viewport: window.innerWidth,
        }));
        assert.ok(overflow.body <= overflow.viewport, `${engine.name()}: no 320px horizontal overflow ${JSON.stringify(overflow)}`);
        await page.emulateMedia({ forcedColors: 'active', reducedMotion: 'reduce' });
        await page.evaluate(() => { document.documentElement.style.fontSize = '64px'; });
        const enlarged = await page.evaluate(() => ({
          width: document.documentElement.scrollWidth, viewport: window.innerWidth,
        }));
        assert.ok(enlarged.width <= enlarged.viewport,
          `${engine.name()}: no 400% enlarged-text horizontal overflow ${JSON.stringify(enlarged)}`);
        await page.locator('[data-command-item]').first().evaluate((el) => el.focus());
        assert.equal(await page.locator('[data-command-item]').first().evaluate((el) => el === document.activeElement), true);
        assert.deepEqual(errors, []);
        await context.close();

        const noJS = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 320, height: 740 } });
        const staticPage = await noJS.newPage();
        await staticPage.goto(url);
        assert.equal(await staticPage.locator('[data-command-open]').isVisible(), false, `${engine.name()}: no dead launcher button without JS`);
        assert.equal(await staticPage.locator('#quick-destinations a').count(), 3);
        assert.equal(await staticPage.locator('#quick-destinations').isVisible(), true);
        await noJS.close();
        console.log(`${engine.name()}: enhanced keyboard/filter, forced-colors, reflow, no-JS fallback PASS`);
      } finally { await browser.close(); }
    }
  } finally { server.close(); }
})().catch((e) => { console.error(e); process.exitCode = 1; });
