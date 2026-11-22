/* Optional documentation-only enhancement. Syntyr CSS requires no JavaScript. */
(() => {
  'use strict';
  const search = document.getElementById('catalog-search');
  const category = document.getElementById('catalog-category');
  const browserFilter = document.getElementById('catalog-browser-filter');
  const moduleFilter = document.getElementById('catalog-module-filter');
  const useCaseFilter = document.getElementById('catalog-use-case-filter');
  const controls = document.getElementById('catalog-controls');
  const results = document.getElementById('catalog-results');
  const feedback = document.getElementById("catalog-feedback");
  const empty = document.getElementById('catalog-empty');
  const cards = [...document.querySelectorAll('.catalog-card')];
  if (!search || !category || !controls || !results || !feedback || !empty || !cards.length) return;

  const searchable = cards.map((card) => {
    // The catalog badge is the authored stylesheet contract; match that same
    // contract in the published gallery manifest, not guesses from class names.
    const requiredModules = new Set(
      (card.querySelector('.catalog-card-top .syn-badge')?.textContent || '')
        .split(' + ').map(name => name.trim()).filter(Boolean)
    );
    const useCases = new Set((card.dataset.catalogUseCases || '').split(/\s+/).filter(Boolean));
    return {
      card,
      requiredModules,
      useCases,
      // Detect actual example markup; docs panels/compatibility notes do not count.
      hasAdditionalNativeApi: !!card.querySelector('.catalog-preview [popover], .catalog-preview [popovertarget], .catalog-preview [commandfor], .catalog-preview details[name]'),
      terms: `${card.querySelector('h2')?.textContent || ''} ${card.dataset.catalogKeywords || ''} ${card.querySelector('.syn-muted')?.textContent || ''}`.toLocaleLowerCase(),
    };
  });

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
        if (browserFilter) browserFilter.value = 'all';
        if (moduleFilter) moduleFilter.value = 'all';
        if (useCaseFilter) useCaseFilter.value = 'all';
        updateResults();
      });
    }
  }

  function updateResults() {
    const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    let count = 0;
    const feature = browserFilter?.value || 'all';
    const module = moduleFilter?.value || 'all';
    const useCase = useCaseFilter?.value || 'all';
    for (const {card, terms: text, hasAdditionalNativeApi, requiredModules, useCases} of searchable) {
      const matchesModule = module === 'all'
        || (module === 'core-only'
          ? requiredModules.size === 1 && requiredModules.has('syntyr.core.css')
          : requiredModules.has(module));
      const match = (category.value === 'all' || card.dataset.catalogCategory === category.value)
        && matchesModule
        && (useCase === 'all' || useCases.has(useCase))
        && (feature === 'all' || (feature === 'native-advanced' ? hasAdditionalNativeApi : !hasAdditionalNativeApi))
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
  browserFilter?.addEventListener("change", updateResults);
  moduleFilter?.addEventListener("change", updateResults);
  useCaseFilter?.addEventListener("change", updateResults);
  updateResults();

  // Docs-only: create an actual, version-local HTML document rather than
  // implying that a partial component snippet includes its CSS dependencies.
  const knownStylesheets = new Set([
    'syntyr.core.css', 'syntyr.recipes.css', 'syntyr.geometry.css',
    'syntyr.viz.css', 'syntyr.semantic.css', 'syntyr.utilities.css',
  ]);
  function standalonePage(card, markup) {
    const badge = card.querySelector('.catalog-card-top .syn-badge');
    const modules = (badge?.textContent || '').split(' + ').map(s => s.trim()).filter(Boolean);
    const required = new Set(['syntyr.core.css']);
    for (const name of modules) {
      if (!knownStylesheets.has(name)) throw new Error('Unknown catalog stylesheet');
      required.add(name);
    }
    const links = [...required].map(name => `<link rel="stylesheet" href="/dist/${name}">`).join('\n');
    const heading = card.querySelector('h2')?.textContent || 'Syntyr example';
    const title = heading.replace(/[&<>"']/g, ch => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[ch]));
    return `<!doctype html>\n<html lang="en">\n<head>\n  <meta charset="utf-8">\n  <meta name="viewport" content="width=device-width,initial-scale=1">\n  <title>${title} — Syntyr CSS</title>\n  <!-- Self-host matching unreleased alpha.5 CSS under /dist/ or adjust these paths. -->\n  ${links}\n</head>\n<body class="syn-root" data-syn-theme="studio">\n${markup}\n</body>\n</html>`;
  }

  for (const card of cards) {
    const button = card.querySelector('[data-catalog-copy]');
    const pageButton = card.querySelector('[data-catalog-copy-page]');
    const code = card.querySelector('.catalog-source code');
    if (!button || !pageButton || !code) continue;
    button.hidden = false;
    pageButton.hidden = false;
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
    pageButton.addEventListener('click', async () => {
      const value = standalonePage(card, code.textContent.trim());
      try {
        if (!navigator.clipboard?.writeText) throw new Error('Clipboard API unavailable');
        await navigator.clipboard.writeText(value);
        feedback.textContent = `${card.querySelector('h2').textContent} full HTML page copied. Check asset paths and app endpoints.`;
      } catch {
        // Keep the entire generated page visible and keyboard selectable,
        // even in local file:// previews where clipboard permissions fail.
        let details = card.querySelector('[data-catalog-page-fallback]');
        if (!details) {
          details = document.createElement('details');
          details.className = 'catalog-page-fallback';
          details.dataset.catalogPageFallback = '';
          const summary = document.createElement('summary');
          summary.textContent = 'Standalone HTML (select to copy)';
          const pre = document.createElement('pre');
          pre.className = 'catalog-source';
          const fallbackCode = document.createElement('code');
          pre.append(fallbackCode);
          details.append(summary, pre);
          card.append(details);
        }
        const fallbackCode = details.querySelector('code');
        fallbackCode.textContent = value;
        details.open = true;
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(fallbackCode);
        selection?.removeAllRanges();
        selection?.addRange(range);
        feedback.textContent = 'Complete page selected. Use your keyboard to copy it.';
      }
    });
  }
})();
