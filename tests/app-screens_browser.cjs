/* Developer-only browser proof; no runtime JavaScript is shipped in examples. */
const assert = require('node:assert/strict');
const { resolve } = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require(process.env.SYNTYR_PLAYWRIGHT_MODULE || 'playwright');
const ROOT = resolve(__dirname, '..');
const SCREENS = ['app-onboarding', 'app-team', 'app-notifications', 'app-integrations', 'app-security'];
const VIEWPORTS = [320, 390, 768, 1024, 1280, 1440];

const layout = () => ({
  scrollWidth: document.documentElement.scrollWidth,
  viewport: innerWidth,
  clipped: [...document.querySelectorAll('a,button,input,select,textarea,summary')]
    .filter(el => {
      const rect = el.getBoundingClientRect();
      const style = getComputedStyle(el);
      if (style.display === 'none' || style.visibility === 'hidden' || !rect.width || !rect.height) return false;
      if (el.closest('.syn-table-wrap')) return false;
      return rect.left < -1 || rect.right > innerWidth + 1;
    }).slice(0, 4).map(el => `${el.tagName}:${(el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 25)}`)
});

(async () => {
  const browser = await chromium.launch({headless:true, ...(process.env.SYNTYR_CHROMIUM ? {executablePath:process.env.SYNTYR_CHROMIUM}: {})});
  try {
    for (const name of SCREENS) for (const width of VIEWPORTS) {
      const context = await browser.newContext({viewport:{width,height:900},javaScriptEnabled:false,reducedMotion:'reduce'});
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', e=>errors.push(e.message));
      await page.goto(pathToFileURL(resolve(ROOT, `examples/${name}.html`)).href);
      assert.equal(await page.locator('script').count(), 0, name);
      assert.equal(await page.getByRole('main').count(), 1, name);
      assert.equal(await page.getByRole('heading', {level:1}).count(), 1, name);
      assert.equal(await page.locator('.app-nav a[aria-current="page"]').count(), 1, name);
      assert.equal(await page.locator('.app-nav a').count(), 5, name);
      assert.equal(await page.locator('button:not(:disabled)').count(), 0, name);
      const inspect = async stage => {
        const current = await page.evaluate(layout);
        assert.ok(current.scrollWidth <= current.viewport + 1, `${name} ${width} ${stage} root overflow ${JSON.stringify(current)}`);
        assert.deepEqual(current.clipped, [], `${name} ${width} ${stage} clipped controls`);
      };
      await inspect('normal');
      if (width === 320) {
        for (const factor of [2,4]) {
          await page.evaluate(factor=>{document.documentElement.style.fontSize=`${16*factor}px`}, factor);
          await inspect(`${factor}x text`);
        }
        await page.emulateMedia({forcedColors:'active', reducedMotion:'reduce'});
        await inspect('forced-colors');
        await page.keyboard.press('Tab');
        assert.ok(await page.locator('.app-skip').evaluate(el => el === document.activeElement), `${name} skip link focus`);
      }
      if (width === 1280) {
        const grid = await page.locator('.app-columns').evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(' ').length);
        assert.equal(grid,2,`${name} desktop two-column content`);
      }
      assert.deepEqual(errors, []);
      if (width === 1440 && name === 'app-onboarding') await page.screenshot({path:'/tmp/syntyr-app-screens-20261121/onboarding-desktop.png',fullPage:true});
      if (width === 390 && name === 'app-team') await page.screenshot({path:'/tmp/syntyr-app-screens-20261121/team-mobile.png',fullPage:true});
      await context.close();
    }
    console.log('PASS: 5 application screens × 6 viewports; 200%/400% text; forced colors; keyboard focus; no-JS');
  } finally { await browser.close(); }
})().catch(err=>{console.error(err);process.exitCode=1});
