/* Optional browser smoke: task guide -> editable canonical free block. */
"use strict";
const assert = require("node:assert/strict");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright");
const root = path.resolve(__dirname, "..");
const doc = file => pathToFileURL(path.join(root, "docs", file)).href;

(async () => {
  const executablePath = process.env.SYNTYR_CHROMIUM_EXECUTABLE;
  const browser = await chromium.launch({headless: true, ...(executablePath ? {executablePath} : {})});
  try {
    for (const width of [390, 1280]) {
      const page = await browser.newPage({viewport: {width, height: 850}});
      const errors = [];
      page.on("pageerror", error => errors.push(error.message));
      await page.goto(doc("how-to.html"), {waitUntil: "load"});
      const all = page.locator(".howto-card");
      assert.equal(await all.count(), 10);
      assert.equal(await page.locator("#howto-controls").isVisible(), true);
      assert.equal(await page.locator(".howto-card:visible").count(), 10);
      await page.locator("#howto-search").fill("pricing");
      assert.equal(await page.locator(".howto-card:visible").count(), 1);
      assert.equal(await page.locator("#howto-results").innerText(), "Showing 1 of 10 How-To guides.");
      await page.locator("#howto-search").fill("no-such-howto");
      assert.equal(await page.locator("#howto-empty").isVisible(), true);
      await page.locator("#howto-search").fill("pricing");
      await page.locator(".howto-card:visible a[href*='playground.html']").click();
      assert.ok(page.url().endsWith("playground.html#component=block-pricing-trio"));
      await page.locator("#playground-editor-mount .cm-content[contenteditable=true]").waitFor();
      assert.equal(await page.locator("#playground-example").inputValue(), "block-pricing-trio");
      assert.ok((await page.locator("#playground-markup").inputValue()).includes("syn-pricing"));
      assert.equal(await page.locator("#playground-reference-module").innerText(), "syntyr.core.css");
      const frame = page.frameLocator("#playground-preview");
      await frame.locator(".syn-price-card").first().waitFor();
      // Every free block has its own default Studio root; the selected theme
      // must win in rendered preview and copied HTML without mutating source.
      await page.locator("#playground-theme").selectOption("grid");
      await frame.locator("section.syn-root[data-syn-theme=grid]").first().waitFor();
      const accent = await frame.locator("section.syn-root").first().evaluate(el =>
        getComputedStyle(el).getPropertyValue("--syn-accent").trim());
      assert.equal(accent, "#76e7f7", "Nested block root must actually use Grid tokens");
      assert.ok((await page.locator("#playground-markup").inputValue()).includes('data-syn-theme="studio"'),
                "Canonical editable example should not be rewritten when theme changes");
      await page.evaluate(() => Object.defineProperty(navigator, "clipboard", {
        configurable: true,
        value: {writeText: async html => { window.__blockCopied = html; }}
      }));
      await page.locator("#playground-copy").click();
      const copied = await page.evaluate(() => window.__blockCopied);
      assert.equal((copied.match(/data-syn-theme="grid"/g) || []).length, 2,
                   "Outer wrapper and canonical inner block should both adopt Grid");
      assert.equal(copied.includes('data-syn-theme="studio"'), false,
                   "Copy must not accidentally reset the block theme");
      // CodeRabbit regression: valid edited single-quoted HTML must continue
      // honoring the selected theme in preview and export without mutation.
      await page.locator("#playground-markup").evaluate(el => {
        const original = el.value;
        el.value = original.replace(
          'class="syn-root syn-region" data-syn-theme="studio"',
          "class='syn-root syn-region' data-syn-theme='studio'"
        );
        if (el.value === original) throw Error("Expected canonical Studio root");
        el.dispatchEvent(new Event("input", { bubbles: true }));
      });
      await frame.locator("section.syn-root[data-syn-theme=grid]").first().waitFor();
      assert.ok((await page.locator("#playground-markup").inputValue()).includes("data-syn-theme='studio'"),
        "Edited source must remain single-quoted Studio");
      await page.locator("#playground-copy").click();
      const editedCopy = await page.evaluate(() => window.__blockCopied);
      assert.equal(editedCopy.includes("data-syn-theme='studio'"), false,
        "Configured export must not restore the nested Studio theme");
      assert.ok(editedCopy.includes("data-syn-theme='grid'"),
        "Configured export must apply the selected theme to edited single-quoted roots");

      await page.locator("#playground-source-link").click();
      assert.ok(page.url().includes("blocks.html#block-title-pricing-trio"));
      await page.locator(".blocks-edit").first().waitFor();
      assert.equal(await page.locator(".blocks-edit").count(), 20);
      await page.locator("#blocks-search").fill("onboarding");
      assert.equal(await page.locator(".blocks-card:visible").count(), 1);
      await page.locator(".blocks-card:visible .blocks-edit").click();
      assert.ok(page.url().endsWith("playground.html#component=block-onboarding-steps"));
      assert.equal(await page.locator("#playground-example").inputValue(), "block-onboarding-steps");
      assert.equal(await page.locator("#playground-reference-module").innerText(),
                   "syntyr.core.css + syntyr.recipes.css");
      await frame.locator(".syn-root").first().waitFor();
      assert.ok((await page.locator("#playground-markup").inputValue()).includes("syn-activity-list"));
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true,
                   "unexpected horizontal viewport overflow");
      assert.deepEqual(errors, []);
      await page.close();

      const noJs = await browser.newContext({viewport: {width, height: 850}, javaScriptEnabled: false});
      const fallbackPage = await noJs.newPage();
      await fallbackPage.goto(doc("how-to.html"), {waitUntil: "load"});
      assert.equal(await fallbackPage.locator(".howto-card:visible").count(), 10);
      assert.equal(await fallbackPage.locator("#howto-controls").isVisible(), false);
      assert.equal(await fallbackPage.locator(".howto-card a[href*='playground.html']").count(), 10);
      await noJs.close();
      console.log(`PASS chromium ${width}px: How-To search / static fallback / free block / CodeMirror`);
    }
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
