import test from "node:test";
import assert from "node:assert/strict";
import { createStoredZip, SITE_ZIP_MAX_ENTRIES } from "../docs/page-builder-zip.mjs";

const read = bytes => new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
function entries(zip) {
  const view = read(zip);
  const decoder = new TextDecoder();
  const contents = new Map();
  let offset = 0;
  while (offset + 4 <= zip.byteLength && view.getUint32(offset, true) === 0x04034b50) {
    const len = view.getUint16(offset + 26, true);
    const extra = view.getUint16(offset + 28, true);
    const dataSize = view.getUint32(offset + 18, true);
    const name = decoder.decode(zip.slice(offset + 30, offset + 30 + len));
    const start = offset + 30 + len + extra;
    contents.set(name, decoder.decode(zip.slice(start, start + dataSize)));
    offset = start + dataSize;
  }
  return contents;
}

test("generates an offline static ZIP with HTML, CSS, and no JavaScript", () => {
  const zip = createStoredZip([
    {name: "index.html", content: "<!doctype html><html><body>TEST</body></html>"},
    {name: "syntyr.all.css", content: ".syn-root{color:black}"},
    {name: "assets/gallery-horizon.svg", content: "<svg/>"},
    {name: "LICENSE", content: "MIT License"}
  ]);
  assert.ok(zip instanceof Uint8Array);
  const files = entries(zip);
  assert.deepEqual([...files.keys()], ["index.html", "syntyr.all.css", "assets/gallery-horizon.svg", "LICENSE"]);
  assert.equal(files.get("index.html").includes("TEST"), true);
  assert.equal(zip[zip.length - 22], 0x50); // valid EOCD signature
});

test("ZIP exporter fails closed for dangerous paths, duplicates and oversized input", () => {
  for (const invalid of ["../secrets.txt", "/root.txt", "scripts/app.js", "x\\y", "assets//x.svg", ""]) {
    assert.throws(() => createStoredZip([{name: invalid, content: "x"}]), /path|name|file/i);
  }
  assert.throws(() => createStoredZip([
    {name:"index.html",content:"a"},{name:"index.html",content:"b"}
  ]), /duplicate/i);
  assert.throws(() => createStoredZip([
    {name:"index.html",content:"x".repeat(20)}
  ], {maxBytes: 10}), /large|limit/i);
});

test("keeps standalone and multi-page ZIP entry counts bounded", () => {
  const files = Array.from({length: SITE_ZIP_MAX_ENTRIES + 1}, (_, n) => ({
    name: "assets/gallery-" + n + ".svg", content: "<svg/>"
  }));
  assert.throws(() => createStoredZip(files.slice(0, 129)), /file count/i);
  assert.doesNotThrow(() => createStoredZip(files.slice(0, -1), {maxEntries: SITE_ZIP_MAX_ENTRIES}));
  assert.throws(() => createStoredZip(files, {maxEntries: SITE_ZIP_MAX_ENTRIES}), /file count/i);
  assert.throws(() => createStoredZip(files, {maxEntries: files.length}), /file count/i);
});
