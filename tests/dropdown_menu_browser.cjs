// Optional real-browser regression for the opt-in ARIA menu adapter.
const assert = require("node:assert/strict");
const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const { chromium, firefox, webkit } = require("playwright");
const ROOT = path.resolve(__dirname, "..");

function serve() {
  const server = http.createServer((req, res) => {
    const relative = new URL(req.url, "http://localhost").pathname;
    const full = path.resolve(ROOT, "." + relative);
    if (!full.startsWith(ROOT + path.sep) || !fs.existsSync(full) || !fs.statSync(full).isFile()) {
      res.writeHead(404); res.end(); return;
    }
    const ext = path.extname(full);
    res.setHeader("Content-Type", ext === ".mjs" || ext === ".js" ? "text/javascript" :
      ext === ".css" ? "text/css" : "text/html");
    fs.createReadStream(full).pipe(res);
  });
  return new Promise(resolve => server.listen(0, "127.0.0.1", () => resolve(server)));
}
async function run(engine, name, url) {
  const env = process.env["SYNTYR_TEST_" + name.toUpperCase() + "_EXECUTABLE"];
  const browser = await engine.launch({ headless: true, ...(env ? { executablePath: env } : {}) });
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 800 } });
    const errors = [];
    page.on("pageerror", e => errors.push(e.message));
    await page.goto(url + "/examples/dropdowns.html");
    const outcome = await page.evaluate(async () => {
      const { enhanceMenu } = await import("/integrations/dropdown/menu.mjs");
      // aria-current=false or empty must not activate current-item styling.
      const currentPanel = document.createElement("div");
      currentPanel.className = "syn-popover syn-dropdown";
      const ordinary = document.createElement("a");
      ordinary.className = "syn-dropdown__item";
      ordinary.setAttribute("aria-current", "false");
      const empty = document.createElement("a");
      empty.className = "syn-dropdown__item";
      empty.setAttribute("aria-current", "");
      const current = document.createElement("a");
      current.className = "syn-dropdown__item";
      current.setAttribute("aria-current", "page");
      currentPanel.append(ordinary, empty, current);
      document.querySelector("main").append(currentPanel);
      const background = element => getComputedStyle(element).backgroundColor;
      const selectionCorrect = background(ordinary) === background(empty) &&
        background(current) !== background(ordinary);
      currentPanel.remove();
      const manual = document.createElement("div");
      manual.setAttribute("popover", "manual");
      manual.dataset.synMenu = "";
      document.body.append(manual);
      let manualRejected = false;
      try { enhanceMenu(manual); } catch (e) { manualRejected = e instanceof TypeError; }
      const manualRole = manual.getAttribute("role");
      manual.remove();
      const trigger = document.createElement("button");
      trigger.textContent = "Inline menu";
      trigger.setAttribute("popovertarget", "enhanced-panel");
      const menu = document.createElement("div");
      menu.id = "enhanced-panel";
      menu.setAttribute("popover", "");
      menu.setAttribute("data-syn-menu", "");
      menu.innerHTML = '<button data-syn-menu-item>Rename</button>' +
        '<div inert><button data-syn-menu-item>Duplicate</button></div>' +
        '<button data-syn-menu-item>Delete</button>' +
        '<a data-syn-menu-item aria-disabled="true" href="#should-not-navigate">Unavailable</a>';
      document.querySelector("main").append(trigger, menu);
      const dispose = enhanceMenu(menu);
      let disabledActions = 0;
      const disabled = menu.querySelector("[aria-disabled]");
      disabled.addEventListener("click", () => disabledActions++);
      disabled.click();
      const suppressed = !window.location.hash && disabledActions === 0;
      window.__menu = menu;
      window.__disposeMenu = dispose;
      const host = document.createElement("section");
      host.id = "shadow-menu-host";
      document.body.append(host);
      const shadow = host.attachShadow({ mode: "open" });
      shadow.innerHTML = '<button popovertarget="shadow-panel" id="shadow-trigger">Shadow actions</button>' +
        '<div popover data-syn-menu id="shadow-panel">' +
        '<button data-syn-menu-item>First</button><button data-syn-menu-item>Second</button></div>';
      const shadowMenu = shadow.getElementById("shadow-panel");
      const disposeShadow = enhanceMenu(shadowMenu);
      window.__shadow = shadow;
      window.__shadowMenu = shadowMenu;
      window.__disposeShadow = disposeShadow;
      const alreadyOpen = document.createElement("div");
      alreadyOpen.id = "already-open";
      alreadyOpen.setAttribute("popover", "auto");
      alreadyOpen.setAttribute("data-syn-menu", "");
      alreadyOpen.innerHTML = '<button data-syn-menu-item>Open menu action</button>';
      document.querySelector("main").append(alreadyOpen);
      alreadyOpen.showPopover();
      const disposeAlreadyOpen = enhanceMenu(alreadyOpen);
      const opensWithFocus = document.activeElement === alreadyOpen.querySelector("button");
      disposeAlreadyOpen();
      alreadyOpen.hidePopover();
      alreadyOpen.remove();
      return { manualRejected, manualRole, suppressed, selectionCorrect, opensWithFocus };
    });
    assert.equal(outcome.manualRejected, true);
    assert.equal(outcome.manualRole, null);
    assert.equal(outcome.suppressed, true);
    assert.equal(outcome.selectionCorrect, true);
    assert.equal(outcome.opensWithFocus, true, "enhancing an already-open popover focuses first item");

    await page.evaluate(() => window.__shadowMenu.showPopover());
    await page.waitForFunction(() =>
      document.querySelector("#shadow-menu-host").shadowRoot.activeElement?.textContent === "First");
    await page.keyboard.press("ArrowDown");
    assert.equal(await page.evaluate(() => window.__shadow.activeElement.textContent), "Second");
    await page.keyboard.press("Escape");
    assert.equal(await page.evaluate(() => window.__shadowMenu.matches(":popover-open")), false);
    await page.evaluate(() => window.__disposeShadow());

    await page.evaluate(() => window.__menu.showPopover());
    await page.waitForFunction(() => document.activeElement?.textContent === "Rename");
    await page.keyboard.press("ArrowDown");
    assert.equal(await page.evaluate(() => document.activeElement?.textContent), "Delete",
      "inert descendants must be skipped by arrow navigation");
    await page.evaluate(() => window.__disposeMenu());
    assert.equal(await page.evaluate(() => window.__menu.getAttribute("role")), null);

    assert.deepEqual(errors, []);
    await page.close();
    console.log(name + ": optional menu adapter passed");
  } finally {
    await browser.close();
  }
}
(async () => {
  const server = await serve();
  try {
    const url = "http://127.0.0.1:" + server.address().port;
    const requested = (process.env.SYNTYR_TEST_ENGINES || "chromium,firefox,webkit").split(",");
    for (const [name, engine] of [["chromium", chromium], ["firefox", firefox], ["webkit", webkit]]) {
      if (requested.includes(name)) await run(engine, name, url);
    }
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
