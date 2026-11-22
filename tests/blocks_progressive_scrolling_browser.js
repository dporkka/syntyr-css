/* Browser contract: CSS-first batches, native fragment navigation, optional search. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const {pathToFileURL} = require("node:url");
const {chromium, firefox} = require("playwright");
const root = path.resolve(__dirname, "..");
const href = pathToFileURL(path.join(root, "docs", "blocks.html")).href;
const blocks = JSON.parse(fs.readFileSync(path.join(root, "blocks", "manifest.json"), "utf8")).blocks;
const iconCount = JSON.parse(fs.readFileSync(path.join(root, "blocks", "icons.json"), "utf8")).icons.length;

async function checkFilteredBatchCount(page, batch, items, results, total, noun) {
  const summary = batch.locator(":scope > summary");
  assert.notEqual(await batch.getAttribute("open"), null, "Filtering should open the matching batch");
  for (const open of [false, true]) {
    await summary.click();
    assert.equal((await batch.getAttribute("open")) !== null, open);
    const visible = await page.locator(items + ":visible").count();
    const expected = `Showing ${visible} of ${total} ${noun}.`;
    await page.waitForFunction(({results, expected}) =>
      document.querySelector(results).textContent === expected, {results, expected}, {timeout: 2000});
  }
}

(async () => {
  for (const engine of [chromium, ...((process.argv.includes("--firefox")) ? [firefox] : [])]) {
    const executable = engine === chromium
      ? process.env.SYNTYR_CHROMIUM_EXECUTABLE
      : process.env.SYNTYR_FIREFOX_EXECUTABLE;
    const browser = await engine.launch({headless: true, ...(executable ? {executablePath: executable} : {})});
    try {
      for (const javascriptEnabled of [false, true]) {
        const context = await browser.newContext({javaScriptEnabled: javascriptEnabled, viewport: {width: 390, height: 844}});
        const page = await context.newPage();
        const errors = [];
        page.on("pageerror", error => errors.push(error.message));
        await page.goto(href, {waitUntil: "load"});
        assert.equal(await page.locator("[data-block-id]").count(), blocks.length);
        assert.equal(await page.locator("[data-icon-id]").count(), iconCount);
        assert.equal(await page.locator("details[data-block-batch]").count(), Math.ceil(blocks.length / 12) - 1);
        assert.equal(await page.locator("[data-block-id]:visible").count(), 12);
        assert.equal(await page.locator("details[data-icon-batch]").count(), Math.ceil(iconCount / 30) - 1);
        assert.equal(await page.locator("[data-icon-id]:visible").count(), 30);
        assert.equal(await page.locator("details[data-block-batch][open]").count(), 0);
        assert.equal(await page.locator("details[data-icon-batch][open]").count(), 0);

        // The scroll-snap strip must remain navigable by keyboard without JS.
        const rail = page.locator(".blocks-category-nav");
        await rail.evaluate(e => { e.scrollLeft = 0; });
        await rail.locator("a").last().focus();
        assert.ok((await rail.evaluate(e => e.scrollLeft)) > 0,
          "Focus should reveal the last category in the horizontal strip");

        const firstLater = page.locator('details[data-block-batch]').first();
        await firstLater.locator(":scope > summary").click();
        assert.equal(await page.locator("[data-block-id]:visible").count(), 24);
        await firstLater.locator(":scope > summary").click();
        assert.equal(await page.locator("[data-block-id]:visible").count(), 12);
        const nextIcons = page.locator('details[data-icon-batch]').first();
        await nextIcons.locator(":scope > summary").click();
        assert.equal(await page.locator("[data-icon-id]:visible").count(), 60);
        await nextIcons.locator(":scope > summary").click();
        assert.equal(await page.locator("[data-icon-id]:visible").count(), 30);

        const lastBlock = blocks[blocks.length - 1];
        await page.goto(href + "#block-title-" + lastBlock.id, {waitUntil: "load"});
        const lastCard = page.locator('[data-block-id="' + lastBlock.id + '"]');
        assert.equal(await lastCard.isVisible(), true, "Direct fragment link did not reveal the last batch");
        assert.equal(await lastCard.locator('xpath=ancestor::details[@data-block-batch]').getAttribute("open") !== null, true);
        if (javascriptEnabled) {
          await page.goto(href, {waitUntil: "load"});
          await page.locator("#blocks-category").selectOption("Applications");
          assert.equal(await page.locator("[data-block-id]:visible").count(), blocks.filter(b => b.category === "Applications").length);
          await checkFilteredBatchCount(page, firstLater, "[data-block-id]", "#blocks-results", blocks.length, "blocks");
          await page.locator("#blocks-category").selectOption("all");
          assert.equal(await page.locator("[data-block-id]:visible").count(), 12);
          await page.locator("#blocks-search").fill("pricing");
          assert.ok(await page.locator("[data-block-id]:visible").count() > 0);
          await page.locator("#blocks-search").fill("");
          assert.equal(await page.locator("[data-block-id]:visible").count(), 12);
          await page.locator("#blocks-icon-search").fill("moon");
          assert.equal(await page.locator("[data-icon-id]:visible").count(), 1);
          const moonBatch = page.locator('details[data-icon-batch]').filter({has: page.locator('[data-icon-id="moon"]')});
          await checkFilteredBatchCount(page, moonBatch, "[data-icon-id]", "#blocks-icon-results", iconCount, "icons");
          await page.locator("#blocks-icon-search").fill("");
          assert.equal(await page.locator("[data-icon-id]:visible").count(), 30);
          const categories = page.locator(".blocks-category-nav");
          assert.ok((await categories.evaluate(e => getComputedStyle(e).scrollSnapType)).startsWith("inline"));
          await page.locator('[data-block-category-link="Applications"]').click();
          assert.equal(await page.locator("#blocks-category").inputValue(), "Applications");
          assert.ok(await page.locator("[data-block-id]:visible").count() > 0);
        }
        assert.deepEqual(errors, []);
        console.log("PASS " + engine.name() + " JS=" + javascriptEnabled + " progressive block and icon batches");
        await context.close();
      }
    } finally { await browser.close(); }
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
