/* Search is an optional enhancement: every guide stays readable without JavaScript. */
(() => {
  "use strict";
  const controls = document.getElementById("howto-controls");
  const search = document.getElementById("howto-search");
  const results = document.getElementById("howto-results");
  const empty = document.getElementById("howto-empty");
  const cards = [...document.querySelectorAll(".howto-card")];
  if (!controls || !search || !results || !empty || !cards.length) return;

  const entries = cards.map(card => ({
    card,
    terms: `${card.dataset.howtoKeywords || ""} ${card.textContent || ""}`.toLocaleLowerCase()
  }));
  function updateResults() {
    const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    let count = 0;
    for (const { card, terms: indexed } of entries) {
      const match = terms.every(term => indexed.includes(term));
      card.hidden = !match;
      if (match) count += 1;
    }
    empty.hidden = count !== 0;
    results.textContent = `Showing ${count} of ${cards.length} How-To guides.`;
  }

  controls.hidden = false;
  search.addEventListener("input", updateResults);
  updateResults();
})();
