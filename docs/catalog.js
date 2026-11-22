/* Optional documentation-only enhancement. Syntyr CSS requires no JavaScript. */
(() => {
  'use strict';
  const search = document.getElementById('catalog-search');
  const category = document.getElementById('catalog-category');
  const controls = document.getElementById('catalog-controls');
  const results = document.getElementById('catalog-results');
  const feedback = document.getElementById("catalog-feedback");
  const empty = document.getElementById('catalog-empty');
  const cards = [...document.querySelectorAll('.catalog-card')];
  if (!search || !category || !controls || !results || !feedback || !empty || !cards.length) return;

  const searchable = cards.map((card) => ({
    card,
    terms: `${card.querySelector('h2')?.textContent || ''} ${card.dataset.catalogKeywords || ''} ${card.querySelector('.syn-muted')?.textContent || ''}`.toLocaleLowerCase(),
  }));

  // Keep the index functional without JS: markup and links are present in HTML.
  // JavaScript only adds scroll-aware highlighting and filter-aware navigation.
  const indexLinks = [...document.querySelectorAll('#catalog-index .catalog-index-link, .catalog-mobile-index .catalog-mobile-index-link')];
  const linksById = new Map();
  for (const link of indexLinks) {
    const id = link.getAttribute('href').slice(1);
    if (!linksById.has(id)) linksById.set(id, []);
    linksById.get(id).push(link);
  }
  const indexedCards = cards.map((card) => ({
    card,
    links: linksById.get(card.getAttribute('aria-labelledby')) || [],
  })).filter(({links}) => links.length);

  function updateActiveIndex() {
    const viewportTop = window.innerHeight * 0.08;
    const viewportBottom = window.innerHeight * 0.85;
    const intersecting = [];
    for (const {card, links} of indexedCards) {
      const bounds = card.getBoundingClientRect();
      const inView = !card.hidden && bounds.top < viewportBottom && bounds.bottom > viewportTop;
      for (const link of links) {
        link.classList.toggle('is-in-view', inView);
        link.removeAttribute('aria-current');
      }
      if (inView) intersecting.push({links, top: bounds.top});
    }
    // Only the visible navigation receives aria-current; hidden landmarks stay silent.
    intersecting.sort((a, b) => a.top - b.top);
    const current = intersecting[0]?.links.find(link => link.getClientRects().length);
    current?.setAttribute('aria-current', 'location');
  }

  let indexUpdateQueued = false;
  function scheduleIndexUpdate() {
    if (indexUpdateQueued) return;
    indexUpdateQueued = true;
    window.requestAnimationFrame(() => {
      indexUpdateQueued = false;
      updateActiveIndex();
    });
  }
  window.addEventListener('scroll', scheduleIndexUpdate, {passive: true});
  window.addEventListener('resize', scheduleIndexUpdate);
  window.addEventListener('hashchange', scheduleIndexUpdate);
  for (const {card, links} of indexedCards) {
    for (const link of links) {
      link.addEventListener('click', () => {
        // Selecting a component outside the active filter must still reach it.
        if (!card.hidden) return;
        search.value = '';
        category.value = 'all';
        updateResults();
      });
    }
  }

  function updateResults() {
    const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    let count = 0;
    for (const {card, terms: text} of searchable) {
      const match = (category.value === 'all' || card.dataset.catalogCategory === category.value)
        && terms.every((term) => text.includes(term));
      card.hidden = !match;
      if (match) count += 1;
    }
    empty.hidden = count !== 0;
    results.textContent = `Showing ${count} of ${cards.length} examples.`;
    scheduleIndexUpdate();
  }

  const theme = document.getElementById('catalog-theme');
  const previewSize = document.getElementById('catalog-preview-size');
  const grid = document.getElementById('catalog-items');
  const root = document.querySelector('.syn-root');
  if (theme && root) {
    theme.addEventListener("change", () => {
      root.dataset.synTheme = theme.value;
    });
  }
  if (previewSize && grid) {
    previewSize.addEventListener("change", () => {
      grid.setAttribute('data-catalog-preview', previewSize.value);
    });
  }
  controls.hidden = false;
  search.addEventListener("input", updateResults);
  category.addEventListener("change", updateResults);
  updateResults();

  for (const card of cards) {
    const button = card.querySelector('[data-catalog-copy]');
    const code = card.querySelector('.catalog-source code');
    if (!button || !code) continue;
    button.hidden = false;
    button.addEventListener('click', async () => {
      const value = code.textContent.trim();
      try {
        if (!navigator.clipboard?.writeText) throw new Error('Clipboard API unavailable');
        await navigator.clipboard.writeText(value);
        feedback.textContent = `${card.querySelector('h2').textContent} HTML copied.`;
      } catch {
        code.closest('details').open = true;
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(code);
        selection?.removeAllRanges();
        selection?.addRange(range);
        feedback.textContent = 'HTML selected. Use your keyboard to copy it.';
      }
    });
  }
})();
