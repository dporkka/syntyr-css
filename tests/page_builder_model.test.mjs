import test from "node:test";
import assert from "node:assert/strict";
import {
  BLOCK_TYPES,
  SCHEMA_VERSION,
  MAX_PROJECT_BYTES,
  createBlock,
  createDefaultDocument,
  parseDocument,
  moveBlock,
  renderSections,
  exportHtml
} from "../docs/page-builder-model.mjs";

test("creates a versioned portable Syntyr page from known blocks", () => {
  const page = createDefaultDocument();
  assert.equal(page.schema, SCHEMA_VERSION);
  assert.equal(page.theme, "studio");
  assert.deepEqual(page.blocks.map(block => block.type), ["hero", "features", "cta"]);
  assert.equal(BLOCK_TYPES.length >= 6, true);
  assert.ok(page.blocks.every(block => typeof block.id === "string" && block.props));
});

test("round-trips user edits without changing schema", () => {
  const original = createDefaultDocument();
  original.blocks[0].props.title = "An independent website";
  const restored = parseDocument(JSON.stringify(original));
  assert.deepEqual(restored, original);
});

test("rejects unknown blocks, duplicate ids and incompatible schema", () => {
  const page = createDefaultDocument();
  page.blocks.push({ id: "unknown", type: "script", props: { html: "<script>" } });
  assert.throws(() => parseDocument(page), /Unknown block/);
  page.blocks.pop();
  page.blocks[1].id = page.blocks[0].id;
  assert.throws(() => parseDocument(page), /Duplicate/);
  page.blocks[1].id = "unique";
  page.schema = "syntyr.page.v99";
  assert.throws(() => parseDocument(page), /schema/i);
});

test("escapes hostile text and never exposes event handlers or javascript URLs", () => {
  const page = createDefaultDocument();
  page.blocks[0].props.title = '<img src=x onerror="alert(1)">';
  page.blocks[0].props.actionHref = "javascript:alert(1)";
  page.blocks[0].props.actionText = '" onclick="alert(1)';
  const html = renderSections(page);
  assert.match(html, /&lt;img src=x onerror=&quot;alert\(1\)&quot;&gt;/);
  assert.doesNotMatch(html, /<img|href="javascript:| onclick="/);
  assert.match(html, /href="#"/);
});

test("requires string-only declared props and permits safe HTTPS links", () => {
  const page = createDefaultDocument();
  page.blocks[0].props.actionHref = "https://example.com/start?x=1&y=2";
  assert.match(renderSections(page), /href="https:\/\/example.com\/start\?x=1&amp;y=2"/);
  page.blocks[0].props.title = { html: "unsafe" };
  assert.throws(() => parseDocument(page), /string/i);
});

test("moves blocks without mutating the original document", () => {
  const page = createDefaultDocument();
  const result = moveBlock(page, 0, 2);
  assert.deepEqual(result.blocks.map(block => block.type), ["features", "cta", "hero"]);
  assert.deepEqual(page.blocks.map(block => block.type), ["hero", "features", "cta"]);
  assert.throws(() => moveBlock(page, 0, 100), /range/i);
});

test("exports complete framework-neutral HTML with local Syntyr CSS", () => {
  const page = createDefaultDocument();
  const html = exportHtml(page);
  assert.match(html, /^<!doctype html>/i);
  assert.match(html, /href="syntyr.all.css"/);
  assert.match(html, /<main/);
  assert.match(html, /data-syn-theme="studio"/);
  assert.doesNotMatch(html, /<script|react|grapesjs/i);
});

test("truncation and oversized imported documents fail closed", () => {
  const page = createDefaultDocument();
  page.blocks[0].props.title = "x".repeat(5001);
  assert.throws(() => parseDocument(page), /too long/i);
  const copy = createDefaultDocument();
  copy.blocks = Array.from({ length: 51 }, (_, index) => createBlock("cta", "c" + index));
  assert.throws(() => parseDocument(copy), /50/);
});


test("repeated section types generate unique HTML ids", () => {
  const page = createDefaultDocument();
  page.blocks.push(createBlock("hero", "hero-another"));
  page.blocks.push(createBlock("features", "features-another"));
  page.blocks.push(createBlock("cta", "cta-another"));
  const html = renderSections(page);
  const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map(match => match[1]);
  assert.equal(ids.length, new Set(ids).size, "duplicate anchor ids break navigation");
  assert.ok(ids.includes("top"));
  assert.ok(ids.includes("features"));
  assert.ok(ids.includes("contact"));
});

test("rejects array-valued or object-valued block types instead of coercing keys", () => {
  for (const type of [["hero"], { toString: () => "hero" }, null, 12]) {
    const page = createDefaultDocument();
    page.blocks[0].type = type;
    assert.throws(() => parseDocument(page), /Unknown block|block type/i);
    assert.throws(() => parseDocument(JSON.stringify(page)), /Unknown block|block type/i);
  }
});

test("all valid editor projects, including large and multibyte text, can be reopened", () => {
  const page = createDefaultDocument();
  page.blocks = Array.from({ length: 50 }, (_, i) => {
    const block = createBlock("features", "features-" + i);
    for (const key of Object.keys(block.props)) block.props[key] = "á".repeat(5000);
    return block;
  });
  const normalized = parseDocument(page);
  const saved = JSON.stringify(normalized);
  assert.ok(new TextEncoder().encode(saved).length > 500000);
  assert.ok(new TextEncoder().encode(saved).length < MAX_PROJECT_BYTES);
  assert.deepEqual(parseDocument(saved), normalized);
  const longestEscaped = structuredClone(page);
  for (const block of longestEscaped.blocks) {
    for (const key of Object.keys(block.props)) block.props[key] = String.fromCharCode(0).repeat(5000);
  }
  const escapedProject = JSON.stringify(parseDocument(longestEscaped));
  assert.ok(new TextEncoder().encode(escapedProject).length < MAX_PROJECT_BYTES);
  assert.deepEqual(parseDocument(escapedProject), parseDocument(longestEscaped));
});

test("JSON import is bounded by the same UTF-8 byte limit as the file picker", () => {
  assert.equal(MAX_PROJECT_BYTES, 16 * 1024 * 1024);
  const huge = JSON.stringify(createDefaultDocument()) + " ".repeat(MAX_PROJECT_BYTES);
  assert.throws(() => parseDocument(huge), /too large/i);
});

test("optional page SEO metadata is rendered safely and legacy projects still reopen", () => {
  const fresh = createDefaultDocument();
  assert.equal(fresh.description, "");
  assert.equal(fresh.language, "en");
  fresh.description = 'Accessible & practical "component" sites <no-script>';
  fresh.language = "pt-BR";
  const html = exportHtml(fresh);
  assert.match(html, /<html lang="pt-BR">/);
  assert.match(html, /<meta name="description" content="Accessible &amp; practical &quot;component&quot; sites &lt;no-script&gt;">/);
  assert.doesNotMatch(html, /<no-script>|<script\b/);
  assert.deepEqual(parseDocument(JSON.stringify(fresh)), fresh);
  const legacy = createDefaultDocument();
  delete legacy.description;
  delete legacy.language;
  const imported = parseDocument(JSON.stringify(legacy));
  assert.equal(imported.description, "");
  assert.equal(imported.language, "en");
  assert.throws(() => parseDocument({...fresh, description: "x".repeat(301)}), /description/i);
  assert.throws(() => parseDocument({...fresh, description: { toString() {return "<script>";} }}), /description/i);
  assert.throws(() => parseDocument({...fresh, language: "en\" onmouseover=\"alert(1)"}), /language/i);
  assert.throws(() => parseDocument({...fresh, language: "fr\nFR"}), /language/i);
});
