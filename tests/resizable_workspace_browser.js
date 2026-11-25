// Developer-only browser regression: node tests/resizable_workspace_browser.js
// Requires separately installed Playwright and browser executables; none ship in CSS.
const { chromium, firefox, webkit } = require("playwright");
const assert = require("node:assert/strict");
const http = require("node:http");
const path = require("node:path");
const fs = require("node:fs");

const ROOT = path.resolve(__dirname, "..");
const allowed = new Map([
  ["/examples/resizable-workspace.html", "text/html; charset=utf-8"],
  ["/examples/resizable-workspace.mjs", "text/javascript; charset=utf-8"],
  ["/dist/syntyr.core.css", "text/css; charset=utf-8"],
  ["/dist/syntyr.recipes.css", "text/css; charset=utf-8"],
]);

async function exercise(engine, name, base) {
  const key = "SYNTYR_TEST_" + name.toUpperCase() + "_EXECUTABLE";
  const browser = await engine.launch({
    headless: true, timeout: 15000,
    ...(process.env[key] ? { executablePath: process.env[key] } : {}),
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1100, height: 800 } });
    const errors = [];
    page.on("pageerror", error => errors.push(error.message));
    await page.goto(base + "/examples/resizable-workspace.html");
    const separator = page.getByRole("separator");
    await separator.waitFor({ state: "visible" });
    assert.equal(await separator.getAttribute("aria-valuenow"), "35");
    assert.equal(await separator.getAttribute("tabindex"), "0");

    await separator.focus();
    await page.keyboard.press("End");
    assert.equal(await separator.getAttribute("aria-valuenow"), "70");
    await page.keyboard.press("ArrowRight");
    assert.equal(await separator.getAttribute("aria-valuenow"), "70", "max is clamped");
    await page.keyboard.press("Home");
    assert.equal(await separator.getAttribute("aria-valuenow"), "20");
    await page.keyboard.press("ArrowRight");
    assert.equal(await separator.getAttribute("aria-valuenow"), "22");
    await page.keyboard.press("Shift+ArrowRight");
    assert.equal(await separator.getAttribute("aria-valuenow"), "32");

    async function assertRenderedFraction() {
      const leading = await page.locator("#asset-list").boundingBox();
      const total = await page.locator(".syn-resizable-workspace__panes").boundingBox();
      const reported = Number(await separator.getAttribute("aria-valuenow"));
      const rendered = leading.width / total.width * 100;
      assert(Math.abs(rendered - reported) < 1,
        `ARIA reports ${reported}% but rendered split is ${rendered}%`);
    }
    await assertRenderedFraction();

    const frame = await page.locator(".syn-resizable-workspace__panes").boundingBox();
    const grip = await separator.boundingBox();
    await page.mouse.move(grip.x + grip.width / 2, grip.y + grip.height / 2);
    const initialValue = Number(await separator.getAttribute("aria-valuenow"));
    await page.mouse.down();
    assert.equal(Number(await separator.getAttribute("aria-valuenow")), initialValue,
      "stationary LTR pointerdown must not jump the divider");
    await page.mouse.move(frame.x + frame.width * .58, grip.y + grip.height / 2, { steps: 5 });
    await page.mouse.up();
    let value = Number(await separator.getAttribute("aria-valuenow"));
    assert(value >= 56 && value <= 60, "pointer drag must resize: " + value);
    await assertRenderedFraction();

    // In RTL the visual inline-start edge is the right side.
    await page.locator(".syn-root").evaluate(el => { el.dir = "rtl"; });
    await separator.focus();
    const before = Number(await separator.getAttribute("aria-valuenow"));
    await page.keyboard.press("ArrowRight");
    assert.equal(Number(await separator.getAttribute("aria-valuenow")), before - 2);
    await assertRenderedFraction();
    // Pointer direction also flips in RTL; moving toward visual right narrows
    // the leading pane instead of widening it.
    const rtlBox = await page.locator(".syn-resizable-workspace__panes").boundingBox();
    const rtlGrip = await separator.boundingBox();
    await page.mouse.move(rtlGrip.x + rtlGrip.width / 2, rtlGrip.y + rtlGrip.height / 2);
    const rtlInitial = Number(await separator.getAttribute("aria-valuenow"));
    await page.mouse.down();
    assert.equal(Number(await separator.getAttribute("aria-valuenow")), rtlInitial,
      "stationary RTL pointerdown must not jump the divider");
    await page.mouse.move(rtlBox.x + rtlBox.width * .7, rtlGrip.y + rtlGrip.height / 2, { steps: 3 });
    await page.mouse.up();
    const rtlValue = Number(await separator.getAttribute("aria-valuenow"));
    assert(rtlValue >= 28 && rtlValue <= 32, "RTL pointer should invert: " + rtlValue);
    await assertRenderedFraction();
    await page.locator(".syn-root").evaluate(el => { el.dir = "ltr"; });

    // Synthetic simultaneous touch pointers; stub capture for DOM events
    // because pointer capture requires a browser-active hardware pointer.
    const multiTouch = await separator.evaluate(el => {
      const panes = el.closest("[data-syn-resizable]").querySelector(".syn-resizable-workspace__panes");
      const box = panes.getBoundingClientRect();
      const grip = el.getBoundingClientRect();
      const start = Number(el.getAttribute("aria-valuenow"));
      el.setPointerCapture = () => {};
      el.hasPointerCapture = () => false;
      const send = (type, id, x) => el.dispatchEvent(new PointerEvent(type, {
        bubbles: true, button: 0, pointerId: id, pointerType: "touch",
        clientX: x, clientY: grip.y + grip.height / 2,
      }));
      const point = grip.x + grip.width / 2;
      send("pointerdown", 41, point);
      send("pointerdown", 42, point);
      send("pointerup", 42, point);
      send("pointermove", 41, box.x + box.width * .46);
      const after = Number(el.getAttribute("aria-valuenow"));
      send("pointerup", 41, point);
      return { start, after };
    });
    assert(multiTouch.after > multiTouch.start + 5,
      "second touch must not steal first pointer: " + JSON.stringify(multiTouch));

    // Container queries follow the workspace's width, not just viewport width.
    await page.locator(".syn-resizable-workspace").evaluate(el => { el.style.inlineSize = "400px"; });
    assert.equal(await separator.isVisible(), false, "narrow embedded container hides handle");
    const stackedGap = await page.locator("#asset-detail").evaluate(el =>
      Number.parseFloat(getComputedStyle(el).marginBlockStart));
    assert(stackedGap >= 8, "stacked panes should retain a visible separation: " + stackedGap);
    await page.locator(".syn-resizable-workspace").evaluate(el => { el.style.removeProperty("inline-size"); });

    await page.setViewportSize({ width: 320, height: 760 });
    assert.equal(await separator.isVisible(), false, "narrow container hides handle");
    assert.equal(await page.locator(".syn-resizable-workspace__pane").count(), 2);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
    assert.equal(overflow, false, "320px layout has no horizontal overflow");
    await page.locator(".syn-root").evaluate(el => { document.documentElement.style.fontSize = "64px"; });
    const highZoomOverflow = await page.evaluate(() =>
      document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
    assert.equal(highZoomOverflow, false, "enlarged-text layout must not overflow page");
    await page.evaluate(() => { document.documentElement.style.removeProperty("font-size"); });
    assert.deepEqual(errors, []);

    // The no-script fallback must not expose an inert keyboard focus target.
    const fallback = await browser.newPage({ viewport: { width: 1100, height: 800 }, javaScriptEnabled: false });
    await fallback.goto(base + "/examples/resizable-workspace.html");
    assert.equal(await fallback.locator('[role="separator"]').isVisible(), false);
    assert.equal(await fallback.locator(".syn-resizable-workspace__pane").count(), 2);
    await fallback.close();

    // Color semantics remain visible to native forced-colors mode.
    const colors = await browser.newPage({ viewport: { width: 1100, height: 800 }, forcedColors: "active" });
    await colors.goto(base + "/examples/resizable-workspace.html");
    await colors.getByRole("separator").waitFor({ state: "visible" });
    await colors.getByRole("separator").focus();
    const outline = await colors.getByRole("separator").evaluate(el => getComputedStyle(el).outlineStyle);
    assert.notEqual(outline, "none");
    const contrast = await colors.getByRole("separator").evaluate(el => ({
      grip: getComputedStyle(el, "::before").backgroundColor,
      panel: getComputedStyle(el.parentElement.children[0]).backgroundColor,
    }));
    assert.notEqual(contrast.grip, contrast.panel, "forced-colors grip must contrast with panel");
    await colors.close();
    await page.close();
    console.log("PASS", name, "keyboard/pointer/RTL/narrow/fallback/forced-colors");
  } finally {
    await browser.close();
  }
}

async function main() {
  const server = http.createServer((req, res) => {
    const pathname = new URL(req.url, "http://localhost").pathname;
    if (!allowed.has(pathname)) { res.writeHead(404); res.end(); return; }
    const full = path.join(ROOT, pathname.slice(1));
    res.writeHead(200, { "Content-Type": allowed.get(pathname) });
    fs.createReadStream(full).pipe(res);
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const base = "http://127.0.0.1:" + server.address().port;
  try {
    const engines = { chromium, firefox, webkit };
    const selected = (process.env.SYNTYR_TEST_BROWSERS || "chromium,firefox,webkit").split(",");
    for (const name of selected) {
      if (!Object.hasOwn(engines, name)) throw Error("Unknown browser: " + name);
      await exercise(engines[name], name, base);
    }
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
