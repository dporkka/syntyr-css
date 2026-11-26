// Actual build-output parity, using the already locked maintainer-only
// Playwright driver. No JS is shipped or enabled in the pages being tested.
import { strict as assert } from "node:assert";
import { lstat, readFile, readdir, realpath } from "node:fs/promises";
import { createServer } from "node:http";
import { join, resolve, sep } from "node:path";
import { chromium, firefox, webkit } from "playwright";

const engines = { chromium, firefox, webkit };
const mounts = [
  ["Python", "reference", "/"],
  ["Hugo", "syntyr-hugo", "/syntyr-hugo/"],
  ["Eleventy", "syntyr-eleventy", "/syntyr-eleventy/"],
  ["Astro", "syntyr-astro-keystatic", "/syntyr-astro-keystatic/"],
];
const [input, ...names] = process.argv.slice(2);
if (!input || names.some(name => !Object.hasOwn(engines, name))) {
  throw new Error("Usage: node examples/lit/generator-parity-browser.mjs FIXTURE_DIR [chromium firefox webkit]");
}
const browsers = names.length ? names : Object.keys(engines);
assert.equal(new Set(browsers).size, browsers.length, "duplicate browser");
const root = await realpath(resolve(input));
const files = new Map();

async function addTree(directory, prefix) {
  const st = await lstat(directory);
  assert(st.isDirectory() && !st.isSymbolicLink(), "invalid fixture directory");
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    assert(!entry.isSymbolicLink() && (await realpath(path)).startsWith(root + sep), "unexpected symlink or escaping fixture");
    if (entry.isDirectory()) await addTree(path, prefix + entry.name + "/");
    else if (entry.isFile() && /\.(css|html)$/.test(entry.name)) {
      const requestPath = prefix + entry.name;
      assert(!files.has(requestPath), "duplicate fixture path: " + requestPath);
      files.set(requestPath, path);
    } else {
      assert(entry.isFile() && !/\.(mjs|cjs|js)$/i.test(entry.name), "unexpected executable fixture: " + path);
    }
  }
}

for (const [, directory, base] of mounts) {
  await addTree(join(root, directory), base);
  assert(files.has(base + "index.html"), "missing rendered fixture " + directory);
  // Native directory links and fragment links must resolve under real mount paths.
  files.set(base, files.get(base + "index.html"));
}
const server = createServer(async (req, res) => {
  try {
    const path = new URL(req.url, "http://localhost").pathname;
    const file = files.get(path);
    if (!file) { res.writeHead(404); res.end(); return; }
    const data = await readFile(file);
    res.writeHead(200, {
      "Content-Type": file.endsWith(".css") ? "text/css; charset=utf-8" : "text/html; charset=utf-8",
      "X-Content-Type-Options": "nosniff",
    });
    res.end(data);
  } catch {
    res.writeHead(500); res.end();
  }
});
await new Promise((ok, fail) => { server.once("error", fail); server.listen(0, "127.0.0.1", ok); });
const origin = `http://127.0.0.1:${server.address().port}`;

async function capture(browser, base, width) {
  const context = await browser.newContext({
    viewport: { width, height: 900 }, deviceScaleFactor: 1,
    javaScriptEnabled: false, reducedMotion: "reduce",
  });
  context.setDefaultTimeout(15_000);
  context.setDefaultNavigationTimeout(15_000);
  const failures = [];
  try {
    await context.route("**/*", route => {
      const url = new URL(route.request().url());
      if (url.origin !== origin || !url.pathname.startsWith(base)) {
        failures.push("Non-local or wrong-mount request: " + url.href);
        return route.abort();
      }
      return route.continue();
    });
    const page = await context.newPage();
    page.on("pageerror", error => failures.push(String(error)));
    page.on("requestfailed", req => failures.push("Request failed: " + req.url()));
    page.on("response", res => {
      if (res.status() >= 400 && !res.url().endsWith("/favicon.ico")) failures.push("HTTP " + res.status() + ": " + res.url());
    });
    await page.goto(origin + base + "index.html", { waitUntil: "load" });
    // The fixture has no downloadable fonts and has reached load. Avoid
    // awaiting document.fonts.ready in script-disabled Firefox (it can hang).
    for (const selector of ["main", "h1", ".syn-root"]) {
      assert.equal(await page.locator(selector).count(), 1, base + " expected one " + selector);
    }
    assert.equal(await page.locator("script").count(), 0, base + " script found");
    assert.equal(await page.evaluate("document.styleSheets.length > 0 && Array.from(document.styleSheets).every(s => s.cssRules.length > 0)"), true,
      base + " missing local stylesheets");
    assert.equal(await page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), true, base + " overflow");
    const image = await page.screenshot({ fullPage: true, animations: "disabled", timeout: 15_000 });

    await page.keyboard.press("Tab");
    assert.match(await page.locator(":focus").innerText(), /skip/i);
    await page.keyboard.press("Enter");
    await page.waitForURL(url => url.hash === "#content", { timeout: 5000 });
    const feature = page.getByRole("link", { name: "Explore features" });
    await feature.click();
    await page.waitForURL(url => url.pathname === base && url.hash === "#section-features", { timeout: 5000 });
    const details = page.locator("details").first();
    assert.equal(await details.evaluate(el => el.open), false);
    await details.locator("summary").click();
    assert.equal(await details.evaluate(el => el.open), true);
    assert.deepEqual(failures, [], base + " failed network requests");
    return image;
  } finally {
    await context.close();
  }
}

let total = 0;
try {
  for (const name of browsers) {
    const executablePath = process.env["SYNTYR_" + name.toUpperCase() + "_EXECUTABLE"];
    const browser = await engines[name].launch(executablePath ? { executablePath } : {});
    try {
      console.log(`Checking ${name} ${browser.version()} with independent CMS builds`);
      for (const width of [320, 390, 1280]) {
        const reference = await capture(browser, "/", width);
        for (const [generator, , base] of mounts.slice(1)) {
          const screenshot = await capture(browser, base, width);
          assert(reference.equals(screenshot), `${name} ${generator} ${width}px: screenshot differs from Python`);
          total++;
        }
        console.log(`PASS ${name} ${width}px: 3 generator comparisons`);
      }
      console.log(`PASS ${name}: 9 actual-generator browser comparisons`);
    } finally {
      await browser.close();
    }
  }
  console.log(`PASS ${total} comparisons; zero browser JS, local-only CSS and native navigation`);
} finally {
  await new Promise(ok => server.close(ok));
}
