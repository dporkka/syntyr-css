// CI-only scriptless starter parity, using the existing locked Playwright
// driver. Python remains the sole builder; no Node package enters the export.
import { strict as assert } from "node:assert";
import { execFileSync } from "node:child_process";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { chromium } from "playwright";

const ROOT = resolve(import.meta.dirname, "../..");
const routes = JSON.parse(execFileSync("python3", ["-c",
  "import json; from scripts.export_site_starter import STARTER_ROUTES; print(json.dumps(STARTER_ROUTES))"
], { cwd: ROOT, encoding: "utf8" }));
const work = await mkdtemp(join(tmpdir(), "syntyr-starters-ci-"));
const files = new Map([
  ["/dist/syntyr.core.css", join(ROOT, "dist/syntyr.core.css")],
  ["/examples/site-starters/shared/site.css", join(ROOT, "examples/site-starters/shared/site.css")],
]);
let browser, server;
try {
  for (const [name, pages] of Object.entries(routes)) {
    const dest = join(work, name);
    execFileSync("python3", ["scripts/export_site_starter.py", "--starter", name, "--output", dest], { cwd: ROOT });
    for (const page of pages) {
      files.set(`/examples/site-starters/${name}/${page}`, join(ROOT, "examples/site-starters", name, page));
      files.set(`/nested/${name}/${page}`, join(dest, page));
    }
    if (name === "saas-marketing") {
      files.set(`/examples/site-starters/${name}/assets/site.css`, join(ROOT, "examples/site-starters", name, "assets/site.css"));
    }
    for (const asset of ["assets/site.css", "assets/syntyr.core.css"]) {
      files.set(`/nested/${name}/${asset}`, join(dest, asset));
    }
  }

  // Serve just the reviewed HTML and CSS, rather than the repository wholesale.
  server = createServer(async (req, res) => {
    try {
      const path = new URL(req.url, "http://localhost").pathname;
      const file = files.get(path);
      if (!file) { res.writeHead(404); res.end(); return; }
      const data = await readFile(file);
      res.writeHead(200, { "Content-Type": path.endsWith(".css") ? "text/css; charset=utf-8" : "text/html; charset=utf-8" });
      res.end(data);
    } catch {
      res.writeHead(500); res.end();
    }
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const origin = `http://127.0.0.1:${server.address().port}`;
  const executablePath = process.env.SYNTYR_CHROMIUM_EXECUTABLE;
  browser = await chromium.launch(executablePath ? { executablePath, args: ["--no-sandbox"] } : {});

  async function capture(path, width, interactions) {
    const context = await browser.newContext({ viewport: { width, height: 900 },
      deviceScaleFactor: 1, javaScriptEnabled: false, reducedMotion: "reduce" });
    const failures = [];
    try {
      await context.route("**/*", route => {
        if (new URL(route.request().url()).origin !== origin) {
          failures.push("External request: " + route.request().url());
          return route.abort();
        }
        return route.continue();
      });
      const page = await context.newPage();
      page.on("requestfailed", req => failures.push("Failed: " + req.url()));
      page.on("response", res => {
        if (res.status() >= 400 && !res.url().endsWith("/favicon.ico")) failures.push(`HTTP ${res.status()}: ${res.url()}`);
      });
      await page.goto(origin + path, { waitUntil: "load" });
      await page.evaluate("document.fonts.ready");
      for (const selector of ["main", "h1", ".syn-root"]) {
        assert.equal(await page.locator(selector).count(), 1, path + ": " + selector);
      }
      assert(await page.evaluate("document.styleSheets.length > 0 && Array.from(document.styleSheets).every(s => s.cssRules.length > 0)"), path + ": local CSS");
      assert(await page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), `${path}: overflow at ${width}px`);
      const image = await page.screenshot({ fullPage: true, animations: "disabled" });
      if (interactions) {
        await page.keyboard.press("Tab");
        assert.match(await page.locator(":focus").innerText(), /skip/i);
        await page.keyboard.press("Enter");
        await page.waitForURL(url => url.hash === "#main", { timeout: 5000 });
        const details = page.locator("details").first();
        if (await details.count()) {
          assert.equal(await details.evaluate(el => el.open), false);
          await details.locator("summary").click();
          assert.equal(await details.evaluate(el => el.open), true);
        }
        const nav = page.locator('nav[aria-label="Primary"] a:not([aria-current])').first();
        if (await nav.count()) {
          await nav.click();
          await page.waitForLoadState("load");
          assert.equal(await page.locator("main").count(), 1);
        }
      }
      assert.deepEqual(failures, []);
      return image;
    } finally {
      await context.close();
    }
  }

  let comparisons = 0;
  for (const [name, pages] of Object.entries(routes)) {
    for (const page of pages) {
      for (const width of [320, 390, 1280]) {
        const source = await capture(`/examples/site-starters/${name}/${page}`, width, false);
        const exported = await capture(`/nested/${name}/${page}`, width, true);
        // Both screenshots are captured in the same browser run, with the same
        // viewport and no dynamic content. Exact PNG bytes avoid a golden image
        // inventory and an additional image-comparison dependency.
        assert(source.equals(exported), `${name}/${page} at ${width}px: visual export drift`);
        comparisons++;
      }
    }
    console.log(`PASS ${name}: ${pages.length * 3} exact browser comparisons`);
  }
  console.log(`PASS ${comparisons} comparisons (Chromium, JS disabled, local requests only)`);
} finally {
  await browser?.close();
  if (server) await new Promise(resolve => server.close(resolve));
  await rm(work, { recursive: true, force: true });
}
