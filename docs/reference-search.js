/* Docs-only progressive enhancement; no fetch, dependencies or consumer JS. */
(() => {
  "use strict";
  const controls = document.getElementById("docs-search-controls");
  const input = document.getElementById("docs-search-input");
  const status = document.getElementById("docs-search-results");
  const groups = Array.from(document.querySelectorAll(".docs-reference-group"), group => ({
    group,
    entries: Array.from(group.querySelectorAll("li[data-doc-search]"), item => ({
      item,
      text: [group.querySelector("h2").textContent, item.textContent, item.dataset.docSearch]
        .join(" ").normalize("NFKC").toLowerCase(),
    })),
  }));
  const total = groups.reduce((sum, group) => sum + group.entries.length, 0);
  if (!controls || !input || !status || !total) return;

  function update() {
    const words = input.value.normalize("NFKC").toLowerCase().trim().split(/\s+/).filter(Boolean);
    let count = 0;
    for (const { group, entries } of groups) {
      let matches = 0;
      for (const { item, text } of entries) {
        const match = words.every(word => text.includes(word));
        item.hidden = !match;
        if (match) matches += 1;
      }
      group.hidden = matches === 0;
      count += matches;
    }
    status.textContent = count === 0
      ? "No matching guides. Clear the search or try fewer words."
      : `Showing ${count} of ${total} guides.`;
  }

  input.addEventListener("input", event => { if (!event.isComposing) update(); });
  input.addEventListener("compositionend", update);
  input.addEventListener("search", update);
  update();
  controls.hidden = false;
})();
