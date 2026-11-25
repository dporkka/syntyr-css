/* Documentation-only live reference; the distributed Syntyr CSS has no runtime JavaScript. */
(() => {
  "use strict";
  const examples = {
    metrics: `<section class="syn-region">
  <h2 class="syn-heading">System telemetry</h2>
  <div class="syn-stats">
    <article class="syn-stat"><span class="syn-stat-label">USERS</span><p class="syn-stat-value">2,840</p></article>
    <article class="syn-stat"><span class="syn-stat-label">UPTIME</span><p class="syn-stat-value">99.9%</p></article>
    <article class="syn-stat"><span class="syn-stat-label">ALERTS</span><p class="syn-stat-value">02</p></article>
  </div>
</section>`,
    actions: `<section class="syn-panel">
  <h2 class="syn-heading">Deployment ready</h2>
  <p class="syn-muted">Scoped tokens customize this panel without a new component class.</p>
  <div class="syn-inline syn-u-wrap">
    <button class="syn-button syn-button--primary" type="button">Deploy</button>
    <button class="syn-button syn-button--outline" type="button">Preview</button>
    <button class="syn-button syn-button--ghost" type="button">Cancel</button>
  </div>
</section>`,
    form: `<form class="syn-panel syn-form" action="#" method="get">
  <h2 class="syn-heading">Create workspace</h2>
  <label class="syn-label" for="workspace-name">WORKSPACE NAME</label>
  <input id="workspace-name" class="syn-input syn-u-w-full" name="workspace" required placeholder="Example Studio">
  <label class="syn-check"><input type="checkbox" required> I accept the terms</label>
  <button class="syn-button syn-button--primary" type="submit">Create</button>
  <p class="syn-muted">Preview only; forms cannot submit in this frame.</p>
</form>`,
    cards: `<section class="syn-grid">
  <article class="syn-panel">
    <span class="syn-badge">ANALYTICS</span>
    <h2 class="syn-heading">Discover patterns</h2>
    <p class="syn-muted">Readable content and restrained color.</p>
    <a class="syn-button syn-button--primary" href="#details">Explore</a>
  </article>
  <article class="syn-panel">
    <span class="syn-badge">WORKFLOWS</span>
    <h2 class="syn-heading">Move faster</h2>
    <p class="syn-muted">Reusable visual language in ordinary HTML.</p>
    <a class="syn-button" href="#details">Learn more</a>
  </article>
</section>`
  };
  const byId = id => document.getElementById(id);
  const example = byId("playground-example");
  const theme = byId("playground-theme");
  const markup = byId("playground-markup");
  const preview = byId("playground-preview");
  const viewport = byId("playground-viewport");
  const radius = byId("playground-panel-radius");
  const padding = byId("playground-panel-padding");
  const search = byId("playground-search");
  const status = byId("playground-status");
  const renderButton = byId("playground-render");
  const copyButton = byId("playground-copy");
  const copyFallback = byId("playground-copy-fallback");
  const catalog = Array.isArray(window.SYNTYR_PLAYGROUND_CATALOG)
    ? window.SYNTYR_PLAYGROUND_CATALOG : [];
  const catalogMap = new Map(catalog.map(item => [item.id, item]));
  const snippet = window.SYNTYR_PLAYGROUND_SNIPPET;
  const starterModules = {
    metrics: "syntyr.core.css",
    actions: "syntyr.core.css + syntyr.utilities.css",
    form: "syntyr.core.css + syntyr.utilities.css",
    cards: "syntyr.core.css",
    "starter-custom": "syntyr.core.css"
  };
  function selectedModule() {
    return catalogMap.get(example.value)?.module ||
      starterModules[example.value] || "syntyr.core.css";
  }
  const starterGuide = {
    metrics: "Responsive statistics using a named container and semantic values.",
    actions: "A native button toolbar; connect actions in your application.",
    form: "Native labeled fields; validation and submission belong to your application.",
    cards: "Semantic marketing cards using a responsive CSS grid."
  };
  let importedStarter = null;
    let framePending = false;
  if (!example || !theme || !markup || !preview || !viewport || !radius || !padding || !snippet) return;

  function numericValue(control, minimum, maximum) {
    return Math.min(maximum, Math.max(minimum, Number(control.value) || minimum));
  }

  function tokens() {
    const corner = numericValue(radius, 0, 32);
    const inset = numericValue(padding, 8, 48);
    byId("playground-panel-radius-value").textContent = `${corner}px`;
    byId("playground-panel-padding-value").textContent = `${inset}px`;
    return `--syn-panel-radius: ${corner}px; --syn-panel-padding: ${inset}px;`;
  }

  function themedMarkup() {
    // The 20 canonical free blocks have their own Studio root. The playground
    // theme controls the rendered/exported composition, but never rewrites the
    // editable source or the generated MIT gallery snippets.
    if (catalogMap.get(example.value)?.kind !== "block") return markup.value;
    return markup.value.replace(/<[a-z][a-z0-9-]*\b[^>]*>/gi, (tag) => {
      // Recognize equivalent quoted attribute syntax from edited HTML.
      const classAttribute = /(?:^|\s)class\s*=\s*(["'])(.*?)\1/i.exec(tag);
      if (!classAttribute || !/(?:^|\s)syn-root(?:\s|$)/.test(classAttribute[2])) return tag;
      return tag.replace(/(\s)data-syn-theme\s*=\s*(["'])(.*?)\2/gi,
        (_, whitespace, quote) => whitespace + "data-syn-theme=" + quote + theme.value + quote);
    });
  }

  function configuredHTML() {
    return snippet.configuredSnippet({
      theme: theme.value,
      tokens: tokens(),
      module: selectedModule(),
      markup: themedMarkup()
    });
  }

  function updateViewport() {
    preview.style.width = viewport.value === "fluid" ? "100%" : `${Number(viewport.value)}px`;
    preview.dataset.viewport = viewport.value;
  }

  function previewSafeMarkup() {
    // Preview-only: keep original destinations in editable/copied HTML, but
    // never allow illustrative links to navigate the sandboxed iframe.
    // Parse a detached document instead of rewriting HTML attribute strings.
    const detached = new DOMParser().parseFromString(themedMarkup(), "text/html");
    for (const link of detached.querySelectorAll("a[href], area[href]")) {
      link.removeAttribute("href");
    }
    return detached.body.innerHTML;
  }

  function render() {
    // No script or form permissions, even if an editor pastes arbitrary markup.
    // allow-same-origin permits the local stylesheet but not script execution.
    // An about:srcdoc document has origin-specific CSS semantics in Firefox.
    const localStyleOrigin = /^https?:$/.test(location.protocol) ? location.origin : "'self'";
    const shell = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self' 'unsafe-inline' ${localStyleOrigin}; img-src data: ${localStyleOrigin}; base-uri 'none'; form-action 'none'">
${snippet.previewStylesheets(selectedModule())}
<style>html,body{min-height:100%;} body.syn-root{margin:0;padding:1.5rem;} *,*::before,*::after{box-sizing:border-box;}</style>
</head><body class="syn-root syn-page" data-syn-theme="${theme.value}" style="${tokens()}">${previewSafeMarkup()}</body></html>`;
    preview.srcdoc = shell;
    status.textContent = `Preview updated: ${theme.options[theme.selectedIndex].text} theme.`;
  }

  function scheduleRender() {
    copyFallback.hidden = true;
    if (framePending) return;
    framePending = true;
    requestAnimationFrame(() => { framePending = false; render(); });
  }

  function populateCatalog() {
    const selected = example.value;
    example.querySelectorAll("[data-playground-catalog]").forEach(group => group.remove());
    const groups = new Map();
    for (const title of ["Component catalog", "Site & application blocks"]) {
      const group = document.createElement("optgroup");
      group.label = title;
      group.dataset.playgroundCatalog = "";
      groups.set(title, group);
    }
    const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    let matching = 0;
    for (const item of catalog) {
      const haystack = [item.title, item.description, item.keywords, item.module, item.html].join(" ").toLocaleLowerCase();
      const matches = terms.every(term => haystack.includes(term));
      if (matches) matching += 1;
      // Keep the selected example available even when filtered, so edits are not lost.
      if (!matches && selected !== item.id) continue;
      const option = document.createElement("option");
      option.value = item.id;
      option.textContent = item.title;
      groups.get(item.kind === "block" ? "Site & application blocks" : "Component catalog").append(option);
    }
    for (const group of groups.values()) if (group.children.length) example.append(group);
    if ([...example.options].some(option => option.value === selected)) example.value = selected;
    byId("playground-search-status").textContent =
      `${matching} of ${catalog.length} examples match. Pick one from Example above.`;
  }

  function loadExample() {
    const item = catalogMap.get(example.value);
    markup.value = item ? item.html : (
      example.value === "starter-custom" && importedStarter
        ? importedStarter.fragment : (examples[example.value] || examples.metrics));
    markup.dispatchEvent(new Event("syntyr:load-example"));
    byId("playground-reference-title").textContent = item ? item.title : "Starter example";
    byId("playground-reference-module").textContent = selectedModule();
    byId("playground-required-stylesheets").textContent = snippet.requiredStylesheets(
      selectedModule()
    ).join(" + ");
    byId("playground-reference-description").textContent = item ? item.description :
      (example.value === "starter-custom" && importedStarter
        ? "Imported from Syntyr's starter wizard. This preview uses the current CSS candidate; export against pinned alpha.4 before shipping."
        : starterGuide[example.value]);
    byId("playground-reference-guidance").textContent = item ? item.guidance :
      "The documentation examples are illustrative. Implement real application actions yourself.";
    const source = byId("playground-source-link");
    source.href = item?.kind === "block" ? `blocks.html#block-title-${item.id.slice(6)}` :
      item ? `catalog.html#${item.id}` : "catalog.html";
    source.textContent = item?.kind === "block" ? "View original block" : "View original component";
    scheduleRender();
  }

  example.addEventListener("change", loadExample);
  theme.addEventListener("change", scheduleRender);
  markup.addEventListener("input", scheduleRender);
  for (const control of [radius, padding]) control.addEventListener("input", scheduleRender);
  viewport.addEventListener("change", updateViewport);
  search.addEventListener("input", populateCatalog);
  renderButton.addEventListener("click", render);
  copyButton.addEventListener("click", async () => {
    try {
      if (!navigator.clipboard?.writeText) throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText(configuredHTML());
      copyFallback.hidden = true;
      status.textContent = "Configured HTML copied.";
    } catch {
      // Keep CodeMirror (or the native editor) intact: manual copy must include
      // the complete configured wrapper, not only the editable inner HTML.
      copyFallback.value = configuredHTML();
      copyFallback.hidden = false;
      copyFallback.focus();
      copyFallback.select();
      status.textContent = "Configured HTML selected. Copy it with your keyboard.";
    }
  });
  populateCatalog();
  const requested = new URLSearchParams(location.hash.slice(1)).get("component");
  if (requested && catalogMap.has(requested)) example.value = requested;
  updateViewport();
  loadExample();
  // The starter wizard passes only public allowlisted selections, not an HTML
  // payload. Recreate its fragment using the one canonical generator module.
  const handoff = new URLSearchParams(location.hash.slice(1));
  if (handoff.has("starter")) {
    import("./starter-wizard.mjs").then(({ createStarter }) => {
      const starter = createStarter({
        kind: handoff.get("starter"),
        theme: handoff.get("theme"),
        stack: handoff.get("stack")
      });
      importedStarter = starter;
      const option = document.createElement("option");
      option.value = "starter-custom";
      option.textContent = "Starter wizard / generated project";
      example.append(option);
      example.value = option.value;
      theme.value = handoff.get("theme");
      loadExample();
      status.textContent = "Starter imported from the wizard. Edit it here, then export your HTML.";
    }).catch(() => {
      status.textContent = "Starter handoff was invalid. Choose a catalog example instead.";
    });
  }
})();

/* Geometry mixer is docs-only; application styles remain zero-JavaScript. */
(() => {
  "use strict";
  const byId = id => document.getElementById(id);
  const shape = byId("geometry-shape");
  const stroke = byId("geometry-stroke");
  const paint = byId("geometry-border-paint");
  const inlay = byId("geometry-inlay");
  const theme = byId("playground-theme");
  const frame = byId("geometry-preview");
  const stage = byId("geometry-preview-theme");
  const output = byId("geometry-code");
  const status = byId("geometry-status");
  const cornerIds = ["tl", "tr", "br", "bl"];
  const corners = cornerIds.map(corner => byId(`geometry-cut-${corner}`));
  const allowedShapes = new Set(["bevel", "notch", "step", "facet"]);
  const borderPaints = {
    outline: null,
    accent: "var(--syn-accent)",
    gradient: "linear-gradient(120deg, var(--syn-accent), var(--syn-frame-strong))"
  };
  const wash = "linear-gradient(145deg, color-mix(in srgb, var(--syn-accent) 9%, transparent), transparent 70%)";

  function updateGeometry() {
    const profile = allowedShapes.has(shape.value) ? shape.value : "bevel";
    const width = Math.max(1, Math.min(6, Number(stroke.value) || 1));
    frame.className = `syn-panel syn-frame syn-frame--${profile}`;
    stage.dataset.synTheme = theme.value;
    const declarations = [];
    corners.forEach((control, index) => {
      const corner = cornerIds[index];
      const pixels = Math.max(0, Math.min(48, Number(control.value) || 0));
      const value = `${pixels}px`;
      byId(`geometry-cut-${corner}-value`).textContent = value;
      frame.style.setProperty(`--syn-frame-cut-${corner}`, value);
      declarations.push(`--syn-frame-cut-${corner}: ${value};`);
    });
    byId("geometry-stroke-value").textContent = `${width}px`;
    frame.style.setProperty("--syn-frame-stroke", `${width}px`);
    declarations.push(`--syn-frame-stroke: ${width}px;`);
    const selectedPaint = Object.hasOwn(borderPaints, paint.value) ? borderPaints[paint.value] : null;
    if (selectedPaint) {
      frame.style.setProperty("--syn-frame-border-paint", selectedPaint);
      declarations.push(`--syn-frame-border-paint: ${selectedPaint};`);
    } else {
      frame.style.removeProperty("--syn-frame-border-paint");
    }
    if (inlay.checked) {
      frame.style.setProperty("--syn-frame-inlay-paint", wash);
      declarations.push(`--syn-frame-inlay-paint: ${wash};`);
    } else {
      frame.style.removeProperty("--syn-frame-inlay-paint");
    }
    output.value = `<!-- Load syntyr.core.css and syntyr.geometry.css -->\n<section class="syn-root" data-syn-theme="${stage.dataset.synTheme}">\n  <article class="syn-panel syn-frame syn-frame--${profile}"\n    style="${declarations.join(" ")}">\n    <h2>Signal interface</h2>\n    <p>Semantic content with optional framing.</p>\n  </article>\n</section>`;
    status.textContent = "Geometry preview updated.";
  }

  for (const control of [shape, stroke, paint, inlay, theme, ...corners]) {
    control.addEventListener("input", updateGeometry);
    control.addEventListener("change", updateGeometry);
  }
  byId("geometry-copy").addEventListener("click", async () => {
    try {
      if (!navigator.clipboard?.writeText) throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText(output.value);
      status.textContent = "HTML copied.";
    } catch (_error) {
      output.focus();
      output.select();
      status.textContent = "HTML selected. Copy with your keyboard.";
    }
  });
  updateGeometry();
})();


// Documentation-only: actual browser text bounds (never shipped in CSS bundles).
(() => {
  "use strict";
  const byId = id => document.getElementById(id);
  const text = byId("type-lab-text");
  const width = byId("type-lab-width");
  const style = byId("type-lab-style");
  const wrap = byId("type-lab-wrap");
  const preview = byId("type-lab-preview");
  const report = byId("type-lab-report");
  const stage = byId("type-lab-stage");
  const themes = byId("playground-theme");
  const classes = {title: "syn-title", heading: "syn-heading", body: "syn-body"};
  const wraps = {safe: "syn-u-text-safe", balance: "syn-u-text-balance", pretty: "syn-u-text-pretty"};
  let pending = false;

  function measure() {
    pending = false;
    const range = document.createRange();
    range.selectNodeContents(preview);
    // Font fallback can produce multiple fragment tops on the same visual line.
    const bands = [];
    const fragments = Array.from(range.getClientRects(), rect => ({
      center: (rect.top + rect.bottom) / 2, height: rect.bottom - rect.top
    })).filter(rect => rect.height > 0).sort((a, b) => a.center - b.center);
    for (const fragment of fragments) {
      const band = bands[bands.length - 1];
      if (!band || fragment.center - band.center >= Math.min(fragment.height, band.height) / 2)
        bands.push(fragment);
    }
    const lineCount = preview.textContent ? bands.length : 0;
    const actualWidth = Math.round(preview.getBoundingClientRect().width);
    const actualHeight = Math.round(preview.getBoundingClientRect().height);
    const overflow = preview.scrollWidth > preview.clientWidth + 1 ||
      preview.scrollHeight > preview.clientHeight + 1;
    report.textContent = `${lineCount} visual line${lineCount === 1 ? "" : "s"} · ${actualWidth}px content box · ${actualHeight}px element height · ${overflow ? "Overflow detected" : "No element overflow detected"}.`;
  }

  function update() {
    const desired = Math.max(160, Math.min(640, Number(width.value) || 320));
    byId("type-lab-width-value").textContent = `${desired}px`;
    preview.style.setProperty("--lab-width", `${desired}px`);
    preview.className = `${classes[style.value] || classes.heading} ${wraps[wrap.value] || wraps.safe}`;
    preview.textContent = text.value;
    stage.dataset.synTheme = themes.value;
    report.textContent = "Measuring browser text…";
    if (!pending) {
      pending = true;
      requestAnimationFrame(measure);
    }
  }

  for (const control of [text, width, style, wrap, themes]) {
    control.addEventListener("input", update);
    control.addEventListener("change", update);
  }
  // Width can change independently of the slider (zoom, responsive layout).
  if (typeof ResizeObserver === "function") new ResizeObserver(() => {
    if (!pending) { pending = true; requestAnimationFrame(measure); }
  }).observe(stage);
  document.fonts?.ready.then(() => requestAnimationFrame(measure));
  update();
})();
