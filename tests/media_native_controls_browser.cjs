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
    await page.reload();
    await rail.evaluate(el => el.classList.remove("syn-media-rail--markers", "syn-media-rail--controls"));
    const baseRail = page.locator(".syn-media-rail").first();
    await baseRail.focus();
    const beforeKeyboard = await baseRail.evaluate(el => el.scrollLeft);
    assert.equal(beforeKeyboard, 0, "keyboard check starts at the beginning of the rail");
    // Tab to a card beyond the visible area to exercise native focus scrolling.
    for (let i = 0; i < 4; i++) await page.keyboard.press("Tab");
    await page.waitForFunction(({ el, beforeKeyboard }) => el.scrollLeft > beforeKeyboard,
      { el: await baseRail.elementHandle(), beforeKeyboard }, { timeout: 2000 });
    console.log("PASS accessible scrollbar and keyboard fallback (JavaScript disabled)");

    if (initial.supports) {
      await page.reload();
      await rail.evaluate(el => el.parentElement.setAttribute("dir", "rtl"));
      await rail.scrollIntoViewIfNeeded();
      const bounds = await rail.boundingBox();
      assert.ok(bounds, "RTL rail exists");
      const clickForward = bounds.x + 27;
      const clickBackward = bounds.x + bounds.width - 27;
      const buttonY = bounds.y + 26;
      await page.mouse.click(clickForward, buttonY);
      await page.waitForFunction(el => el.scrollLeft < 0, await rail.elementHandle(), { timeout: 2000 });
      const advanced = await rail.evaluate(el => el.scrollLeft);
      await page.mouse.click(clickBackward, buttonY);
      await page.waitForFunction(({ el, advanced }) => el.scrollLeft > advanced,
        { el: await rail.elementHandle(), advanced }, { timeout: 2000 });
      const labels = await rail.evaluate(el => ["inline-start", "inline-end"].map(side =>
        getComputedStyle(el, `::scroll-button(${side})`).content));
      assert.deepEqual(labels, ['"→" / "Scroll backward"', '"←" / "Scroll forward"']);
      console.log("PASS RTL buttons advance left and return right within the rail");
    }

    await page.reload();
    if (await rail.evaluate(el => getComputedStyle(el, "::scroll-marker-group").display === "flex")) {
      await rail.evaluate(el => {
        for (let i = el.children.length; i < 30; i++) {
          const card = document.createElement("article");
          card.setAttribute("data-syn-scroll-label", `Story ${i + 1}`);
          card.textContent = `Story ${i + 1}`;
          el.append(card);
        }
      });
      await rail.scrollIntoViewIfNeeded();
      const bounds = await rail.boundingBox();
      assert.ok(bounds, "long marker rail exists");
      const [documentWidth, viewportWidth] = await page.evaluate(() => [
        document.documentElement.scrollWidth, document.documentElement.clientWidth,
      ]);
      assert.equal(documentWidth, viewportWidth, "markers do not widen the page");
      const markerY = bounds.y + bounds.height + 22;
      const markerX = bounds.x + bounds.width - 14;
      await page.mouse.move(markerX, markerY);
      await page.mouse.wheel(1500, 0);
      await page.waitForTimeout(250);
      await page.mouse.click(markerX, markerY);
      await page.waitForFunction(el => el.scrollWidth - el.clientWidth - el.scrollLeft <= 1,
        await rail.elementHandle(), { timeout: 2000 });
      console.log("PASS long marker strip stays local and the last marker is clickable");
    }
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
