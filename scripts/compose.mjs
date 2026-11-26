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

// Reviewed mappings describe the presentation and the missing host work,
// never claim that a section implements a backend or a live interaction.
const INTENTS = [
  ["pipeline", "crm-workspace", ["Deal queries, stages and authorized mutations"]],
  ["metrics", "metric-overview", ["Real metrics and calculation"]],
  ["inventory-search", "resource-workspace", ["Inventory data, search and pagination"]],
  ["record-search", "resource-workspace", ["Record data, search and pagination"]],
  ["account-management", "resource-crud", ["Account-specific fields, data and authorized CRUD routes"]],
  ["record-management", "resource-crud", ["Record data and authorized CRUD routes"]],
  ["team-management", "organization-members", ["Membership data, invitations and role authorization"]],
  ["billing", "billing-workspace", ["Billing provider, invoices and authorized account updates"]],
  ["sign-in", "auth-sign-in", ["Authentication, session handling and CSRF protection"]],
  ["notifications", "notification-center", ["Notification data and read-state persistence"]],
  ["settings", "settings-form", ["Settings persistence and server validation"]],
  ["product-intro", "hero-product", []],
  ["features", "feature-grid", []],
  ["pricing", "pricing-trio", []],
  ["faq", "faq", []],
  ["call-to-action", "cta-band", []],
  ["services", "services-grid", []],
  ["portfolio", "portfolio-grid", []],
  ["articles", "article-grid", []],
  ["resources", "resource-index", []],
  ["product-catalog", "product-collection", ["Product data, pricing and destination routes"]],
];

export function listIntents(release) {
  initialize(release);
  const sections = new Set(manifest.sections.map(s => s.id));
  return { release, intents: INTENTS.map(([id, section_id, host]) => {
    if (!sections.has(section_id)) throw new Error("Intent mapping needs review: " + id);
    return {id, section_id, status: host.length ? "presentation-only" : "static-content",
      host_requirements: [...host]};
  }) };
}

export function planIntent(input) {
  exactKeys(input, ["release","title","description","language","theme","requirements"], "intent plan");
  const catalog = listIntents(input.release);
  if (!Array.isArray(input.requirements) || input.requirements.length < 1 ||
      input.requirements.length > 50 ||
      input.requirements.some(id => typeof id !== "string" || !/^[a-z][a-z0-9-]{1,80}$/.test(id)) ||
      new Set(input.requirements).size !== input.requirements.length)
    throw new Error("Requirements must contain 1–50 unique lowercase intent IDs");
  const {requirements, ...base} = input;
  // Validate the shared document fields even when an intent is unresolved.
  parseDocument({schema: SCHEMA_VERSION, title: base.title, description: base.description,
    language: base.language, theme: base.theme, media: {}, blocks: []});
  const byId = new Map(catalog.intents.map(intent => [intent.id, intent]));
  const coverage = [], unresolved = [], selected = new Set();
  for (const id of requirements) {
    const intent = byId.get(id);
    if (!intent) { unresolved.push(id); continue; }
    coverage.push(intent);
    selected.add(intent.section_id);
  }
  return {release: input.release, ready: unresolved.length === 0,
    coverage, unresolved,
    composition: unresolved.length ? null : {...base,
      sections: [...selected].map(section_id => ({section_id}))},
    note: "Ready means every declared intent has a static section mapping, not a working application. Review sample content, routes and host requirements. Unresolved requirements block composition; do not infer a replacement."};
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
