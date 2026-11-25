import assert from "node:assert/strict";
import { test } from "node:test";
import { app } from "../server.mjs";

test("serves local Syntyr CSS and escaped, functional SSR markup", async (t) => {
  const server = app.listen(0, "127.0.0.1");
  t.after(() => new Promise((resolve, reject) => {
    server.close((error) => error ? reject(error) : resolve());
  }));
  await new Promise((resolve) => server.once("listening", resolve));
  const base = "http://127.0.0.1:" + server.address().port;

  const css = await fetch(base + "/css/syntyr.core.css");
  assert.equal(css.status, 200);
  assert.match(css.headers.get("content-type"), /text\/css/);
  assert.match(await css.text(), /syn-root/);

  const page = await fetch(base + "/search?q=Metro");
  assert.equal(page.status, 200);
  const html = await page.text();
  assert.match(html, /Metro Displays/);
  assert.doesNotMatch(html, /Northside Media/);
  assert.match(html, /class="syn-root"/);
  assert.match(html, /method="get"/);

  const injection = await fetch(base + "/search?q=" + encodeURIComponent('<script>alert(1)</script>'));
  const escaped = await injection.text();
  assert.ok(escaped.includes("&lt;script&gt;"), "EJS must escape untrusted values");
  assert.ok(!escaped.includes('<script>alert(1)</script>'), "untrusted HTML must not execute");
});
