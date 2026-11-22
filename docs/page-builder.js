/* Docs-only, dependency-free visual composition. The shipped Syntyr CSS stays JS-free. */
import {
  BLOCK_TYPES, THEMES, MAX_PROJECT_BYTES,
  registerGalleryManifest, galleryBlockTypes, registerSectionManifest, sectionBlockTypes,
  getBlockDefinition, createBlock, createDefaultDocument, parseDocument, moveBlock,
  duplicateBlock, insertBlockAfter, exportHtml, requiredAssets,
  projectNeedsGalleryManifest, projectNeedsSectionManifest
} from "./page-builder-model.mjs";
import { createStoredZip } from "./page-builder-zip.mjs";

const byId = (id) => document.getElementById(id);
const palette = byId("builder-palette");
const galleryPalette = byId("builder-gallery-palette");
const gallerySearch = byId("builder-gallery-search");
const sectionPalette = byId("builder-section-palette");
const sectionSearch = byId("builder-section-search");
const sectionCategory = byId("builder-section-category");
const outline = byId("builder-outline");
const inspector = byId("builder-inspector");
const preview = byId("builder-preview");
const status = byId("builder-status");
const theme = byId("builder-theme");
const title = byId("builder-page-title");
const viewport = byId("builder-viewport");
const viewportFrame = byId("builder-viewport-frame");
const undo = byId("builder-undo");
const redo = byId("builder-redo");
const history = [];
const future = [];
let page = createDefaultDocument();
let selectedId = page.blocks[0].id;
let sequence = 4;
let draggingIndex = null;
let titleEditing = false;

function notify(message) {
  status.textContent = message;
}
function remember(snapshot = JSON.stringify(page)) {
  history.push(snapshot);
  if (history.length > 40) history.shift();
  future.length = 0;
  updateHistoryButtons();
}
function updateHistoryButtons() {
  undo.disabled = !history.length;
  redo.disabled = !future.length;
}
function commit(next, message) {
  const normalized = parseDocument(next);
  remember();
  page = normalized;
  if (!page.blocks.some(block => block.id === selectedId)) selectedId = page.blocks[0]?.id || null;
  redraw();
  notify(message);
}
function makeElement(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined && text !== null) element.textContent = text;
  if (className) element.className = className;
  return element;
}
function makeButton(label, action, disabled = false) {
  const element = makeElement("button", label);
  element.type = "button";
  element.dataset.action = action;
  element.disabled = disabled;
  return element;
}

function appendPaletteButton(target, type) {
  const def = getBlockDefinition(type);
  const button = makeElement("button", null, "builder-add");
  button.type = "button";
  button.dataset.blockType = type;
  button.append(makeElement("strong", "+ " + def.label), makeElement("small", def.description));
  target.append(button);
}
function renderPalette() {
  palette.replaceChildren();
  for (const type of BLOCK_TYPES) appendPaletteButton(palette, type);
}
function renderGalleryPalette() {
  galleryPalette.replaceChildren();
  const terms = gallerySearch.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  let count = 0;
  for (const type of galleryBlockTypes()) {
    const def = getBlockDefinition(type);
    const searchable = (def.label + " " + def.description + " " + type).toLocaleLowerCase();
    if (!terms.every(term => searchable.includes(term))) continue;
    appendPaletteButton(galleryPalette, type);
    count += 1;
  }
  byId("builder-gallery-count").textContent = count + " gallery examples.";
}
gallerySearch.addEventListener("input", renderGalleryPalette);
async function loadGallery() {
  try {
    const url = new URL("../metadata/component-gallery.v1.json", import.meta.url);
    const response = await fetch(url, { credentials: "same-origin" });
    if (!response.ok) throw new Error("HTTP " + response.status);
    const manifest = await response.json();
    const count = registerGalleryManifest(manifest);
    renderGalleryPalette();
    notify(count + " manifest-backed gallery examples available.");
  } catch {
    byId("builder-gallery-count").textContent = "Gallery unavailable; native page sections still work.";
    notify("Optional gallery could not load. The basic page composer remains usable.");
  }
}
function renderSectionPalette() {
  sectionPalette.replaceChildren();
  const terms = sectionSearch.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  const category = sectionCategory.value;
  let count = 0;
  for (const type of sectionBlockTypes()) {
    const def = getBlockDefinition(type);
    if (category !== "all" && def.category !== category) continue;
    const searchable = (def.label + " " + def.description + " " + def.category + " " + type).toLocaleLowerCase();
    if (!terms.every(term => searchable.includes(term))) continue;
    appendPaletteButton(sectionPalette, type);
    count++;
  }
  byId("builder-section-count").textContent =
    count + " of " + sectionBlockTypes().length + " copy-owned sections.";
}
sectionSearch.addEventListener("input", renderSectionPalette);
sectionCategory.addEventListener("change", renderSectionPalette);
async function loadSections() {
  try {
    const url = new URL("../metadata/section-composer.v1.json", import.meta.url);
    const response = await fetch(url, {credentials: "same-origin"});
    if (!response.ok) throw new Error("HTTP " + response.status);
    const manifest = await response.json();
    const count = registerSectionManifest(manifest);
    for (const category of [...new Set(manifest.sections.map(item => item.category))].sort()) {
      const option = makeElement("option", category);
      option.value = category;
      sectionCategory.append(option);
    }
    renderSectionPalette();
    notify(count + " copy-owned sections available for static page composition.");
  } catch {
    byId("builder-section-count").textContent = "Website sections unavailable; basic blocks still work.";
    notify("Section manifest unavailable. The basic page composer remains usable.");
  }
}

function renderOutline() {
  const focusedButton = outline.contains(document.activeElement)
    ? document.activeElement.closest("button[data-action]") : null;
  const priorRow = focusedButton?.closest("[data-block-id]");
  const focusedId = priorRow?.dataset.blockId;
  const priorIndex = priorRow ? Number(priorRow.dataset.index) : 0;
  const focusedAction = focusedButton?.dataset.action;
  outline.replaceChildren();
  page.blocks.forEach((block, index) => {
    const item = makeElement("li", null, "builder-outline-item");
    item.draggable = true;
    item.dataset.index = String(index);
    item.dataset.blockId = block.id;
    item.dataset.selected = String(block.id === selectedId);
    const name = makeButton((index + 1) + ". " + getBlockDefinition(block.type).label, "select");
    name.className = "builder-outline-select";
    name.setAttribute("aria-label", "Edit " + getBlockDefinition(block.type).label + ", block " + (index + 1));
    const actions = makeElement("div", null, "builder-outline-actions");
    actions.append(
      makeButton("↑ Up", "up", index === 0),
      makeButton("↓ Down", "down", index === page.blocks.length - 1),
      makeButton("First", "first", index === 0),
      makeButton("Last", "last", index === page.blocks.length - 1),
      makeButton("Duplicate", "duplicate", page.blocks.length >= 50),
      makeButton("Remove", "remove")
    );
    item.append(name, actions);
    outline.append(item);
  });
  if (focusedButton) {
    const moved = page.blocks.findIndex(block => block.id === focusedId);
    const position = moved < 0 ? Math.min(priorIndex, page.blocks.length - 1) : moved;
    const row = outline.children[position];
    const replacement = [...(row?.querySelectorAll("button[data-action]") || [])]
      .find(button => button.dataset.action === focusedAction && !button.disabled)
      || row?.querySelector('button[data-action="select"]')
      || palette.querySelector("button");
    replacement?.focus();
  }
  updateHistoryButtons();
}
function renderInspector() {
  inspector.replaceChildren();
  const block = page.blocks.find(item => item.id === selectedId);
  if (!block) {
    inspector.append(makeElement("p", "Add or select a block to edit its content."));
    byId("builder-inspector-help").textContent = "No block selected.";
    return;
  }
  const def = getBlockDefinition(block.type);
  byId("builder-inspector-help").textContent = def.description;
  inspector.append(makeElement("p", def.label, "builder-block-name"));
  for (const name of Object.keys(def.fields)) {
    const label = makeElement("label", null, "syn-label");
    const fieldKind = def.fieldKinds?.[name];
    const friendlyName = fieldKind
      ? name.replace(/(\d+)$/, " $1").toUpperCase() + " · " + String(block.props[name]).slice(0, 28)
      : name.replace(/([A-Z])/g, " $1").toUpperCase();
    label.append(document.createTextNode(friendlyName));
    const value = block.props[name];
    const multi = value.length > 65 || /description|answer|quote|Text$/i.test(name);
    const control = makeElement(multi ? "textarea" : "input", null, "syn-input");
    if (multi) control.rows = 3;
    else control.type = "text"; // Also supports #anchors and /relative paths.
    control.value = value;
    control.maxLength = 5000;
    control.dataset.field = name;
    control.autocomplete = "off";
    let editing = false;
    control.addEventListener("input", () => {
      if (!editing) { remember(); editing = true; }
      const current = page.blocks.find(item => item.id === selectedId);
      if (!current) return;
      current.props[name] = control.value;
      renderPreview();
      notify("Block content updated. Save project JSON to keep it editable.");
    });
    control.addEventListener("blur", () => { editing = false; });
    label.append(control);
    inspector.append(label);
  }
}

function renderPreview() {
  // Imported content is validated and every user string escaped by exportHtml.
  // The iframe cannot run scripts or submit forms, including pasted hostile content.
  const styleOrigin = /^https?:$/.test(location.protocol) ? location.origin : "'self'";
  const csp = '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'self\' \'unsafe-inline\' ' +
    styleOrigin + '; img-src \'self\' data:; base-uri \'none\'; form-action \'none\'">';
  preview.srcdoc = exportHtml(page, {previewAssets: true})
    .replace('href="syntyr.all.css"', 'href="../dist/syntyr.all.css"')
    .replace("</head>", csp + "</head>");
}
function highlightPreviewSelection(frameDoc) {
  for (const block of frameDoc.querySelectorAll("[data-syntyr-block-id]")) {
    const active = block.dataset.syntyrBlockId === selectedId;
    block.style.outline = active ? "2px solid var(--syn-accent)" : "";
    block.style.outlineOffset = active ? "3px" : "";
  }
}
preview.addEventListener("load", () => {
  try {
    const frameDoc = preview.contentDocument;
    if (!frameDoc) return;
    highlightPreviewSelection(frameDoc);
    frameDoc.addEventListener("click", (event) => {
      // Prevent navigation; preserve details/summary native disclosure behavior.
      if (event.target.closest("a[href]")) event.preventDefault();
      const block = event.target.closest("[data-syntyr-block-id]");
      if (block && block.dataset.syntyrBlockId !== selectedId) {
        selectedId = block.dataset.syntyrBlockId;
        renderOutline();
        renderInspector();
        // Do not replace the iframe: that would close native FAQ disclosures.
        highlightPreviewSelection(frameDoc);
      }
    });
  } catch {
    notify("The sandbox prevented preview selection. Edit using the page outline.");
  }
});
function redraw() {
  title.value = page.title;
  theme.value = page.theme;
  renderOutline();
  renderInspector();
  renderPreview();
}
function nextBlockId(type) {
  let id;
  do { id = type.replace(/^(?:gallery|section):/, "").slice(0, 42) + "-" + sequence++; }
  while (page.blocks.some(block => block.id === id));
  return id;
}
function shift(from, to) {
  if (from === to) return;
  const movedId = page.blocks[from].id;
  commit(moveBlock(page, from, to), "Block reordered.");
  selectedId = movedId;
  renderOutline();
  renderInspector();
}
function addFromPalette(event) {
  const button = event.target.closest("[data-block-type]");
  if (!button) return;
  try {
    const block = createBlock(button.dataset.blockType, nextBlockId(button.dataset.blockType));
    const next = structuredClone(page);
    if (byId("builder-insert-after").checked && selectedId)
      next.blocks = insertBlockAfter(next, selectedId, block).blocks;
    else next.blocks.push(block);
    commit(next, getBlockDefinition(block.type).label + " added.");
    selectedId = block.id;
    redraw();
  } catch (error) {
    notify(error.message);
  }
}
palette.addEventListener("click", addFromPalette);
galleryPalette.addEventListener("click", addFromPalette);
sectionPalette.addEventListener("click", addFromPalette);
outline.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-action]");
  const item = event.target.closest("[data-index]");
  if (!button || !item) return;
  const index = Number(item.dataset.index);
  const action = button.dataset.action;
  if (action === "select") {
    selectedId = page.blocks[index].id;
    redraw();
    return;
  }
  if (action === "up" && index > 0) shift(index, index - 1);
  if (action === "down" && index < page.blocks.length - 1) shift(index, index + 1);
  if (action === "first" && index > 0) shift(index, 0);
  if (action === "last" && index < page.blocks.length - 1) shift(index, page.blocks.length - 1);
  if (action === "duplicate") {
    try {
      const clonedId = nextBlockId(page.blocks[index].type);
      commit(duplicateBlock(page, index, clonedId), "Section duplicated.");
      selectedId = clonedId;
      redraw();
    } catch (error) { notify(error.message); }
  }
  if (action === "remove") {
    const next = structuredClone(page);
    next.blocks.splice(index, 1);
    commit(next, "Block removed.");
  }
});
outline.addEventListener("dragstart", (event) => {
  const item = event.target.closest("[data-index]");
  if (!item) return;
  draggingIndex = Number(item.dataset.index);
  event.dataTransfer.effectAllowed = "move";
  event.dataTransfer.setData("text/plain", String(draggingIndex));
});
outline.addEventListener("dragover", (event) => {
  if (event.target.closest("[data-index]")) event.preventDefault();
});
outline.addEventListener("drop", (event) => {
  const item = event.target.closest("[data-index]");
  if (!item || draggingIndex === null) return;
  event.preventDefault();
  shift(draggingIndex, Number(item.dataset.index));
  draggingIndex = null;
});
outline.addEventListener("dragend", () => { draggingIndex = null; });

function stepBack() {
  if (!history.length) return;
  future.push(JSON.stringify(page));
  page = parseDocument(history.pop());
  if (!page.blocks.some(item => item.id === selectedId)) selectedId = page.blocks[0]?.id || null;
  redraw();
  notify("Change undone.");
}
function stepForward() {
  if (!future.length) return;
  history.push(JSON.stringify(page));
  page = parseDocument(future.pop());
  if (!page.blocks.some(item => item.id === selectedId)) selectedId = page.blocks[0]?.id || null;
  redraw();
  notify("Change restored.");
}
undo.addEventListener("click", stepBack);
redo.addEventListener("click", stepForward);
document.addEventListener("keydown", (event) => {
  if (!(event.ctrlKey || event.metaKey) || event.altKey) return;
  if (/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName || "")) return;
  if (event.key.toLowerCase() === "z") {
    event.preventDefault();
    if (event.shiftKey) stepForward();
    else stepBack();
  } else if (event.key.toLowerCase() === "y") {
    event.preventDefault();
    stepForward();
  }
});
title.addEventListener("input", () => {
  if (!titleEditing) { remember(); titleEditing = true; }
  page.title = title.value;
  renderPreview();
});
title.addEventListener("blur", () => { titleEditing = false; });
theme.addEventListener("change", () => {
  if (!THEMES.includes(theme.value) || theme.value === page.theme) return;
  const next = structuredClone(page);
  next.theme = theme.value;
  commit(next, "Theme updated to " + theme.value + ".");
});
viewport.addEventListener("change", () => {
  const value = ["desktop", "tablet", "mobile"].includes(viewport.value) ? viewport.value : "desktop";
  viewportFrame.className = "builder-viewport builder-viewport--" + value;
  notify("Preview: " + value + ".");
});
function download(filename, data, type) {
  const url = URL.createObjectURL(new Blob([data], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  // Keep the object URL alive while the browser finalizes its download.
  setTimeout(() => URL.revokeObjectURL(url), 30000);
}
byId("builder-export-html").addEventListener("click", () => {
  download("index.html", exportHtml(page), "text/html;charset=utf-8");
  notify("HTML downloaded. Add syntyr.all.css and referenced images, or use the complete static-site ZIP.");
});
byId("builder-export-zip").addEventListener("click", async () => {
  const button = byId("builder-export-zip");
  button.disabled = true;
  notify("Preparing static site files…");
  try {
    const cssResponse = await fetch(new URL("../dist/syntyr.all.css", import.meta.url),
      {credentials: "same-origin"});
    if (!cssResponse.ok) throw new Error("Syntyr stylesheet unavailable");
    const entries = [
      {name: "index.html", content: exportHtml(page)},
      {name: "syntyr.all.css", content: await cssResponse.text()}
    ];
    for (const name of requiredAssets(page)) {
      const url = new URL("../assets/" + name, import.meta.url);
      const response = await fetch(url, {credentials: "same-origin"});
      if (!response.ok) throw new Error("Missing approved local asset: " + name);
      entries.push({name: "assets/" + name, content: new Uint8Array(await response.arrayBuffer())});
    }
    const license = await fetch(new URL("../LICENSE", import.meta.url),
      {credentials: "same-origin"});
    if (!license.ok) throw new Error("MIT license file unavailable");
    entries.push({name: "LICENSE", content: await license.text()});
    entries.push({name: "README.txt", content: [
      "Syntyr static website export",
      "",
      "Upload index.html, syntyr.all.css, and any assets/ folder together.",
      "No JavaScript or build step is necessary for static layout and native details/links.",
      "Forms, checkout, authentication, search, filtering and live data need an application backend.",
      "Replace demo routes, fictional claims and examples with your own verified content.",
      "Save your syntyr-page.json project separately to continue editing.",
      "The original Syntyr CSS and HTML source is MIT-licensed.",
      "https://github.com/dporkka/syntyr-css/blob/main/LICENSE"
    ].join("\n") + "\n"});
    const archive = createStoredZip(entries);
    download("syntyr-static-site.zip", archive, "application/zip");
    notify("Static-site ZIP downloaded: HTML, CSS and " + requiredAssets(page).length + " local images; no JavaScript.");
  } catch (error) {
    notify("Static export failed: " + error.message);
  } finally {
    button.disabled = false;
  }
});
byId("builder-export-json").addEventListener("click", () => {
  download("syntyr-page.json", JSON.stringify(parseDocument(page), null, 2) + "\n", "application/json");
  notify("Editable JSON project downloaded.");
});
let importGeneration = 0;
byId("builder-import").addEventListener("change", async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  const generation = ++importGeneration;
  try {
    if (file.size > MAX_PROJECT_BYTES) throw new Error("Project file exceeds 16 MiB");
    const text = await file.text();
    if (generation !== importGeneration) return;
    let candidate;
    try { candidate = JSON.parse(text); }
    catch { throw new Error("Invalid project JSON"); }
    if (projectNeedsGalleryManifest(candidate)) {
      // Native projects import immediately even if the optional manifest
      // request has failed or stalled. Gallery imports wait only briefly.
      let timeout;
      try {
        await Promise.race([
          galleryLoadPromise,
          new Promise(resolve => { timeout = setTimeout(resolve, 4000); })
        ]);
      } finally {
        clearTimeout(timeout);
      }
      if (!galleryBlockTypes().length)
        throw new Error("Gallery definitions unavailable. Try again after the gallery loads.");
    }
    if (projectNeedsSectionManifest(candidate)) {
      let timeout;
      try {
        await Promise.race([
          sectionLoadPromise,
          new Promise(resolve => { timeout = setTimeout(resolve, 4000); })
        ]);
      } finally { clearTimeout(timeout); }
      if (!sectionBlockTypes().length)
        throw new Error("Section definitions unavailable. Try again after the library loads.");
    }
    // A previously selected gallery project may finish after a newer native
    // file has already been imported. Never let stale async work overwrite it.
    if (generation !== importGeneration) return;
    const imported = parseDocument(candidate);
    commit(imported, "Project opened.");
    sequence = Math.max(sequence, imported.blocks.length + 5);
  } catch (error) {
    if (generation === importGeneration)
      notify("Cannot open project: " + error.message);
  } finally {
    if (generation === importGeneration) event.target.value = "";
  }
});

renderPalette();
redraw();
const galleryLoadPromise = loadGallery();

const sectionLoadPromise = loadSections();
