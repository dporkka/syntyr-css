// Optional maintainer CI only. No consumer dependencies or lifecycle scripts.
import {readdirSync} from "node:fs";
import {join, resolve} from "node:path";
import {fileURLToPath} from "node:url";
import {spawnSync} from "node:child_process";

const root = fileURLToPath(new URL("../", import.meta.url));
const excluded = new Set([".git", "node_modules"]);

export function discoverLocks(directory) {
  const locks = [];
  for (const entry of readdirSync(directory, {withFileTypes: true})) {
    if (excluded.has(entry.name) || entry.isSymbolicLink()) continue;
    const path = join(directory, entry.name);
    if (entry.isDirectory()) locks.push(...discoverLocks(path));
    else if (entry.isFile() && entry.name === "package-lock.json") locks.push(directory);
  }
  return locks.sort();
}

export function auditLocks(locks, run = spawnSync) {
  if (!locks.length) throw new Error("No npm lockfiles found; refusing an empty security audit");
  let failed = false;
  for (const directory of locks) {
    console.log("Auditing " + directory);
    const result = run("npm", ["audit", "--prefix", directory, "--package-lock-only",
      "--ignore-scripts", "--audit-level=high"], {stdio: "inherit"});
    if (result.error || result.status !== 0) failed = true;
  }
  return failed ? 1 : 0;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const locks = discoverLocks(root);
  if (process.argv[2] === "--list") console.log(locks.join("\n"));
  else process.exitCode = auditLocks(locks);
}
