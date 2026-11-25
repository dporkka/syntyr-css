#!/usr/bin/env node
/** Optional offline authoring tool. Reuses the existing page-builder model. */
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import {
  registerSectionManifest, getBlockDefinition, createBlock,
  parseDocument, exportHtml, requiredAssets, SCHEMA_VERSION,
} from "../docs/page-builder-model.mjs";

const manifest = JSON.parse(readFileSync(new URL("../metadata/section-composer.v1.json", import.meta.url), "utf8"));
const version = readFileSync(new URL("../VERSION", import.meta.url), "utf8").trim();
const MAX_INPUT = 256 * 1024;
const own = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
const object = x => x !== null && typeof x === "object" && !Array.isArray(x);

function initialize(release) {
  if (release !== version || manifest.source_version !== version || manifest.schema_version !== 1 ||
      manifest.runtime_requirement !== "none")
    throw new Error("Explicit matching source-candidate release required");
  registerSectionManifest(manifest);
}

function exactKeys(value, keys, label) {
  if (!object(value) || Object.keys(value).some(key => !keys.includes(key)))
    throw new Error("Invalid or unknown " + label + " property");
}

export function listSections(release) {
  initialize(release);
  return { release, sections: manifest.sections.map(entry => {
    const def = getBlockDefinition("section:" + entry.id);
    return { id: entry.id, title: entry.title, description: entry.description,
      category: entry.category, fields: {...def.fields}, field_kinds: {...def.fieldKinds},
      required_stylesheets: [...entry.required_stylesheets] };
  }) };
}

export function compose(input) {
  exactKeys(input, ["release", "title", "description", "language", "theme", "sections"], "composition");
  initialize(input.release);
  if (!Array.isArray(input.sections) || input.sections.length < 1 || input.sections.length > 50)
    throw new Error("Composition requires 1–50 sections");
  const blocks = input.sections.map((entry, index) => {
    exactKeys(entry, ["section_id", "fields"], "section");
    if (typeof entry.section_id !== "string" || !/^[a-z][a-z0-9-]{1,80}$/.test(entry.section_id))
      throw new Error("Invalid section ID");
    const block = createBlock("section:" + entry.section_id, "section-" + (index + 1));
    const fields = entry.fields === undefined ? {} : entry.fields;
    exactKeys(fields, Object.keys(block.props), "field");
    for (const [key, value] of Object.entries(fields)) {
      if (!own(block.props, key) || typeof value !== "string") throw new Error("Invalid field");
      block.props[key] = value;
    }
    return block;
  });
  const project = parseDocument({schema: SCHEMA_VERSION, title: input.title,
    description: input.description, language: input.language, theme: input.theme,
    media: {}, blocks});
  return {release: input.release, release_status: "unreleased_candidate",
    project, html: exportHtml(project), stylesheets: ["syntyr.all.css"],
    assets: requiredAssets(project),
    note: "Scriptless canonical sections with editable sample content. Host routes and interactions are not generated. Invalid links follow the editor's safe fallback. Copy listed assets and the matching candidate CSS alongside the HTML."};
}

async function main(args) {
  if (args.length === 2 && args[0] === "--list") return listSections(args[1]);
  if (args.length) throw new Error("Usage: compose.mjs [--list RELEASE]; otherwise read JSON from stdin");
  const chunks = [];
  let size = 0;
  for await (const chunk of process.stdin) {
    size += chunk.length;
    if (size > MAX_INPUT) throw new Error("Composition JSON exceeds 256 KiB");
    chunks.push(chunk);
  }
  return compose(JSON.parse(Buffer.concat(chunks).toString("utf8")));
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
