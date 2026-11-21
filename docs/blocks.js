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

  function filter() {
    const terms = query.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    const selected = category.value;
    let visible = 0;
    for (const item of indexed) {
      const matches = (selected === "all" || item.category === selected) && terms.every(term => item.words.includes(term));
      item.card.hidden = !matches;
      if (matches) visible += 1;
    }
    empty.hidden = visible !== 0;
    results.textContent = "Showing " + visible + " of " + indexed.length + " blocks.";
  }

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

  const iconControls = document.getElementById("blocks-icon-controls");
  const iconQuery = document.getElementById("blocks-icon-search");
  const iconResults = document.getElementById("blocks-icon-results");
  const icons = Array.from(document.querySelectorAll("[data-icon-id]"));
  if (iconControls && iconQuery && iconResults && icons.length) {
    function filterIcons() {
      const terms = iconQuery.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
      let visible = 0;
      for (const icon of icons) {
        const words = ((icon.dataset.iconId || "") + " " +
          (icon.querySelector("strong")?.textContent || "")).toLocaleLowerCase();
        const matches = terms.every(term => words.includes(term));
        icon.hidden = !matches;
        if (matches) visible++;
      }
      iconResults.textContent = "Showing " + visible + " of " + icons.length + " icons.";
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
