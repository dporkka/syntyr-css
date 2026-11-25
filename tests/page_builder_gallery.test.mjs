import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  registerGalleryManifest, galleryBlockTypes, getBlockDefinition,
  createBlock, createDefaultDocument, parseDocument, exportHtml, renderSections,
  projectNeedsGalleryManifest
} from "../docs/page-builder-model.mjs";

const manifest = JSON.parse(readFileSync(new URL("../metadata/component-gallery.v1.json", import.meta.url), "utf8"));

test("registers existing generated gallery examples as optional composer blocks", () => {
  const count = registerGalleryManifest(manifest);
  assert.equal(count, manifest.examples.length);
  assert.equal(galleryBlockTypes().length, manifest.examples.length);
  const type = "gallery:catalog-buttons-title";
  assert.equal(galleryBlockTypes().includes(type), true);
  assert.equal(getBlockDefinition(type).label, "Buttons");
  assert.equal(getBlockDefinition(type).requiredStylesheets[0], "syntyr.core.css");
  assert.deepEqual(
    getBlockDefinition("gallery:catalog-geometry-frame-title").requiredStylesheets.slice(0, 2),
    ["syntyr.core.css", "syntyr.geometry.css"]
  );
  assert.ok(Object.keys(createBlock(type, "buttons-1").props).length > 0);
  assert.equal(createBlock(type).id, "catalog-buttons-title-1");
});

test("edits gallery text safely and exports framework-neutral HTML/CSS references", () => {
  registerGalleryManifest(manifest);
  const page = createDefaultDocument();
  const block = createBlock("gallery:catalog-buttons-title", "buttons-1");
  const first = Object.keys(block.props)[0];
  block.props[first] = '<img src=x onerror="alert(1)">';
  page.blocks.push(block);
  const restored = parseDocument(JSON.stringify(page));
  assert.deepEqual(restored, page);
  const html = exportHtml(restored);
  assert.match(html, /&lt;img src=x onerror=&quot;alert\(1\)&quot;&gt;/);
  assert.doesNotMatch(html, /<img src=x|<script|href="javascript:/);
  assert.match(html, /href="syntyr\.all\.css"/);
  assert.match(html, /data-syntyr-block-id="buttons-1"/);
  assert.match(html, /syn-button--primary/);
});

test("repeated gallery blocks scope IDs and accessible references per instance", () => {
  registerGalleryManifest(manifest);
  const page = createDefaultDocument();
  page.blocks = [
    createBlock("gallery:catalog-interaction-card-2", "confirmation-a"),
    createBlock("gallery:catalog-interaction-card-2", "confirmation-b"),
    createBlock("gallery:catalog-forms-title", "fields-a"),
    createBlock("gallery:catalog-forms-title", "fields-b")
  ];
  const html = renderSections(page);
  const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map(match => match[1]);
  assert.equal(ids.length, new Set(ids).size);
  assert.match(html, /commandfor="confirmation-a--catalog-interaction-dialog"/);
  assert.match(html, /aria-labelledby="confirmation-b--catalog-interaction-dialog-title"/);
  assert.match(html, /for="fields-a--catalog-email"/);
  assert.match(html, /id="fields-b--catalog-email"/);
});

test("project import rejects raw markup, unknown gallery IDs and unexpected properties", () => {
  registerGalleryManifest(manifest);
  const page = createDefaultDocument();
  const type = "gallery:catalog-buttons-title";
  const b = createBlock(type, "buttons-1");
  page.blocks = [b];
  page.blocks[0].html = "<script>alert(1)</script>";
  assert.throws(() => parseDocument(page), /property|block/i);
  delete page.blocks[0].html;
  b.props.html = "<img src=x>";
  assert.throws(() => parseDocument(page), /property/i);
  delete b.props.html;
  b.type = "gallery:arbitrary-template";
  assert.throws(() => parseDocument(page), /Unknown block/);
});

test("rejects untrusted or incompatible manifest markup before registration", () => {
  const evil = structuredClone(manifest);
  evil.examples[0].html += '<img src=x onerror="alert(1)">';
  assert.throws(() => registerGalleryManifest(evil), /unsafe|event|markup|script/i);
  const wrong = structuredClone(manifest);
  wrong.schema_version = 999;
  assert.throws(() => registerGalleryManifest(wrong), /manifest|schema/i);
  registerGalleryManifest(manifest);
});

test("every curated gallery example survives import and renders without inline scripts", () => {
  registerGalleryManifest(manifest);
  const page = createDefaultDocument();
  page.blocks = manifest.examples.map((example, index) =>
    createBlock("gallery:" + example.id, "catalog-" + (index + 1)));
  const restored = parseDocument(JSON.stringify(page));
  assert.equal(restored.blocks.length, manifest.examples.length);
  const html = exportHtml(restored);
  assert.ok(html.includes('href="syntyr.all.css"'));
  assert.doesNotMatch(html, /<script|<iframe| onload=| onerror=/);
  const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map(match => match[1]);
  assert.equal(ids.length, new Set(ids).size);
});

test("an edited gallery HTTPS link is allowed but unsupported schemes are neutralized", () => {
  registerGalleryManifest(manifest);
  const block = createBlock("gallery:catalog-breadcrumbs-title", "crumbs");
  const hrefField = Object.keys(block.props).find(name => name.startsWith("href"));
  assert.ok(hrefField);
  block.props[hrefField] = "https://example.org/doc?x=1&y=2";
  const page = createDefaultDocument();
  page.blocks = [block];
  assert.ok(renderSections(page).includes('href="https://example.org/doc?x=1&amp;y=2"'));
  block.props[hrefField] = "javascript:alert(1)";
  assert.doesNotMatch(renderSections(page), /href="javascript:/);
  assert.match(renderSections(page), /href="#"/);
});

test("native popover triggers reference the scoped popover ID for each block", () => {
  registerGalleryManifest(manifest);
  const page = createDefaultDocument();
  page.blocks = [
    createBlock("gallery:catalog-native-popover-title", "help-one"),
    createBlock("gallery:catalog-native-popover-title", "help-two")
  ];
  const html = renderSections(page);
  for (const id of ["help-one", "help-two"]) {
    assert.match(html, new RegExp('id="' + id + '--catalog-help-popover"'));
    assert.equal((html.match(new RegExp('popovertarget="' + id + '--catalog-help-popover"', 'g')) || []).length, 2);
  }
});


test("native-only projects do not depend on an optional gallery fetch", () => {
  const native = createDefaultDocument();
  assert.equal(projectNeedsGalleryManifest(native), false);
  const mixed = structuredClone(native);
  mixed.blocks.push({ id: "g1", type: "gallery:catalog-buttons-title", props: {} });
  assert.equal(projectNeedsGalleryManifest(mixed), true);
  assert.equal(projectNeedsGalleryManifest({ blocks: [{ type: "hero" }] }), false);
  assert.equal(projectNeedsGalleryManifest({ blocks: "invalid" }), false);
});


test("recovery example keeps its functioning destination on export", () => {
  registerGalleryManifest(manifest);
  const page = createDefaultDocument();
  page.blocks = [createBlock("gallery:catalog-recovery-state-title", "recover-1")];
  const html = exportHtml(page);
  assert.match(html, /href="https:\/\/syntyr-css\.pages\.dev\/docs\/guides\.html"/);
});
