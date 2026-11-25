/* Developer-only native HTML/browser regression: NODE_PATH points to local Playwright. */
'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium, firefox, webkit } = require('playwright');
const base = path.resolve(__dirname, '../examples/native-elements.html');

async function tabToSummary(page, summary) {
  assert.equal(await summary.count(), 1,
    'Named disclosure must expose exactly one summary before keyboard navigation');
  for (let attempt = 0; attempt < 80; attempt += 1) {
    await page.keyboard.press('Tab');
    if (await summary.evaluate(el => el === document.activeElement)) return;
  }
  assert.fail('Named disclosure summary is not keyboard-reachable with Tab');
}

async function supportsExclusiveDetails(page) {
  return page.evaluate(() => {
    const fixture = document.createElement('div');
    fixture.innerHTML = '<details name="syntyr-grouping-support" open><summary>One</summary></details><details name="syntyr-grouping-support"><summary>Two</summary></details>';
    document.body.append(fixture);
    const [first, second] = fixture.querySelectorAll('details');
    second.open = true;
    const supported = !first.open && second.open;
    fixture.remove();
    return supported;
  });
}

const engine = process.env.SYNTYR_BROWSER || 'chromium';
const executables = {
  chromium: process.env.SYNTYR_CHROMIUM_EXECUTABLE,
  firefox: process.env.SYNTYR_FIREFOX_EXECUTABLE,
  webkit: process.env.SYNTYR_WEBKIT_EXECUTABLE,
};
if (!(engine in executables)) throw new Error('Unsupported browser: ' + engine);
(async () => {
  const browser = await {chromium, firefox, webkit}[engine].launch({
    headless: true, ...(executables[engine] ? {executablePath: executables[engine]} : {}),
  });
  try {
    for (const width of [320, 390, 768]) {
      const page = await browser.newPage({ viewport: {width, height: 800}, reducedMotion: 'reduce' });
      await page.goto(pathToFileURL(base).href);
      assert.equal(await page.locator('script').count(), 0, 'No runtime JS');
      for (const fontSize of ['100%', '200%', '400%']) {
        await page.evaluate(s => document.documentElement.style.fontSize = s, fontSize);
        const metric = await page.evaluate(() => {
          const file = document.querySelector('#design-file');
          const color = document.querySelector('#design-color');
          const fieldset = file.closest('fieldset');
          const box = element => {
            const rect = element.getBoundingClientRect();
            return {left: rect.left, right: rect.right};
          };
          return {
            page: document.documentElement.scrollWidth,
            viewport: document.documentElement.clientWidth,
            fieldset: box(fieldset),
            file: box(file),
            color: box(color),
          };
        });
        assert.ok(metric.page <= metric.viewport + 1,
          engine + ': horizontal overflow at width=' + width + ', root font=' + fontSize +
          ': ' + JSON.stringify(metric));
        for (const control of ['file', 'color']) {
          const rect = metric[control];
          assert.ok(rect.left >= metric.fieldset.left - 1 &&
                    rect.right <= metric.fieldset.right + 1,
            engine + ': ' + control + ' exceeds Native inputs fieldset at ' +
            width + 'px and ' + fontSize + ': ' + JSON.stringify(metric));
        }
      }
      await page.evaluate(() => document.documentElement.style.fontSize = '');
      const suggestions = page.locator('#native-location');
      assert.equal(await suggestions.getAttribute('list'), 'native-location-list');
      const listOptions = await suggestions.evaluate(input => input.list
        ? Array.from(input.list.options)
            .filter(option => !option.disabled && option.value.trim())
            .map(option => option.value)
        : []);
      assert.deepEqual(listOptions, ['North district', 'Central district', 'South district'],
        'Datalist must expose enabled, nonempty suggestions through the input');
      await suggestions.fill('Unlisted district');
      assert.equal(await suggestions.inputValue(), 'Unlisted district');
      const details = page.locator('details[name="native-review-sections"]');
      assert.equal(await details.count(), 2);
      await assert.rejects(
        tabToSummary(page, page.locator('details[name="missing-summary"] summary')),
        /must expose exactly one summary/,
        'Missing summary should fail immediately rather than hang on locator.evaluate');
      const groupingSupported = await supportsExclusiveDetails(page);
      await tabToSummary(page, details.nth(0).locator('summary'));
      assert.equal(await details.nth(0).locator('summary').evaluate(el => el === document.activeElement), true);
      await page.keyboard.press('Enter');
      assert.equal(await details.nth(0).getAttribute('open'), '');
      await tabToSummary(page, details.nth(1).locator('summary'));
      assert.equal(await details.nth(1).locator('summary').evaluate(el => el === document.activeElement), true);
      await page.keyboard.press('Enter');
      assert.equal(await details.nth(1).getAttribute('open'), '');
      if (groupingSupported) {
        assert.equal(await details.nth(0).getAttribute('open'), null,
          'Native named disclosure must close the previously open panel');
      }
      // Older engines may keep both disclosures open, but both must stay keyboard-accessible.
      assert.equal(await page.locator('button[commandfor="sample-dialog"]').count(), 1);
      await page.close();
    }
    console.log(engine + ': native HTML input, keyboard, disclosure, 320/390/768 reflow PASS');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
