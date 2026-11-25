/* Optional documentation-only enhancement. Syntyr CSS requires no JavaScript. */
(() => {
  'use strict';
  const search = document.getElementById('catalog-search');
  const category = document.getElementById('catalog-category');
  const browserFilter = document.getElementById('catalog-browser-filter');
  const moduleFilter = document.getElementById('catalog-module-filter');
  const useCaseFilter = document.getElementById('catalog-use-case-filter');
  const releaseControl = document.getElementById('catalog-release-control');
  const releaseEyebrow = document.getElementById('catalog-release-eyebrow');
  const releaseTitle = document.getElementById('catalog-release-title');
  const releaseDetails = document.getElementById('catalog-release-details');
  const releaseFilter = document.getElementById('catalog-release-filter');
  const releaseNote = document.getElementById('catalog-release-note');
  const frameworkStylesheet = document.getElementById('catalog-framework-stylesheet');
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
      publishedCssCovered: card.dataset.catalogAlpha4 === 'true',
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

  // A source-only deep link must not be hidden by the default published filter.
  // Resolve the fragment before scrolling; never query-select with raw URL text.
  function revealHashTarget() {
    let id;
    try {
      id = decodeURIComponent(window.location.hash.slice(1));
    } catch {
      return;
    }
    if (!id) return;
    const target = document.getElementById(id);
    const card = target?.closest('.catalog-card');
    if (!card) return;
    if (card.hidden) {
      search.value = '';
      category.value = 'all';
      if (browserFilter) browserFilter.value = 'all';
      if (moduleFilter) moduleFilter.value = 'all';
      if (useCaseFilter) useCaseFilter.value = 'all';
      if (releaseFilter && card.dataset.catalogAlpha4 !== 'true') {
        releaseFilter.value = 'source-alpha5';
      }
      applyRelease();
    }
    // After filtering and CSS selection, ensure the anchor is within view.
    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => target.scrollIntoView({block: 'start'}));
    });
  }
  window.addEventListener('hashchange', revealHashTarget);

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
        if (releaseFilter && card.dataset.catalogAlpha4 !== 'true') releaseFilter.value = 'source-alpha5';
        applyRelease();
      });
    }
  }

  function updateResults() {
    const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    let count = 0;
    const feature = browserFilter?.value || 'all';
    const module = moduleFilter?.value || 'all';
    const useCase = useCaseFilter?.value || 'all';
    const publishedOnly = releaseFilter?.value === 'published-alpha4';
    for (const {card, terms: text, hasAdditionalNativeApi, publishedCssCovered, requiredModules, useCases} of searchable) {
      const matchesModule = module === 'all'
        || (module === 'core-only'
          ? requiredModules.size === 1 && requiredModules.has('syntyr.core.css')
          : requiredModules.has(module));
      const match = (!publishedOnly || publishedCssCovered)
        && (category.value === 'all' || card.dataset.catalogCategory === category.value)
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
  const publishedStylesheet = window.location.protocol === 'file:'
    ? '../site-releases/0.3.0-alpha.4/syntyr.all.css'
    : 'https://syntyr-css.pages.dev/v/0.3.0-alpha.4/syntyr.all.css';
  const sourceStylesheet = '../dist/syntyr.all.css';
  function applyRelease() {
    const published = releaseFilter?.value === 'published-alpha4';
    if (releaseEyebrow) {
      releaseEyebrow.textContent = published
        ? 'PUBLISHED RELEASE / CSS-COVERAGE CHECKED'
        : 'SOURCE PREVIEW / NOT A PUBLISHED RELEASE';
    }
    if (releaseTitle) {
      releaseTitle.textContent = published
        ? 'Published alpha.4 CSS-covered examples'
        : 'Unreleased alpha.5 component examples';
    }
    if (releaseDetails) {
      releaseDetails.textContent = published
        ? 'This view includes examples whose required CSS modules and class selectors exist in the immutable alpha.4 release. It does not certify visual parity, accessibility, or browser interaction behavior. For production, download and self-host the pinned CSS.'
        : 'These examples use the unreleased alpha.5 source candidate. They may need classes or modules absent from published alpha.4. Preview and copy them only with matching alpha.5 CSS.';
    }

    // Switch the real CSS in the preview, not just a status badge.
    if (frameworkStylesheet) {
      frameworkStylesheet.setAttribute('href', published ? publishedStylesheet : sourceStylesheet);
    }
    if (theme && root) {
      for (const option of theme.options) {
        if (!['studio', 'grid', 'noir'].includes(option.value)) option.disabled = published;
      }
      if (published && !['studio', 'grid', 'noir'].includes(theme.value)) {
        theme.value = 'studio';
        root.dataset.synTheme = theme.value;
      }
    }
    for (const {card, publishedCssCovered} of searchable) {
      const label = card.querySelector('.catalog-release-label');
      if (!label) continue;
      const eligible = published && publishedCssCovered;
      label.textContent = eligible ? 'alpha.4 CSS checked' : 'alpha.5 preview';
      label.title = eligible
        ? 'CSS modules and selectors are present in the immutable alpha.4 release; visual and browser behavior must still be verified.'
        : 'Preview from the unreleased alpha.5 source candidate';
    }
    if (releaseNote) {
      releaseNote.textContent = published
        ? 'Published alpha.4: showing only examples with matching frozen CSS modules and class selectors. The gallery uses actual alpha.4 CSS. This is not a visual, accessibility, or interaction certification.'
        : 'Unreleased alpha.5 source preview: all experimental examples are visible. Copy full page uses source candidate CSS; do not mix it with the published release.';
    }
    updateResults();
  }

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
  if (releaseControl) releaseControl.hidden = false;
  controls.hidden = false;
  search.addEventListener("input", updateResults);
  category.addEventListener("change", updateResults);
  browserFilter?.addEventListener("change", updateResults);
  moduleFilter?.addEventListener("change", updateResults);
  useCaseFilter?.addEventListener("change", updateResults);
  releaseFilter?.addEventListener('change', applyRelease);
  applyRelease();
  revealHashTarget();

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
    const published = releaseFilter?.value === 'published-alpha4';
    if (published && card.dataset.catalogAlpha4 !== 'true') {
      throw new Error('This example is not covered by the published CSS release');
    }
    const prefix = published ? 'https://syntyr-css.pages.dev/v/0.3.0-alpha.4/' : '/dist/';
    const releaseComment = published
      ? 'Self-host the pinned 0.3.0-alpha.4 stylesheets in production; class coverage is not an accessibility or behavior guarantee.'
      : 'Self-host matching unreleased alpha.5 CSS under /dist/ or adjust these paths.';
    const links = [...required].map(name => `<link rel="stylesheet" href="${prefix}${name}">`).join('\n');
    const heading = card.querySelector('h2')?.textContent || 'Syntyr example';
    const title = heading.replace(/[&<>"']/g, ch => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[ch]));
    return `<!doctype html>\n<html lang="en">\n<head>\n  <meta charset="utf-8">\n  <meta name="viewport" content="width=device-width,initial-scale=1">\n  <title>${title} — Syntyr CSS</title>\n  <!-- ${releaseComment} -->\n  ${links}\n</head>\n<body class="syn-root" data-syn-theme="studio">\n${markup}\n</body>\n</html>`;
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
