import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  registerSectionManifest, sectionBlockTypes, projectNeedsSectionManifest,
  getBlockDefinition, createBlock, createDefaultDocument, parseDocument,
  renderSections, exportHtml, moveBlock, insertBlockAfter, duplicateBlock,
  requiredAssets
} from "../docs/page-builder-model.mjs";

const manifest = JSON.parse(readFileSync(
  new URL("../metadata/section-composer.v1.json", import.meta.url), "utf8"));

test("all canonical website sections are searchable and editable as static page blocks", () => {
  const count = registerSectionManifest(manifest);
  assert.equal(count, manifest.sections.length);
  assert.ok(count >= 85);
  assert.ok(sectionBlockTypes().includes("section:image-gallery"));
  assert.ok(sectionBlockTypes().includes("section:before-after"));
  assert.equal(getBlockDefinition("section:image-gallery").category, "Portfolio");
  for (const section of manifest.sections) {
    const block = createBlock("section:" + section.id);
    assert.ok(Object.keys(block.props).length > 0, section.id);
    assert.deepEqual(parseDocument({
      ...createDefaultDocument(), blocks: [block]
    }).blocks[0], block);
  }
});

test("new sections are safe to rearrange and duplicate without changing the original", () => {
  registerSectionManifest(manifest);
  const original = createDefaultDocument();
  const gallery = createBlock("section:image-gallery", "gallery-a");
  const updated = insertBlockAfter(original, original.blocks[0].id, gallery);
  assert.deepEqual(updated.blocks.map(b => b.id), ["hero-1", "gallery-a", "features-1", "cta-1"]);
  assert.equal(original.blocks.length, 3);
  assert.equal(moveBlock(updated, 1, 3).blocks.at(-1).id, "gallery-a");
  const duplicated = duplicateBlock(updated, 1, "gallery-b");
  assert.deepEqual(duplicated.blocks.map(b => b.id), ["hero-1", "gallery-a", "gallery-b", "features-1", "cta-1"]);
  assert.deepEqual(duplicated.blocks[2].props, duplicated.blocks[1].props);
  duplicated.blocks[2].props.text1 = "Different";
  assert.notEqual(duplicated.blocks[1].props.text1, "Different");
  assert.throws(() => duplicateBlock(updated, 1, "gallery-a"), /duplicate/i);
  assert.throws(() => insertBlockAfter(updated, "missing-id", gallery), /unknown/i);
  assert.throws(() => insertBlockAfter(updated, "gallery-a", gallery), /duplicate/i);
});

test("image gallery export uses local asset paths and no browser script", () => {
  registerSectionManifest(manifest);
  const page = createDefaultDocument();
  page.blocks = [
    createBlock("section:image-gallery", "gallery-1"),
    createBlock("section:before-after", "compare-1")
  ];
  const html = exportHtml(page);
  assert.doesNotMatch(html, /<script\b|href="\.\.\/assets\/|src="\.\.\/assets\//i);
  assert.match(html, /href="assets\/gallery-horizon\.svg"/);
  assert.match(html, /src="assets\/gallery-botanical\.svg"/);
  assert.match(html, /href="syntyr\.all\.css"/);
  assert.deepEqual(requiredAssets(page), [
    "gallery-architecture.svg", "gallery-botanical.svg",
    "gallery-horizon.svg", "gallery-signal.svg"
  ]);
  assert.match(exportHtml(page, {previewAssets: true}), /src="\.\.\/assets\/gallery-horizon\.svg"/);
});

test("repeating native section snippets scopes internal IDs and preserves edited accessible links", () => {
  registerSectionManifest(manifest);
  const page = createDefaultDocument();
  page.blocks = [
    createBlock("section:image-story", "story-one"),
    createBlock("section:image-story", "story-two"),
    createBlock("section:faq", "faq-one"),
    createBlock("section:faq", "faq-two"),
  ];
  const html = renderSections(page);
  const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map(m => m[1]);
  assert.equal(ids.length, new Set(ids).size);
  assert.match(html, /story-one--syn-image-story-heading/);
  assert.match(html, /story-two--syn-image-story-heading/);
  assert.match(html, /faq-two--syn-faq-heading/);
});

test("section project import requires a known, trusted current manifest", () => {
  registerSectionManifest(manifest);
  const page = createDefaultDocument();
  assert.equal(projectNeedsSectionManifest(page), false);
  page.blocks = [createBlock("section:image-gallery", "img-1")];
  assert.equal(projectNeedsSectionManifest(page), true);
  assert.throws(() => parseDocument({...page, blocks: [{
    ...page.blocks[0], html: "<script>alert(1)</script>"
  }]}), /unknown block property/i);
  const changed = structuredClone(manifest);
  changed.sections[0].html += '<img src="x" onerror="alert(1)">';
  assert.throws(() => registerSectionManifest(changed), /unsafe/i);
  assert.deepEqual(parseDocument(page), page);
});

test("canonical sections can all be rendered into script-free export", () => {
  registerSectionManifest(manifest);
  const page = createDefaultDocument();
  page.blocks = manifest.sections.slice(0, 50).map((s, i) =>
    createBlock("section:" + s.id, "section-" + i));
  const html = exportHtml(page);
  assert.doesNotMatch(html, /<script\b| onload=| onerror=|<iframe/i);
  const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map(match => match[1]);
  assert.equal(ids.length, new Set(ids).size);
});
