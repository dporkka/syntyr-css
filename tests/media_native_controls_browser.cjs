/* Run with NODE_PATH pointing to an installed Playwright package:
   NODE_PATH=/path/to/node_modules node tests/media_native_controls_browser.cjs */
const assert = require("node:assert/strict");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright");

async function main() {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({
      viewport: { width: 390, height: 800 },
      javaScriptEnabled: false,
      reducedMotion: "reduce"
    });
    await page.goto(pathToFileURL(path.resolve(__dirname, "../examples/media-entertainment.html")).href);
    const rail = page.locator(".syn-media-rail--controls").first();
    const initial = await rail.evaluate(el => ({
      left: el.scrollLeft,
      clientWidth: el.clientWidth,
      scrollWidth: el.scrollWidth,
      supports: CSS.supports("selector(::scroll-button(inline-end))") &&
        CSS.supports("anchor-name", "--syn-media-rail"),
      button: getComputedStyle(el, "::scroll-button(inline-end)").content,
      marker: getComputedStyle(el.firstElementChild, "::scroll-marker").content,
      scrollbar: getComputedStyle(el).scrollbarWidth,
    }));
    assert.ok(initial.scrollWidth > initial.clientWidth, "rail remains horizontally scrollable");
    assert.notEqual(initial.scrollbar, "none", "fallback scrollbar remains available");

    if (initial.supports) {
      assert.match(initial.button, /Scroll forward/, "scroll button has an accessible name");
      assert.match(initial.marker, /Long Orbit/, "marker has a distinct label");
      await rail.scrollIntoViewIfNeeded();
      const bounds = await rail.boundingBox();
      assert.ok(bounds, "rail exists");
      await page.mouse.click(bounds.x + bounds.width - 27, bounds.y + 26);
      await page.waitForTimeout(250);
      const after = await rail.evaluate(el => el.scrollLeft);
      assert.ok(after > initial.left, `scroll button should advance: ${initial.left} => ${after}`);
      console.log("PASS chromium native CSS buttons and markers", initial, { after });
    } else {
      console.log("SKIP native generated buttons: browser does not support them");
    }
    await rail.focus();
    await page.keyboard.press("End");
    await page.waitForTimeout(120);
    assert.ok(await rail.evaluate(el => el.scrollLeft) > 0,
      "keyboard scrolling works with JavaScript disabled");
    console.log("PASS accessible scrollbar and keyboard fallback (JavaScript disabled)");
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
