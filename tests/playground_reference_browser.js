/* Optional live browser regression for the catalog-to-playground workflow. */
'use strict';
const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require('playwright');

const root = path.resolve(__dirname, '..');
const gallery = pathToFileURL(path.join(root, 'docs/catalog.html')).href;

(async () => {
  const executablePath = process.env.SYNTYR_CHROMIUM_EXECUTABLE;
  const browser = await chromium.launch({headless: true, ...(executablePath ? {executablePath} : {})});
  try {
    for (const width of [390, 1280]) {
      const page = await browser.newPage({viewport: {width, height: 850}});
      const errors = [];
      page.on('pageerror', error => errors.push(String(error)));
      await page.goto(gallery, {waitUntil: 'load'});
      const editLinks = page.locator('.catalog-edit');
      const cards = await page.locator('.catalog-card').count();
      assert.ok(cards >= 8);
      assert.equal(await editLinks.count(), cards);
      await editLinks.first().click();
      assert.ok(page.url().includes('#component=catalog-buttons-title'));
      const frame = page.frameLocator('#playground-preview');
      await frame.locator('.syn-button--primary').first().waitFor();
      assert.equal(await page.locator('#playground-example').inputValue(), 'catalog-buttons-title');
      assert.equal(await page.locator('#playground-reference-module').innerText(), 'syntyr.core.css');
      assert.equal(await frame.locator('link[rel="stylesheet"]').count(), 1);
      assert.equal(await frame.locator('link[rel="stylesheet"]').first().getAttribute('href'),
        '../dist/syntyr.core.css');
      await page.locator('#playground-example').selectOption('catalog-interaction-card-4');
      await frame.locator('meter').first().waitFor();
      assert.ok((await page.locator('#playground-required-stylesheets').innerText()).includes('syntyr.semantic.css'));
      assert.equal(await frame.locator('link[rel="stylesheet"]').count(), 2);
      await page.locator('#playground-example').selectOption('catalog-buttons-title');
      assert.ok((await page.locator('#playground-markup').inputValue()).includes('syn-button--primary'));
      const editor = page.locator('#playground-editor-mount .cm-content[contenteditable="true"]');
      await editor.waitFor();
      assert.equal(await page.locator('#playground-markup').isVisible(), false);
      assert.equal(await page.locator('#playground-editor-mount').getAttribute('data-editor'), 'codemirror6');

      await page.locator('#playground-search').fill('breadcrumb');
      const searchText = await page.locator('#playground-search-status').innerText();
      const counts = /^(\d+) of (\d+) examples match\./.exec(searchText);
      assert.ok(counts && Number(counts[1]) >= 1, 'Breadcrumb search must find a result: ' + searchText);
      await page.locator('#playground-example').selectOption('catalog-breadcrumbs-title');
      await frame.locator('.syn-breadcrumbs').first().waitFor();
      assert.ok((await page.locator('#playground-reference-description').innerText()).length > 5);

      await page.locator('#playground-example').selectOption('actions');
      await frame.locator('.syn-panel').first().waitFor();
      assert.ok((await page.locator('#playground-required-stylesheets').innerText()).includes('syntyr.utilities.css'));
      assert.equal(await frame.locator('link[rel="stylesheet"]').count(), 2);
      await page.locator('#playground-panel-radius').evaluate(el => {
        el.value = '22';
        el.dispatchEvent(new Event('input', {bubbles: true}));
      });
      await page.waitForFunction(() => {
        const frame = document.querySelector('#playground-preview');
        const panel = frame?.contentDocument?.querySelector('.syn-panel');
        return panel && getComputedStyle(panel).borderTopLeftRadius === '22px';
      });
      assert.equal(await page.locator('#playground-panel-radius-value').innerText(), '22px');
      await page.locator('#playground-viewport').selectOption('390');
      assert.ok(await page.locator('#playground-preview').evaluate(el => el.getBoundingClientRect().width <= 391));
      await page.locator('#playground-viewport').selectOption('1200');
      const dimensions = await page.locator('.playground-canvas').evaluate(canvas => ({
        frame: canvas.querySelector('#playground-preview').getBoundingClientRect().width,
        view: canvas.clientWidth,
        scroll: canvas.scrollWidth
      }));
      assert.ok(Math.abs(dimensions.frame - 1200) < 2, `Desktop preview should be 1200px: ${JSON.stringify(dimensions)}`);
      assert.ok(dimensions.scroll > dimensions.view, 'Fixed desktop preview should scroll horizontally');
      await page.locator('#playground-viewport').selectOption('fluid');
      assert.ok(await page.locator('#playground-preview').evaluate(el => el.getBoundingClientRect().width <= el.parentElement.clientWidth));
      await page.locator('#playground-theme').selectOption('grid');
      await frame.locator('body[data-syn-theme="grid"]').waitFor();

      await editor.click();
      await page.keyboard.press('ControlOrMeta+A');
      await page.keyboard.insertText('<p id="sandbox-check">Safe</p><script>parent.document.body.dataset.injected="yes"</script>');
      await page.waitForFunction(() => document.querySelector('#playground-markup')?.value.includes('sandbox-check'));
      await frame.locator('#sandbox-check').waitFor();
      assert.equal(await page.locator('body').getAttribute('data-injected'), null);
      assert.ok(await page.locator('#playground-editor-mount .cm-line span').count() > 0, 'HTML syntax highlighting is missing');
      await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', {
        configurable: true,
        value: {writeText: async text => { window.__copiedHTML = text; }}
      }));
      await page.locator('#playground-copy').click();
      const copiedHTML = await page.evaluate(() => window.__copiedHTML);
      assert.ok(copiedHTML.includes('data-syn-theme="grid"'));
      assert.ok(copiedHTML.includes('--syn-panel-radius: 22px'));
      assert.ok(copiedHTML.includes('<p id="sandbox-check">Safe</p>'));
      await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', {configurable: true, value: undefined}));
      await page.locator('#playground-copy').click();
      const manualFallback = page.locator('#playground-copy-fallback');
      assert.equal(await manualFallback.isVisible(), true, 'Manual copy fallback must be exposed');
      const fallbackHTML = await manualFallback.inputValue();
      assert.equal(fallbackHTML, copiedHTML, 'Manual copy must include the complete configured HTML');
      assert.equal(await manualFallback.evaluate(el => el.selectionStart === 0 && el.selectionEnd === el.value.length), true);
      await editor.click();
      await page.keyboard.press('ControlOrMeta+Z');
      await page.waitForFunction(() => document.querySelector('#playground-markup')?.value.includes('Deployment ready'));
      await frame.locator('.syn-panel').first().waitFor();
      assert.equal(errors.length, 0, errors.join('\n'));
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
      assert.equal(overflow, false, `Horizontal overflow at ${width}px`);
      console.log(`PASS chromium ${width}px CodeMirror / gallery link / search / tokens / width / sandbox`);
      await page.close();
      const fallback = await browser.newContext({viewport: {width, height: 800}, javaScriptEnabled: false});
      const fallbackPage = await fallback.newPage();
      await fallbackPage.goto(pathToFileURL(path.join(root, 'docs/playground.html')).href);
      assert.equal(await fallbackPage.locator('#playground-markup').isVisible(), true);
      assert.equal(await fallbackPage.locator('#playground-editor-mount').isVisible(), false);
      await fallbackPage.locator('#playground-markup').fill('<p>Native fallback</p>');
      assert.equal(await fallbackPage.locator('#playground-markup').inputValue(), '<p>Native fallback</p>');
      await fallback.close();
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
