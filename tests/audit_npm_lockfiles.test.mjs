import test from "node:test";
import assert from "node:assert/strict";
import {mkdtempSync, mkdirSync, writeFileSync, symlinkSync, rmSync} from "node:fs";
import {tmpdir} from "node:os";
import {join} from "node:path";
import {discoverLocks, auditLocks} from "../scripts/audit_npm_lockfiles.mjs";

test("discovers nested lockfiles but never follows symlinks or dependency directories", () => {
  const root = mkdtempSync(join(tmpdir(), "syntyr-audit-"));
  try {
    for (const name of ["examples/a", "tools/new tool", "node_modules/skip", ".git/skip"]) {
      mkdirSync(join(root, name), {recursive: true});
      writeFileSync(join(root, name, "package-lock.json"), "{}");
    }
    symlinkSync(join(root, "examples"), join(root, "link"), "dir");
    assert.deepEqual(discoverLocks(root), [join(root, "examples/a"), join(root, "tools/new tool")]);
  } finally { rmSync(root, {recursive: true, force: true}); }
});

test("audits every discovered lock without lifecycle scripts and fails closed", () => {
  const calls = [];
  const run = (cmd, args) => {
    calls.push([cmd, args]);
    return {status: calls.length === 1 ? 1 : 0};
  };
  assert.equal(auditLocks(["a", "b with spaces"], run), 1);
  assert.deepEqual(calls, [
    ["npm", ["audit", "--prefix", "a", "--package-lock-only", "--ignore-scripts", "--audit-level=high"]],
    ["npm", ["audit", "--prefix", "b with spaces", "--package-lock-only", "--ignore-scripts", "--audit-level=high"]]
  ]);
  assert.equal(auditLocks(["a"], () => ({status: 0})), 0);
  assert.throws(() => auditLocks([], run), /No npm lockfiles/);
});
