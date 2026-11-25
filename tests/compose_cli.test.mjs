import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { compose, listSections } from "../scripts/compose.mjs";

const release = "0.3.0-alpha.5";
const input = {release, title: "Demo", theme: "studio",
  sections: [{section_id: "hero-product"}, {section_id: "faq"}, {section_id: "faq"}]};

test("deterministic HTML and editable project use canonical sections and scoped IDs", () => {
  const result = compose(input);
  assert.deepEqual(result, compose(input));
  assert.equal(result.project.schema, "syntyr.page.v1");
  assert.equal(result.project.blocks.length, 3);
  assert.equal(result.release, release);
  assert.deepEqual(result.stylesheets, ["syntyr.all.css"]);
  assert.match(result.html, /<title>Demo<\/title>/);
  assert.doesNotMatch(result.html, /<script\b/i);
  const ids = [...result.html.matchAll(/\sid="([^"]+)"/g)].map(m => m[1]);
  assert.equal(ids.length, new Set(ids).size);
  assert.match(result.html, /section-2--syn-faq-heading/);
  assert.match(result.html, /section-3--syn-faq-heading/);
});

test("fields are editable, escaped, and unsafe links do not survive rendering", () => {
  const result = compose({...input, sections: [{section_id: "hero-product",
    fields: {text1: '<img src=x onerror=alert(1)>', href1: 'javascript:alert(1)'}}]});
  assert.match(result.html, /&lt;img src=x onerror=alert\(1\)&gt;/);
  assert.doesNotMatch(result.html, /<img src=x|href="javascript:/i);
  assert.throws(() => compose({...input, sections: [{section_id:"hero-product",fields:{invented:"x"}}]}), /unknown/i);
});

test("catalog exposes exact editable fields and every canonical section renders", () => {
  const listing = listSections(release);
  const manifest = JSON.parse(readFileSync(new URL("../metadata/section-composer.v1.json", import.meta.url)));
  assert.equal(listing.sections.length, manifest.sections.length);
  for (const entry of listing.sections) {
    assert.ok(Object.keys(entry.fields).length);
    assert.doesNotMatch(compose({...input, sections:[{section_id:entry.id}]}).html, /<script\b/i);
  }
  const result = compose({...input, sections:[{section_id:"image-gallery"}]});
  assert.ok(result.assets.includes("gallery-horizon.svg"));
});

test("reject arbitrary markup, invalid release, oversized plan and unsupported interactions", () => {
  for (const value of [
    {...input, release:"0.3.0-alpha.4"},
    {...input, sections:[]},
    {...input, sections:Array.from({length:51},()=>({section_id:"faq"}))},
    {...input, sections:[{section_id:"../../secret"}]},
    {...input, sections:[{section_id:"faq",html:"<script>"}]},
    {...input, interactions:[{contract:"combobox"}]},
    {...input, theme:"invented"},
  ]) assert.throws(()=>compose(value));
});

test("CLI returns JSON, supports list, and rejects invalid input without output", () => {
  const path = new URL("../scripts/compose.mjs", import.meta.url);
  const run = (args, data) => spawnSync(process.execPath,[fileURLToPath(path),...args],{input:data, encoding:"utf8"});
  const output = run([], JSON.stringify(input));
  assert.equal(output.status,0,output.stderr);
  assert.deepEqual(JSON.parse(output.stdout),compose(input));
  const listing = run(["--list",release],"");
  assert.equal(listing.status,0,listing.stderr);
  assert.deepEqual(JSON.parse(listing.stdout),listSections(release));
  const bad = run([], '{"title":');
  assert.notEqual(bad.status,0);
  assert.equal(bad.stdout,"");
});

test("canonical sections preserve selected non-Studio theme", () => {
  for (const theme of ["noir", "auto", "corporate"]) {
    const result = compose({...input, theme, sections:[{section_id:"hero-product"}]});
    assert.match(result.html, new RegExp('<section class="syn-root syn-region" data-syn-theme="' + theme + '"'));
  }
  const studio = compose({...input, sections:[{section_id:"hero-product"}]});
  assert.match(studio.html, /<section class="syn-root syn-region" aria-labelledby=/);
});

test("asset manifest includes padded and unpadded download links", () => {
  // Use a link-only asset so that other image fields cannot mask the regression.
  for (const href1 of ["../assets/gallery-horizon.svg", " ../assets/gallery-horizon.svg "]) {
    const result = compose({...input,sections:[{section_id:"resource-downloads",
      fields:{href1,href2:"/other",href3:"/other"}}]});
    assert.match(result.html,/href="assets\/gallery-horizon\.svg"/);
    assert.ok(result.assets.includes("gallery-horizon.svg"));
  }
});
