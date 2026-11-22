/* Documentation-only progressive enhancement. Gallery previews require no JS. */
(() => {
  "use strict";
  const controls = document.getElementById("blocks-controls");
  const query = document.getElementById("blocks-search");
  const category = document.getElementById("blocks-category");
  const theme = document.getElementById("blocks-theme");
  const results = document.getElementById("blocks-results");
  const feedback = document.getElementById("blocks-feedback");
  const empty = document.getElementById("blocks-empty");
  const cards = Array.from(document.querySelectorAll("[data-block-id]"));
  if (!controls || !query || !category || !theme || !results || !feedback || !empty || !cards.length) return;

  const indexed = cards.map(card => ({
    card,
    words: (card.querySelector("h2")?.textContent || "") + " " + (card.dataset.blockKeywords || ""),
    category: card.dataset.blockCategory,
    preview: card.querySelector(".blocks-preview > .syn-root"),
    code: card.querySelector(".blocks-source code"),
    copy: card.querySelector("[data-block-copy]")
  }));
  for (const item of indexed) item.words = item.words.toLocaleLowerCase();

  // Without JS every preview remains open; progressive enhancement creates
  // a concise mobile gallery using native, keyboard-accessible disclosures.
  const compactViewport = window.matchMedia("(max-width: 40rem)");
  const previewToggle = document.getElementById("blocks-preview-toggle");
  const blockBatches = [...document.querySelectorAll(".blocks-batch")];
  let blockFiltering = false;
  let showAllPreviews = false;

  function visibleBlocks() {
    return indexed.filter(item => {
      if (item.card.hidden) return false;
      const batch = item.card.closest(".blocks-batch");
      return !batch?.hidden && (batch.tagName !== "DETAILS" || batch.open);
    }).length;
  }

  function updateBlockResults() {
    const visible = visibleBlocks();
    results.textContent = "Showing " + visible + " of " + indexed.length
      + " blocks." + (blockFiltering ? "" : " Open a batch to browse more.");
  }
  for (const batch of blockBatches) {
    if (batch.tagName === "DETAILS") {
      batch.addEventListener("toggle", () => {
        if (!blockFiltering) updateBlockResults();
      });
    }
  }

  function updatePreviewVisibility() {
    const featured = indexed.filter(item => !item.card.hidden).slice(0, 2);
    for (const item of indexed) {
      const disclosure = item.card.querySelector(".blocks-preview-disclosure");
      if (!disclosure) continue;
      disclosure.open = !compactViewport.matches || showAllPreviews || featured.includes(item);
    }
    if (previewToggle) {
      previewToggle.hidden = !compactViewport.matches;
      previewToggle.textContent = showAllPreviews ? "Collapse previews" : "Show all previews";
      previewToggle.setAttribute("aria-pressed", String(showAllPreviews));
    }
  }

  if (previewToggle) {
    previewToggle.addEventListener("click", () => {
      showAllPreviews = !showAllPreviews;
      updatePreviewVisibility();
    });
  }
  compactViewport.addEventListener("change", updatePreviewVisibility);
  for (const link of document.querySelectorAll("[data-block-category-link]")) {
    link.addEventListener("click", () => {
      query.value = "";
      category.value = link.dataset.blockCategoryLink;
      filter();
    });
  }

  function filter() {
    const terms = query.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    const selected = category.value;
    const wasFiltering = blockFiltering;
    blockFiltering = terms.length > 0 || selected !== "all";
    let matched = 0;
    for (const item of indexed) {
      const matches = (selected === "all" || item.category === selected)
        && terms.every(term => item.words.includes(term));
      item.card.hidden = !matches;
      if (matches) matched++;
    }
    // Search is optional enhancement: matching batches open automatically.
    // Clearing the search restores the 12-item native browsing overview.
    for (const batch of blockBatches) {
      const hasMatches = [...batch.querySelectorAll("[data-block-id]")].some(card => !card.hidden);
      batch.hidden = blockFiltering && !hasMatches;
      if (batch.tagName === "DETAILS") {
        if (blockFiltering && hasMatches) batch.open = true;
        else if (!blockFiltering && wasFiltering) batch.open = false;
      }
    }
    empty.hidden = matched !== 0;
    updatePreviewVisibility();
    updateBlockResults();
  }

  // Back/Forward can restore a native category link's fragment while the
  // previous filter hides its target. Reveal that card before scrolling.
  function restoreCategoryFromHash() {
    let id;
    try { id = decodeURIComponent(window.location.hash.slice(1)); }
    catch { return; }
    if (!id.startsWith("block-title-")) return;
    const target = document.getElementById(id);
    const card = target?.closest("[data-block-id]");
    if (!card) return;
    const batch = card.closest("details.blocks-batch");
    if (card.hidden || card.closest(".blocks-batch")?.hidden) {
      query.value = "";
      category.value = card.dataset.blockCategory;
      filter();
    }
    if (batch && !batch.open) batch.open = true;
    window.requestAnimationFrame(() => target.scrollIntoView({block: "start"}));
  }
  window.addEventListener("hashchange", restoreCategoryFromHash);

  function changeTheme() {
    for (const item of indexed) {
      if (item.preview) item.preview.setAttribute("data-syn-theme", theme.value);
    }
  }

  controls.hidden = false;
  query.addEventListener("input", filter);
  category.addEventListener("change", filter);
  theme.addEventListener("change", changeTheme);
  filter();
  if (window.location.hash.startsWith("#block-title-")) restoreCategoryFromHash();

  const iconControls = document.getElementById("blocks-icon-controls");
  const iconQuery = document.getElementById("blocks-icon-search");
  const iconResults = document.getElementById("blocks-icon-results");
  const icons = Array.from(document.querySelectorAll("[data-icon-id]"));
  if (iconControls && iconQuery && iconResults && icons.length) {
    const iconBatches = [...document.querySelectorAll(".blocks-icons-batch")];
    let iconFiltering = false;

    function updateIconResults() {
      const shown = icons.filter(icon => {
        const batch = icon.closest(".blocks-icons-batch");
        return !icon.hidden && !batch?.hidden && (batch.tagName !== "DETAILS" || batch.open);
      }).length;
      iconResults.textContent = "Showing " + shown + " of " + icons.length
        + " icons." + (iconFiltering ? "" : " Open a batch to browse more.");
    }
    function filterIcons() {
      const terms = iconQuery.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
      const wasFiltering = iconFiltering;
      iconFiltering = terms.length > 0;
      for (const icon of icons) {
        const words = ((icon.dataset.iconId || "") + " " +
          (icon.querySelector("strong")?.textContent || "")).toLocaleLowerCase();
        icon.hidden = !terms.every(term => words.includes(term));
      }
      for (const batch of iconBatches) {
        const hasMatches = [...batch.querySelectorAll("[data-icon-id]")].some(icon => !icon.hidden);
        batch.hidden = iconFiltering && !hasMatches;
        if (batch.tagName === "DETAILS") {
          if (iconFiltering && hasMatches) batch.open = true;
          else if (!iconFiltering && wasFiltering) batch.open = false;
        }
      }
      updateIconResults();
    }
    for (const batch of iconBatches) {
      if (batch.tagName === "DETAILS") {
        batch.addEventListener("toggle", () => {
          if (!iconFiltering) updateIconResults();
        });
      }
    }
    iconControls.hidden = false;
    iconQuery.addEventListener("input", filterIcons);
    filterIcons();
  }

  for (const item of indexed) {
    if (!item.copy || !item.code) continue;
    const edit = document.createElement("a");
    edit.className = "syn-button blocks-edit";
    edit.href = `playground.html#component=${encodeURIComponent("block-" + item.card.dataset.blockId)}`;
    edit.textContent = "Edit in playground";
    item.copy.insertAdjacentElement("afterend", edit);
    item.copy.hidden = false;
    item.copy.addEventListener("click", async () => {
      const value = item.code.textContent.trim();
      try {
        if (!navigator.clipboard?.writeText) throw new Error("Clipboard unavailable");
        await navigator.clipboard.writeText(value);
        feedback.textContent = item.card.querySelector("h2").textContent + " HTML copied.";
      } catch {
        const details = item.code.closest("details");
        if (details) details.open = true;
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(item.code);
        selection?.removeAllRanges();
        selection?.addRange(range);
        feedback.textContent = "Source selected. Press Ctrl+C or Cmd+C to copy.";
      }
    });
  }
})();
