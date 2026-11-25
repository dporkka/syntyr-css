#!/usr/bin/env node
/** Optional offline authoring tool. Reuses the browser-compatible composition model. */
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import {createComposer} from "../docs/composition-model.mjs";
const manifest = JSON.parse(readFileSync(new URL("../metadata/section-composer.v1.json", import.meta.url), "utf8"));
const version = readFileSync(new URL("../VERSION", import.meta.url), "utf8").trim();
const MAX_INPUT = 256 * 1024;
export const {listSections, listIntents, planIntent, compose} = createComposer(manifest, version);

async function main(args) {
  if (args.length === 2 && args[0] === "--list") return listSections(args[1]);
  if (args.length === 2 && args[0] === "--list-intents") return listIntents(args[1]);
  const planning = args.length === 1 && args[0] === "--plan";
  if (args.length && !planning) throw new Error("Usage: compose.mjs [--list RELEASE | --list-intents RELEASE | --plan]");
  const chunks = [];
  let size = 0;
  for await (const chunk of process.stdin) {
    size += chunk.length;
    if (size > MAX_INPUT) throw new Error("Composition JSON exceeds 256 KiB");
    chunks.push(chunk);
  }
  const input = JSON.parse(Buffer.concat(chunks).toString("utf8"));
  if (planning) {
    const plan = planIntent(input);
    if (!plan.ready) process.exitCode = 2;
    return plan;
  }
  return compose(input);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const result = await main(process.argv.slice(2));
    process.stdout.write(JSON.stringify(result, null, 2) + "\n");
  } catch (error) {
    process.stderr.write("Composition error: " + error.message + "\n");
    process.exitCode = 1;
  }
}
