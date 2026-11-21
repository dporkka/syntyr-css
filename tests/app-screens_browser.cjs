/* Developer-only browser proof; no runtime JavaScript is shipped in examples. */
const assert = require('node:assert/strict');
const { resolve } = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require(process.env.SYNTYR_PLAYWRIGHT_MODULE || 'playwright');
const ROOT = resolve(__dirname, '..');
const SCREENS = ['app-onboarding', 'app-team', 'app-notifications', 'app-integrations', 'app-security', 'app-account', 'app-audit', 'app-support', 'app-states'];
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
      assert.equal(await page.locator('.app-nav a').count(), 9, name);
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
        const currentLink = page.locator('.app-nav a[aria-current="page"]');
        const outlineOffset = () => currentLink.evaluate(el => parseFloat(getComputedStyle(el).outlineOffset));
        assert.ok(await outlineOffset() < 0, `${name} unfocused current link has inset outline`);
        // The brand link precedes the screen links in keyboard order.
        for (let i = 0; i < SCREENS.length + 1 && !(await currentLink.evaluate(el => el.matches(':focus-visible'))); i++) {
          await page.keyboard.press('Tab');
        }
        assert.ok(await currentLink.evaluate(el => el.matches(':focus-visible') && getComputedStyle(el).outlineStyle === 'solid'),
          `${name} current link shows a keyboard focus outline`);
        assert.ok(await outlineOffset() > 0, `${name} focused current link has outside outline`);
      }
      if (width === 1280) {
        if (name === 'app-states') {
          const cols = await page.locator('.app-state-grid').evaluate(el => getComputedStyle(el).gridTemplateColumns.split(' ').length);
          assert.ok(cols >= 2, 'state tiles should form multiple desktop columns');
        } else {
          const grid = await page.locator('.app-columns').evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(' ').length);
          assert.equal(grid,2,`${name} desktop two-column content`);
        }
        if (name === 'app-notifications' || name === 'app-integrations') {
          const nav = page.locator('.app-inline-tabs');
          const fragment = name === 'app-notifications' ? '#read' : '#available';
          await nav.locator(`a[href="${fragment}"]`).click();
          assert.equal(new URL(page.url()).hash, fragment, name);
          assert.equal(await nav.locator('[aria-current]').count(), 0, name);
        }
      }
      if (name === 'app-support' && width === 390) {
        const disclosure = page.locator('.app-faq details').first();
        assert.equal(await disclosure.getAttribute('open'), null);
        await disclosure.locator('summary').click();
        assert.equal(await disclosure.evaluate(el=>el.open), true, 'native FAQ disclosure opens without JavaScript');
        await disclosure.locator('summary').click();
        assert.equal(await disclosure.evaluate(el=>el.open), false, 'native FAQ disclosure closes without JavaScript');
      }
      assert.deepEqual(errors, []);
      if (width === 1440 && name === 'app-onboarding') await page.screenshot({path:'/tmp/syntyr-app-screens-20261121/onboarding-desktop.png',fullPage:true});
      if (width === 390 && name === 'app-team') await page.screenshot({path:'/tmp/syntyr-app-screens-20261121/team-mobile.png',fullPage:true});
      if (width === 1440 && name === 'app-audit') await page.screenshot({path:'/tmp/syntyr-extended-audit-desktop.png',fullPage:true});
      if (width === 390 && name === 'app-states') await page.screenshot({path:'/tmp/syntyr-extended-states-mobile.png',fullPage:true});
      await context.close();
    }
    console.log('PASS: 9 application screens × 6 viewports; 200%/400% text; forced colors; keyboard focus; no-JS');
  } finally { await browser.close(); }
})().catch(err=>{console.error(err);process.exitCode=1});
