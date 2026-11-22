/* Run with NODE_PATH pointing to an installed Playwright package:
   NODE_PATH=/path/to/node_modules node tests/media_native_controls_browser.cjs */
const assert = require("node:assert/strict");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium, firefox, webkit } = require("playwright");
const engine = process.env.SYNTYR_BROWSER || "chromium";
const browserType = { chromium, firefox, webkit }[engine];
if (!browserType) throw new Error(`Unknown browser: ${engine}`);

async function main() {
  const browser = await browserType.launch({ headless: true });
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
    const CSS_SUPPORT_MARKERS = await rail.evaluate(el =>
      CSS.supports("scroll-marker-group", "after") &&
      CSS.supports("anchor-name", "--syn-media-rail"));
    assert.ok(initial.scrollWidth > initial.clientWidth, "rail remains horizontally scrollable");
    // OS accessibility preferences and headless browsers can hide scrollbar
    // painting even when overflow-x stays scrollable.
    const overflow = await rail.evaluate(el => getComputedStyle(el).overflowX);
    assert.equal(overflow, "auto", "fallback horizontal scrolling remains enabled");

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
      console.log(`PASS ${engine} native CSS buttons and markers`, initial, { after });
    } else {
      console.log("SKIP native generated buttons: browser does not support them");
    }
    // Independent keyboard check: do not inherit the button's scroll position.
    await rail.evaluate(el => { el.scrollLeft = 0; });
    await page.waitForTimeout(80);
    const keyboardStart = await rail.evaluate(el => el.scrollLeft);
    assert.equal(keyboardStart, 0, "keyboard scroll test begins at the start");
    await rail.focus();
    await page.keyboard.press("ArrowRight");
    await page.waitForTimeout(300);
    const keyboardEnd = await rail.evaluate(el => el.scrollLeft);
    assert.ok(keyboardEnd > keyboardStart,
      `keyboard ArrowRight must scroll independently: ${keyboardStart} -> ${keyboardEnd}`);
    console.log(`PASS ${engine} independent keyboard fallback (JavaScript disabled)`);

    // Trackpads and wheel users must be able to navigate without a generated
    // button even when the OS hides scrollbar painting.
    await rail.evaluate(el => { el.scrollLeft = 0; });
    await page.waitForTimeout(70);
    const wheelStart = await rail.evaluate(el => el.scrollLeft);
    await rail.scrollIntoViewIfNeeded();
    const wheelBounds = await rail.boundingBox();
    await page.mouse.move(wheelBounds.x + wheelBounds.width / 2,
      wheelBounds.y + wheelBounds.height / 2);
    await page.mouse.wheel(160, 0);
    await page.waitForTimeout(300);
    const wheelEnd = await rail.evaluate(el => el.scrollLeft);
    assert.ok(wheelEnd > wheelStart,
      `horizontal wheel must scroll rail: ${wheelStart} -> ${wheelEnd}`);
    console.log(`PASS ${engine} horizontal wheel fallback (JavaScript disabled)`);

    // Stress-test generated marker groups: 30 markers must fit a 320px screen
    // without overflowing the page, and remain reachable by local scrolling.
    if (initial.supports && CSS_SUPPORT_MARKERS) {
      await page.setViewportSize({ width: 320, height: 700 });
      await rail.evaluate(el => {
        const existing = el.querySelector("article");
        for (let i = el.children.length; i < 30; i++) {
          const card = existing.cloneNode(true);
          card.dataset.synScrollLabel = `Story ${i + 1}`;
          el.appendChild(card);
        }
      });
      const markerLayout = await rail.evaluate(el => {
        const style = getComputedStyle(el, "::scroll-marker-group");
        return { width: parseFloat(style.width), overflowX: style.overflowX,
          viewport: innerWidth, pageWidth: document.documentElement.scrollWidth,
          groupContent: 30 * 16 + 29 * 8 };
      });
      assert.ok(markerLayout.width <= markerLayout.viewport - 8, JSON.stringify(markerLayout));
      assert.equal(markerLayout.overflowX, "auto", JSON.stringify(markerLayout));
      assert.ok(markerLayout.groupContent > markerLayout.width, "stress markers exceed group width");
      assert.ok(markerLayout.pageWidth <= markerLayout.viewport + 1, JSON.stringify(markerLayout));
      console.log("PASS 30 native markers confined to independently scrollable group", markerLayout);
    }

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
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
