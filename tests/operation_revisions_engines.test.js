"use strict";
// Optional developer-only test runner validation. No Syntyr runtime dependency.
const test = require("node:test");
const assert = require("node:assert/strict");
const {spawnSync} = require("node:child_process");
const path = require("node:path");
const script = path.join(__dirname, "operation_revisions_browser.js");

for (const value of ["chromiun", "", "  ", "chromium,phantom"]) {
  test(`browser check rejects an invalid engine selection: ${JSON.stringify(value)}`, () => {
    const result = spawnSync(process.execPath, [script], {
      encoding: "utf8",
      env: {...process.env, SYNTYR_TEST_ENGINES: value}
    });
    assert.notEqual(result.status, 0,
      `invalid selection ${JSON.stringify(value)} must not silently pass`);
    assert.match(result.stderr, /Unsupported|unknown|no valid|empty/i);
  });
}
