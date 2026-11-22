/* Docs-only editor model. No dependency on a framework, editor engine or browser API. */
export const SCHEMA_VERSION = "syntyr.page.v1";
export const THEMES = Object.freeze(["studio", "grid", "noir", "industrial", "terminal", "corporate", "minimal", "auto"]);

const DEFINITIONS = {
  hero: {
    label: "Hero", description: "Lead with a headline and a clear action.",
    fields: {
      eyebrow: "MADE WITH SYNTYR",
      title: "Build your next website visually.",
      description: "A composable page built from semantic HTML and the Syntyr CSS system.",
      actionText: "Explore more", actionHref: "#features"
    }
  },
  features: {
    label: "Feature cards", description: "Introduce three benefits or services.",
    fields: {
      heading: "Everything you need",
      firstTitle: "Portable", firstText: "Export ordinary HTML and CSS.",
      secondTitle: "Adaptable", secondText: "Change your theme without rewriting markup.",
      thirdTitle: "Accessible", thirdText: "Native elements and meaningful structure."
    }
  },
  split: {
    label: "Text & action", description: "A focused explanation with a supporting link.",
    fields: {
      eyebrow: "BETTER BY DESIGN", heading: "Keep your content in control.",
      description: "Use Syntyr blocks to create a consistent page without a heavyweight runtime.",
      actionText: "Get started", actionHref: "#contact"
    }
  },
  quote: {
    label: "Testimonial", description: "A short quotation and its attribution.",
    fields: {
      quote: "Our team can move faster without losing control of the markup.",
      attribution: "A thoughtful customer"
    }
  },
  faq: {
    label: "FAQ", description: "Native disclosure questions using details and summary.",
    fields: {
      heading: "Frequently asked questions",
      firstQuestion: "Can I use this without React?", firstAnswer: "Yes. The exported page is HTML and CSS.",
      secondQuestion: "Can I host this myself?", secondAnswer: "Yes. Download the HTML and the matching Syntyr stylesheet."
    }
  },
  cta: {
    label: "Call to action", description: "Invite the reader to take one next step.",
    fields: {
      heading: "Ready to build?", description: "Your design. Your code. Your hosting.",
      actionText: "Contact us", actionHref: "#contact"
    }
  },
  footer: {
    label: "Footer", description: "Closing brand information and a link.",
    fields: {
      brand: "Your company", description: "Independent by design.",
      linkText: "Back to top", linkHref: "#top"
    }
  },
  header: {
    label: "Site header", description: "Brand name and primary navigation link.",
    fields: {
      brand: "Your company", linkText: "Learn more", linkHref: "#features"
    }
  }
};

export const BLOCK_TYPES = Object.freeze(Object.keys(DEFINITIONS));
export const BLOCK_DEFINITIONS = Object.freeze(DEFINITIONS);
const GALLERY_PREFIX = "gallery:";
const SECTION_PREFIX = "section:";
let GALLERY_DEFINITIONS = new Map();
let SECTION_DEFINITIONS = new Map();
const MAX_BLOCKS = 50;
const MAX_FIELD = 5000;
// 50 blocks x at most seven 5,000-code-unit fields fit even when JSON escaping
// expands control characters to six bytes each. Same byte cap on file and parser.
export const MAX_PROJECT_BYTES = 16 * 1024 * 1024;

function plainObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
function own(object, key) {
  return Object.prototype.hasOwnProperty.call(object, key);
}
function escapeHtml(value) {
  return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}
function safeHref(value, allowedAssets = []) {
  const href = value.trim();
  const asset = /^(?:\.\.\/)?assets\/([a-z0-9-]+\.svg)$/.exec(href);
  if (asset && allowedAssets.includes(asset[1])) return "../assets/" + asset[1];
  if (/^#[a-zA-Z][a-zA-Z0-9_-]*$/.test(href)) return href;
  if (/^\/(?!\/)[a-zA-Z0-9_./#?&=%+-]*$/.test(href)) return href;
  if (/^https:\/\/[a-zA-Z0-9.-]+(?::[0-9]+)?(?:[/?#][^\s"'<>]*)?$/i.test(href)) return href;
  return "#";
}

function decodeEntities(value) {
  const named = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: "\u00a0" };
  return value.replace(/&(#x[0-9a-f]+|#[0-9]+|amp|lt|gt|quot|apos|nbsp);/gi, (_, code) => {
    if (code.startsWith("#")) {
      const number = code[1].toLowerCase() === "x"
        ? parseInt(code.slice(2), 16) : parseInt(code.slice(1), 10);
      return number > 0 && number <= 0x10ffff && !(number >= 0xd800 && number <= 0xdfff)
        ? String.fromCodePoint(number) : "\ufffd";
    }
    return named[code.toLowerCase()];
  });
}
function buildGalleryDefinition(entry) {
  if (!plainObject(entry) || typeof entry.id !== "string" ||
      !/^[a-z][a-z0-9-]{1,80}$/.test(entry.id) ||
      typeof entry.title !== "string" || entry.title.length > 120 ||
      typeof entry.description !== "string" || entry.description.length > 1000 ||
      typeof entry.html !== "string" || entry.html.length > 30000 ||
      !Array.isArray(entry.required_stylesheets) || !entry.required_stylesheets.length ||
      entry.required_stylesheets.some(name => ![
        "syntyr.core.css", "syntyr.recipes.css", "syntyr.geometry.css", "syntyr.viz.css", "syntyr.semantic.css"
      ].includes(name)))
    throw new Error("Invalid gallery example metadata");
  // The static manifest is maintained with the repo, not imported from project
  // JSON. Reject dangerous markup regardless of its claimed source.
  if (/<\s*\/?\s*(script|iframe|object|embed|base|meta|link|style|svg|math)\b/i.test(entry.html) ||
      /\son[a-z]+\s*=/i.test(entry.html) ||
      /\b(?:href|src|action)\s*=\s*["']\s*(?:javascript|data):/i.test(entry.html))
    throw new Error("Unsafe gallery markup");
  const chunks = [];
  const fields = {};
  const fieldKinds = {};
  const names = { text: 0, href: 0, placeholder: 0 };
  function pushField(kind, value) {
    const key = kind + (++names[kind]);
    if (Object.keys(fields).length >= 60) throw new Error("Too many gallery fields");
    fields[key] = decodeEntities(value);
    fieldKinds[key] = kind;
    chunks.push({ field: key, kind });
  }
  // This is a static, validated HTML fragment; parse known quoted attributes
  // and text nodes only. No imported project can supply a template or tag.
  for (const part of entry.html.split(/(<[^>]*>)/g)) {
    if (!part) continue;
    if (part.startsWith("<")) {
      const attr = /\s(href|placeholder)="([^"]*)"/g;
      let cursor = 0;
      let match;
      while ((match = attr.exec(part))) {
        chunks.push(part.slice(cursor, match.index) + " " + match[1] + '="');
        pushField(match[1], match[2]);
        chunks.push('"');
        cursor = match.index + match[0].length;
      }
      chunks.push(part.slice(cursor));
    } else if (part.trim()) {
      const match = /^(\s*)([\s\S]*?)(\s*)$/.exec(part);
      chunks.push(match[1]);
      pushField("text", match[2]);
      chunks.push(match[3]);
    } else {
      chunks.push(part);
    }
  }
  if (!Object.keys(fields).length) throw new Error("Gallery example has no editable content");
  // Only explicitly reviewed local SVG assets are exportable; user-project
  // JSON cannot add asset paths or untrusted template markup.
  const assetNames = [...new Set([...entry.html.matchAll(
    /(?:src|href)="\.\.\/assets\/([a-z0-9-]+\.svg)"/g
  )].map(match => match[1]))];
  if (assetNames.some(name => !/^gallery-[a-z0-9-]+\.svg$/.test(name) && name !== "syntyr-mark.svg"))
    throw new Error("Unexpected gallery asset");
  return {
    label: entry.title, description: entry.description,
    requiredStylesheets: [...entry.required_stylesheets],
    fields, fieldKinds, chunks, assetNames
  };
}

export function registerGalleryManifest(manifest) {
  if (!plainObject(manifest) || manifest.schema_version !== 1 ||
      !Array.isArray(manifest.examples) || manifest.examples.length > 100 ||
      !Array.isArray(manifest.components) || !Array.isArray(manifest.themes))
    throw new Error("Unsupported gallery manifest schema");
  const next = new Map();
  for (const entry of manifest.examples) {
    const def = buildGalleryDefinition(entry);
    const type = GALLERY_PREFIX + entry.id;
    if (next.has(type)) throw new Error("Duplicate gallery example");
    next.set(type, def);
  }
  if (!next.size) throw new Error("Gallery manifest has no examples");
  GALLERY_DEFINITIONS = next; // replace atomically after validation
  return next.size;
}

export function galleryBlockTypes() {
  return [...GALLERY_DEFINITIONS.keys()];
}

export function registerSectionManifest(manifest) {
  if (!plainObject(manifest) || manifest.schema_version !== 1 ||
      typeof manifest.source_version !== "string" ||
      !Array.isArray(manifest.sections) || !manifest.sections.length ||
      manifest.sections.length > 150)
    throw new Error("Unsupported section manifest schema");
  const next = new Map();
  for (const entry of manifest.sections) {
    if (typeof entry.category !== "string" ||
        !/^[A-Za-z][A-Za-z ]{1,40}$/.test(entry.category))
      throw new Error("Invalid section category");
    const def = buildGalleryDefinition(entry);
    const type = SECTION_PREFIX + entry.id;
    if (next.has(type)) throw new Error("Duplicate section");
    next.set(type, {...def, category: entry.category});
  }
  SECTION_DEFINITIONS = next;
  return next.size;
}

export function sectionBlockTypes() {
  return [...SECTION_DEFINITIONS.keys()];
}

export function getBlockDefinition(type) {
  return own(DEFINITIONS, type) ? DEFINITIONS[type] :
    (GALLERY_DEFINITIONS.get(type) || SECTION_DEFINITIONS.get(type));
}

function scopeGalleryIds(html, blockId) {
  const ids = new Set([...html.matchAll(/(?:^|\s)id="([a-zA-Z][a-zA-Z0-9_-]*)"/g)].map(match => match[1]));
  if (!ids.size) return html;
  const prefixed = value => ids.has(value) ? blockId + "--" + value : value;
  return html.replace(/<[^>]*>/g, tag => tag.replace(
    /(^|\s)(id|for|list|commandfor|popovertarget|aria-labelledby|aria-describedby|href)="([^"]*)"/g,
    (match, whitespace, attribute, value) => {
      let updated = value;
      if (attribute === "href" && value.startsWith("#")) {
        updated = "#" + prefixed(value.slice(1));
      } else if (attribute === "aria-labelledby" || attribute === "aria-describedby") {
        updated = value.split(/\s+/).map(prefixed).join(" ");
      } else if (attribute !== "href") {
        updated = prefixed(value);
      }
      return whitespace + attribute + '="' + updated + '"';
    }
  ));
}
function renderGalleryBlock(block, def, assetPrefix) {
  let html = def.chunks.map(part => {
    if (typeof part === "string") return part;
    const value = block.props[part.field];
    return escapeHtml(part.kind === "href" ? safeHref(value, def.assetNames) : value);
  }).join("");
  // Canonical snippets use ../assets from docs/blocks.html, while exported
  // standalone pages keep all images alongside index.html in assets/.
  // Only known first-party SVGs are rewritten, never arbitrary user URLs.
  html = html.replace(/(\s(?:href|src))="\.\.\/assets\/([a-z0-9-]+\.svg)"/g,
    (match, attribute, name) => def.assetNames.includes(name)
      ? attribute + '="' + assetPrefix + name + '"' : match);
  // Every copied snippet's Studio theme is a preview default, not an override
  // of the composer-selected theme.
  if (block.type.startsWith(SECTION_PREFIX))
    html = html.replace(/\sdata-syn-theme="studio"/g, "");
  return '<section class="syn-region" data-syntyr-block-id="' + escapeHtml(block.id) +
    '" aria-label="' + escapeHtml(def.label) + '">' +
    scopeGalleryIds(html, block.id) + "</section>";
}

function action(label, href, primary = true) {
  const variant = primary ? " syn-button--primary" : "";
  return '<a class="syn-button' + variant + '" href="' + escapeHtml(safeHref(href)) +
    '">' + escapeHtml(label) + "</a>";
}
function field(name, value) {
  return '<span class="syn-eyebrow">' + escapeHtml(value) + "</span>";
}
function heading(level, value) {
  return "<h" + level + ' class="syn-heading">' + escapeHtml(value) + "</h" + level + ">";
}
function paragraph(value) {
  return '<p class="syn-muted">' + escapeHtml(value) + "</p>";
}

export function createBlock(type, id = String(type).replace(/^(?:gallery|section):/, "").slice(0, 42) + "-1") {
  if (typeof type !== "string" || !getBlockDefinition(type))
    throw new Error("Unknown block: " + String(type));
  if (!/^[a-zA-Z0-9_-]{1,64}$/.test(id)) throw new Error("Invalid block id");
  return { id, type, props: { ...getBlockDefinition(type).fields } };
}

export function createDefaultDocument() {
  return {
    schema: SCHEMA_VERSION,
    title: "My Syntyr page",
    description: "",
    language: "en",
    theme: "studio",
    blocks: [
      createBlock("hero", "hero-1"),
      createBlock("features", "features-1"),
      createBlock("cta", "cta-1")
    ]
  };
}

export function projectNeedsGalleryManifest(candidate) {
  return plainObject(candidate) && Array.isArray(candidate.blocks) &&
    candidate.blocks.some(block => plainObject(block) &&
      typeof block.type === "string" && block.type.startsWith(GALLERY_PREFIX));
}
export function projectNeedsSectionManifest(candidate) {
  return plainObject(candidate) && Array.isArray(candidate.blocks) &&
    candidate.blocks.some(block => plainObject(block) &&
      typeof block.type === "string" && block.type.startsWith(SECTION_PREFIX));
}

export function parseDocument(input) {
  let page;
  if (typeof input === "string") {
    if (new TextEncoder().encode(input).byteLength > MAX_PROJECT_BYTES)
      throw new Error("Project JSON is too large");
    try { page = JSON.parse(input); }
    catch { throw new Error("Invalid project JSON"); }
  } else {
    page = input;
  }
  if (!plainObject(page)) throw new Error("Page must be an object");
  if (page.schema !== SCHEMA_VERSION) throw new Error("Unsupported page schema");
  if (typeof page.title !== "string" || page.title.length > 160) throw new Error("Invalid page title");
  const description = page.description === undefined ? "" : page.description;
  const language = page.language === undefined ? "en" : page.language;
  if (typeof description !== "string" || description.length > 300)
    throw new Error("Invalid page description");
  if (typeof language !== "string" ||
      !/^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8}){0,3}$/.test(language))
    throw new Error("Invalid page language");
  if (!THEMES.includes(page.theme)) throw new Error("Unknown page theme");
  if (!Array.isArray(page.blocks) || page.blocks.length > MAX_BLOCKS)
    throw new Error("Page must contain at most 50 blocks");
  const ids = new Set();
  const blocks = page.blocks.map((block) => {
    if (!plainObject(block) || typeof block.type !== "string" ||
        !getBlockDefinition(block.type))
      throw new Error("Unknown block: " + String(block?.type));
    if (typeof block.id !== "string" || !/^[a-zA-Z0-9_-]{1,64}$/.test(block.id))
      throw new Error("Invalid block id");
    if (ids.has(block.id)) throw new Error("Duplicate block id: " + block.id);
    ids.add(block.id);
    if (Object.keys(block).some(key => !["id", "type", "props"].includes(key)))
      throw new Error("Unknown block property");
    if (!plainObject(block.props)) throw new Error("Invalid block properties");
    const declared = getBlockDefinition(block.type).fields;
    const props = {};
    for (const name of Object.keys(declared)) {
      if (!own(block.props, name) || typeof block.props[name] !== "string")
        throw new Error("Field " + name + " must be a string");
      if (block.props[name].length > MAX_FIELD) throw new Error("Field " + name + " is too long");
      props[name] = block.props[name];
    }
    if (Object.keys(block.props).some(key => !own(declared, key)))
      throw new Error("Unknown block property");
    return { id: block.id, type: block.type, props };
  });
  return { schema: SCHEMA_VERSION, title: page.title, description, language, theme: page.theme, blocks };
}

export function moveBlock(page, from, to) {
  const normalized = parseDocument(page);
  if (!Number.isInteger(from) || !Number.isInteger(to) ||
      from < 0 || to < 0 || from >= normalized.blocks.length || to >= normalized.blocks.length)
    throw new Error("Move indices out of range");
  const [block] = normalized.blocks.splice(from, 1);
  normalized.blocks.splice(to, 0, block);
  return normalized;
}

export function insertBlockAfter(page, afterId, block) {
  const normalized = parseDocument(page);
  if (afterId !== null && !normalized.blocks.some(existing => existing.id === afterId))
    throw new Error("Unknown insertion position");
  const index = afterId === null ? normalized.blocks.length :
    normalized.blocks.findIndex(existing => existing.id === afterId) + 1;
  normalized.blocks.splice(index, 0, block);
  return parseDocument(normalized);
}

export function duplicateBlock(page, index, id) {
  const normalized = parseDocument(page);
  if (!Number.isInteger(index) || index < 0 || index >= normalized.blocks.length)
    throw new Error("Duplicate source index out of range");
  const block = normalized.blocks[index];
  return insertBlockAfter(normalized, block.id, {
    ...block, id, props: {...block.props}
  });
}

export function requiredAssets(page) {
  const names = new Set();
  for (const block of parseDocument(page).blocks) {
    const def = getBlockDefinition(block.type);
    for (const asset of def.assetNames || []) names.add(asset);
  }
  return [...names].sort();
}

function renderBlock(block, anchor, assetPrefix) {
  const p = block.props;
  const template = GALLERY_DEFINITIONS.get(block.type) || SECTION_DEFINITIONS.get(block.type);
  if (template) return renderGalleryBlock(block, template, assetPrefix);
  const id = ' data-syntyr-block-id="' + escapeHtml(block.id) + '"';
  const sectionAnchor = anchor ? ' id="' + escapeHtml(anchor) + '"' : "";
  switch (block.type) {
    case "header":
      return '<header class="syn-header"' + id + '><strong class="syn-logo">' +
        escapeHtml(p.brand) + '</strong><nav aria-label="Primary navigation">' +
        action(p.linkText, p.linkHref, false) + "</nav></header>";
    case "hero":
      return '<section class="syn-stage"' + sectionAnchor + id + ">" + field("eyebrow", p.eyebrow) +
        '<h1 class="syn-title">' + escapeHtml(p.title) + '</h1><p class="syn-lede">' +
        escapeHtml(p.description) + '</p><div class="syn-inline">' +
        action(p.actionText, p.actionHref) + "</div></section>";
    case "features": {
      const cards = [["firstTitle", "firstText"], ["secondTitle", "secondText"], ["thirdTitle", "thirdText"]];
      return '<section class="syn-region"' + sectionAnchor + id + ">" + heading(2, p.heading) +
        '<div class="syn-grid">' + cards.map(([title, text]) =>
          '<article class="syn-panel">' + heading(3, p[title]) + paragraph(p[text]) + "</article>"
        ).join("") + "</div></section>";
    }
    case "split":
      return '<section class="syn-panel syn-region"' + id + ">" + field("eyebrow", p.eyebrow) +
        heading(2, p.heading) + paragraph(p.description) + action(p.actionText, p.actionHref) + "</section>";
    case "quote":
      return '<figure class="syn-panel"' + id + '><blockquote><p>' +
        escapeHtml(p.quote) + '</p></blockquote><figcaption class="syn-caption">' +
        escapeHtml(p.attribution) + "</figcaption></figure>";
    case "faq":
      return '<section class="syn-region"' + id + ">" + heading(2, p.heading) +
        '<details><summary>' + escapeHtml(p.firstQuestion) + "</summary>" +
        paragraph(p.firstAnswer) + '</details><details><summary>' +
        escapeHtml(p.secondQuestion) + "</summary>" + paragraph(p.secondAnswer) + "</details></section>";
    case "cta":
      return '<section class="syn-panel syn-region"' + sectionAnchor + id + ">" +
        heading(2, p.heading) + paragraph(p.description) +
        action(p.actionText, p.actionHref) + "</section>";
    case "footer":
      return '<footer class="syn-region"' + id + '><strong>' + escapeHtml(p.brand) +
        '</strong>' + paragraph(p.description) + action(p.linkText, p.linkHref, false) + "</footer>";
    default:
      throw new Error("Unknown block");
  }
}

export function renderSections(page, {previewAssets = false} = {}) {
  const assetPrefix = previewAssets === true ? "../assets/" : "assets/";
  const anchors = new Set();
  return parseDocument(page).blocks.map((block) => {
    const base = { hero: "top", features: "features", cta: "contact" }[block.type];
    const anchor = base ? (anchors.has(base) ? "section-" + block.id : base) : "";
    if (base) anchors.add(base);
    return renderBlock(block, anchor, assetPrefix);
  }).join("\n");
}

export function exportHtml(page, {previewAssets = false} = {}) {
  const normalized = parseDocument(page);
  return [
    "<!doctype html>",
    '<html lang="' + escapeHtml(normalized.language) + '"><head><meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    "<title>" + escapeHtml(normalized.title) + "</title>",
    ...(normalized.description ? ['<meta name="description" content="' +
      escapeHtml(normalized.description) + '">'] : []),
    '<link rel="stylesheet" href="syntyr.all.css">',
    "</head>",
    '<body class="syn-root syn-page" data-syn-theme="' + escapeHtml(normalized.theme) + '">',
    '<main class="syn-shell">' + renderSections(normalized, {previewAssets}) + "</main>",
    "</body></html>"
  ].join("\n");
}
