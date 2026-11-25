import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const source = readFileSync(new URL("../docs/playground-snippet.js", import.meta.url), "utf8");
const context = { window: {} };
vm.runInNewContext(source, context);
const api = context.window.SYNTYR_PLAYGROUND_SNIPPET;

test("exports only the required Syntyr stylesheets, core first", () => {
  assert.deepEqual(Array.from(api.requiredStylesheets("syntyr.recipes.css")), [
    "syntyr.core.css", "syntyr.recipes.css"
  ]);
  assert.deepEqual(Array.from(api.requiredStylesheets("syntyr.core.css + syntyr.recipes.css")), [
    "syntyr.core.css", "syntyr.recipes.css"
  ]);
  assert.deepEqual(Array.from(api.requiredStylesheets("syntyr.viz.css")), [
    "syntyr.core.css", "syntyr.viz.css"
  ]);
  assert.deepEqual(Array.from(api.requiredStylesheets("syntyr.core.css")), ["syntyr.core.css"]);
});

test("all generated catalog entries produce stylesheets present in the public CSS distribution", () => {
  const catalogCode = readFileSync(new URL("../docs/playground-catalog.js", import.meta.url), "utf8");
  vm.runInNewContext(catalogCode, context);
  const modules = context.window.SYNTYR_PLAYGROUND_CATALOG;
  assert.ok(modules.length > 20);
  for (const item of modules) {
    for (const file of api.requiredStylesheets(item.module)) {
      const css = new URL(`../dist/${file}`, import.meta.url);
      assert.ok(readFileSync(css).length > 0, `${item.id}: ${file}`);
    }
  }
});

test("preview and copy use identical module selections", () => {
  const modules = "syntyr.core.css + syntyr.recipes.css";
  const previewLinks = api.previewStylesheets(modules);
  const snippet = api.configuredSnippet({
    theme: "studio", tokens: "", module: modules, markup: "<p>Preview</p>"
  });
  for (const name of api.requiredStylesheets(modules)) {
    assert.ok(previewLinks.includes(`href="../dist/${name}"`));
    assert.ok(snippet.includes(`href="./${name}"`));
  }
  assert.equal(previewLinks.match(/<link /g).length, 2);
});

test("invalid or invented stylesheet names are never emitted in copied HTML", () => {
  assert.throws(() => api.requiredStylesheets("https://evil.example/foo.css"));
  assert.throws(() => api.requiredStylesheets("syntyr.fake.css"));
  assert.throws(() => api.requiredStylesheets("syntyr.core.css + <script>"));
});

test("copy snippet includes self-hosted links, scoped tokens and complete selected HTML", () => {
  const result = api.configuredSnippet({
    theme: "studio",
    tokens: "--syn-panel-radius: 12px; --syn-panel-padding: 24px;",
    module: "syntyr.core.css + syntyr.recipes.css",
    markup: '<article class="syn-panel syn-kpi-grid">Hello</article>',
  });
  assert.match(result, /<link rel="stylesheet" href="\.\/syntyr\.core\.css">/);
  assert.match(result, /<link rel="stylesheet" href="\.\/syntyr\.recipes\.css">/);
  assert.match(result, /data-syn-theme="studio"/);
  assert.match(result, /--syn-panel-radius: 12px/);
  assert.match(result, /syn-kpi-grid/);
  assert.equal(result.split('href="./syntyr.core.css"').length - 1, 1);
});

test("theme names and override tokens are validated before attribute injection", () => {
  assert.throws(() => api.configuredSnippet({
    theme: 'studio" onfocus="bad', tokens: "", module: "syntyr.core.css", markup: ""
  }));
  assert.throws(() => api.configuredSnippet({
    theme: "studio", tokens: '"><script>', module: "syntyr.core.css", markup: ""
  }));
  assert.doesNotThrow(() => api.configuredSnippet({
    theme: "auto", tokens: "", module: "syntyr.core.css", markup: "<p>OK</p>"
  }));
});

test("accepts every nonaggregate shipped Syntyr stylesheet", () => {
  const shipped = readdirSync(new URL("../dist/", import.meta.url)).filter(
    name => name.startsWith("syntyr.") && name.endsWith(".css") &&
      !["syntyr.all.css", "syntyr.css"].includes(name)
  );
  assert.ok(shipped.length >= 17, "The individual modules must be present in dist");
  for (const stylesheet of shipped) {
    const expected = stylesheet === "syntyr.core.css"
      ? ["syntyr.core.css"] : ["syntyr.core.css", stylesheet];
    assert.deepEqual(Array.from(api.requiredStylesheets(stylesheet)), expected);
    assert.ok(readFileSync(new URL(`../dist/${stylesheet}`, import.meta.url)).length > 0);
  }
  assert.throws(() => api.requiredStylesheets("syntyr.all.css"));
  assert.throws(() => api.requiredStylesheets("syntyr.css"));
});
