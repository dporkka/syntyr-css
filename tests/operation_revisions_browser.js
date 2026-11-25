/* Developer-only browser regression: node tests/operation_revisions_browser.js.
   Requires optional Playwright browsers; never part of the CSS distribution.
   4x text-size stress is more demanding than native 400% browser UI zoom. */
"use strict";
const {chromium, firefox, webkit} = require("playwright");
const assert = require("node:assert/strict");
const path = require("node:path");
const {pathToFileURL} = require("node:url");

const url = pathToFileURL(path.resolve(__dirname, "../examples/operation-revisions.html")).href;

async function check(engine, name) {
  const browser = await engine.launch({headless: true});
  try {
    const page = await browser.newPage({viewport: {width: 320, height: 800}, reducedMotion: "reduce"});
    const errors = [];
    page.on("pageerror", e => errors.push(e.message));
    await page.goto(url, {waitUntil: "load"});
    assert.equal(await page.locator(".syn-operation-feedback").count(), 5);
    assert.equal(await page.locator(".syn-change-pair").count(), 4);
    assert.equal(await page.locator("script").count(), 0);
    const styles = await page.locator('link[rel="stylesheet"]').evaluateAll(
      links => links.map(link => ({href: link.getAttribute("href"), loaded: !!link.sheet}))
    );
    assert.ok(styles.length >= 2 && styles.every(s => s.loaded), JSON.stringify(styles));
    for (const [width, textScale] of [[320, 1], [390, 1], [1280, 1], [320, 2], [320, 4]]) {
      await page.setViewportSize({width, height: 800});
      await page.evaluate(scale => document.documentElement.style.fontSize = (16 * scale) + "px", textScale);
      const dimensions = await page.evaluate(() => ({
        client: document.documentElement.clientWidth,
        scroll: document.documentElement.scrollWidth
      }));
      assert.ok(dimensions.scroll <= dimensions.client + 1,
        `${name}: ${width}px at ${textScale}x root text: ${JSON.stringify(dimensions)}`);
    }
    await page.emulateMedia({forcedColors: "active", reducedMotion: "reduce"});
    const border = await page.locator(".syn-operation-feedback").first().evaluate(
      element => parseFloat(getComputedStyle(element).borderInlineStartWidth)
    );
    assert.ok(border >= 4, "operation state must retain its non-color border distinction");
    await page.keyboard.press("Tab");
    assert.equal(await page.evaluate(() => document.activeElement?.textContent.trim()),
      "Skip to main content");
    assert.deepEqual(errors, [], "static example must have no browser-side exceptions");
    console.log(`PASS ${name}: layout, 4x text stress, states, forced colors and keyboard`);
  } finally {
    await browser.close();
  }
}

(async () => {
  const engines = {chromium, firefox, webkit};
  const requested = (process.env.SYNTYR_TEST_ENGINES ?? "chromium,firefox,webkit")
    .split(",").map(name => name.trim());
  const unsupported = requested.filter(name => !Object.hasOwn(engines, name));
  if (unsupported.length) {
    throw new Error(`Unsupported browser engine selection: ${unsupported.map(JSON.stringify).join(", ")}`);
  }
  if (requested.length === 0) {
    throw new Error("No valid browser engines selected");
  }
  for (const name of new Set(requested)) {
    await check(engines[name], name);
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
