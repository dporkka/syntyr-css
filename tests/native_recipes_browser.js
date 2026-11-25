// Optional browser regression: node tests/native_recipes_browser.js
// Install playwright and browser engines in a developer environment only.
const { chromium, firefox, webkit } = require("playwright");
const assert = require("node:assert/strict");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

async function run(engine, name) {
  const executablePath = process.env["SYNTYR_TEST_" + name.toUpperCase() + "_EXECUTABLE"];
  const browser = await engine.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
  try {
    const page = await browser.newPage({ viewport: { width: 900, height: 820 }, reducedMotion: "reduce" });
    const errors = [];
    page.on("pageerror", e => errors.push(e.message));
    await page.goto(pathToFileURL(path.resolve(__dirname, "../examples/native-recipes.html")).href);
    const field = page.locator("#example-email");
    const label = page.locator('label[for="example-email"]');
    assert.equal(await field.count(), 1);
    assert.equal(await label.count(), 1);
    assert.equal(await label.evaluate(el => getComputedStyle(el).transform), "none");
    await field.fill("dev@example.com");
    assert.notEqual(await label.evaluate(el => getComputedStyle(el).transform), "none");
    await field.fill("");
    await field.blur();
    assert.equal(await label.evaluate(el => getComputedStyle(el).transform), "none");

    const organization = page.locator("#example-organization");
    const organizationLabel = page.locator('label[for="example-organization"]');
    assert.equal(await organizationLabel.evaluate(el => getComputedStyle(el).transform), "none");
    await organization.fill("Example LLC");
    assert.notEqual(await organizationLabel.evaluate(el => getComputedStyle(el).transform), "none");
    await organization.fill("");
    await organization.blur();
    assert.equal(await organizationLabel.evaluate(el => getComputedStyle(el).transform), "none");

    const invalidFile = page.locator("#native-file-invalid");
    const colors = await invalidFile.evaluate(el => {
      const expected = document.createElement("span");
      expected.style.color = "var(--syn-danger)";
      el.parentElement.appendChild(expected);
      const actual = getComputedStyle(el).borderTopColor;
      const danger = getComputedStyle(expected).color;
      expected.remove();
      return { actual, danger, width: getComputedStyle(el).borderTopWidth };
    });
    assert.equal(colors.actual, colors.danger, "Invalid file input should retain danger border");
    assert.notEqual(colors.width, "0px", "Invalid file input must have a visible border");
    assert.ok(await page.locator("#example-search")
      .evaluate(el => parseFloat(getComputedStyle(el).paddingInlineEnd) >= 30));

    const open = page.getByRole("button", { name: "Open actions" });
    await open.click();
    const popover = page.locator("#native-actions");
    assert.equal(await popover.evaluate(el => el.matches(":popover-open")), true);
    if (await page.evaluate(() => CSS.supports("position-area", "block-end"))) {
      const position = await popover.evaluate(el => getComputedStyle(el).positionArea);
      assert.notEqual(position, "none", "anchored variant should apply native position-area");
    }
    await page.keyboard.press("Escape");
    assert.equal(await popover.evaluate(el => el.matches(":popover-open")), false);

    // Invoker Commands are supported in current engines but may require fallback
    // in older deployments. The explicit close form is always a valid fallback.
    if (await page.evaluate(() => "commandForElement" in HTMLButtonElement.prototype)) {
      await page.getByRole("button", { name: "Open dialog" }).click();
      assert.equal(await page.locator("#native-dialog").evaluate(el => el.open), true);
      await page.locator("#native-dialog").getByRole("button", { name: "Close" }).click();
      assert.equal(await page.locator("#native-dialog").evaluate(el => el.open), false);
    }
    assert.equal(await popover.evaluate(el => getComputedStyle(el).transitionDuration), "0s");

    // Avoid browser zoom-dependent absolute pixel assertions; test no horizontal
    // overflow and focusable code at a narrow viewport instead.
    await page.setViewportSize({ width: 360, height: 780 });
    const rootOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    assert.equal(rootOverflow, false, "native recipes should not overflow the viewport");
    assert.equal(await organizationLabel.evaluate(el => getComputedStyle(el).position), "static");
    const layout = await page.evaluate(() => {
      const label = document.querySelector('label[for="example-organization"]');
      const input = document.querySelector("#example-organization");
      return [getComputedStyle(label).gridRowStart, getComputedStyle(input).gridRowStart];
    });
    assert.deepEqual(layout, ["1", "2"]);
    for (const theme of ["studio", "grid", "noir", "industrial", "terminal", "corporate", "minimal"]) {
      await page.locator("body").evaluate((el, t) => { el.dataset.synTheme = t; }, theme);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
        false, theme + " overflow at 360px");
    }
    const code = page.locator(".syn-code-figure pre");
    assert.equal(await code.getAttribute("tabindex"), "0");
    const animated = await browser.newPage({ reducedMotion: "no-preference" });
    await animated.goto(pathToFileURL(path.resolve(__dirname, "../examples/native-recipes.html")).href);
    const supportsTransitions = await animated.evaluate(() =>
      CSS.supports("transition-behavior", "allow-discrete"));
    if (supportsTransitions) {
      const duration = await animated.locator("#native-actions")
        .evaluate(el => getComputedStyle(el).transitionDuration);
      assert.notEqual(duration, "0s", "native transitions should be enabled when motion is allowed");
    }
    await animated.close();
    assert.deepEqual(errors, []);
    console.log(name + ": native recipe smoke passed");
  } finally {
    await browser.close();
  }
}

async function main() {
  const requested = (process.env.SYNTYR_TEST_ENGINES || "chromium,firefox,webkit").split(",");
  for (const [name, engine] of [["chromium", chromium], ["firefox", firefox], ["webkit", webkit]]) {
    if (!requested.includes(name)) continue;
    try {
      await run(engine, name);
    } catch (error) {
      console.error(name + ": " + error.message);
      process.exitCode = 1;
    }
  }
}

main().catch(err => { console.error(err); process.exitCode = 1; });
