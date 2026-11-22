/* Server-side fixtures for the opt-in Syntyr HTMX live demo.
   This is intentionally read-only. No user data, storage or mutations. */
const PATH = '/api/htmx-demo/customers';
const LIMIT = 4;
const SORTS = new Set(['name_asc', 'name_desc']);
const CUSTOMER_DATA = Object.freeze([
  ['Acme Displays', 'Atlanta', 'Static OOH'],
  ['Apex Outdoor', 'Denver', 'Digital OOH'],
  ['Beacon Signs', 'Seattle', 'Static OOH'],
  ['Canyon Media', 'Phoenix', 'Digital OOH'],
  ['Clearline Advertising', 'Austin', 'Transit'],
  ['MetroVista', 'Chicago', 'Static OOH'],
  ['Northstar Media', 'Boston', 'Digital OOH'],
  ['Orbit Outdoor', 'Miami', 'Static OOH'],
  ['Pioneer Displays', 'Portland', 'Transit'],
  ['Summit Signworks', 'Nashville', 'Digital OOH'],
]);

export function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

function queryHref({q, sort, page}) {
  const params = new URLSearchParams();
  if (q) params.set('q', q);
  if (sort !== 'name_asc') params.set('sort', sort);
  if (page > 1) params.set('page', String(page));
  const suffix = params.toString();
  return PATH + (suffix ? '?' + suffix : '');
}

function readState(request) {
  if (request.url.length > 2048) return null;
  const url = new URL(request.url);
  const q = url.searchParams.get('q') ?? '';
  const sort = url.searchParams.get('sort') ?? 'name_asc';
  const pageValue = url.searchParams.get('page') ?? '1';
  if (q.length > 80 || !SORTS.has(sort) || !/^[1-9]\d{0,2}$/.test(pageValue)) return null;
  const page = Number(pageValue);
  const customers = CUSTOMER_DATA
    .filter((row) => row.join(' ').toLocaleLowerCase('en').includes(q.trim().toLocaleLowerCase('en')))
    .slice()
    .sort((a, b) => a[0].localeCompare(b[0], 'en') * (sort === 'name_desc' ? -1 : 1));
  const totalPages = Math.max(1, Math.ceil(customers.length / LIMIT));
  if (page > totalPages) return null;
  return {q, sort, page, customers, totalPages};
}

function response(html, status = 200, extraHeaders = {}) {
  const headers = {
    'Content-Type': 'text/html; charset=utf-8',
    'Cache-Control': 'no-store',
    'Vary': 'HX-Request, HX-History-Restore-Request',
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'X-Frame-Options': 'DENY',
    'Content-Security-Policy': "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'",
    ...extraHeaders,
  };
  return new Response(html, {status, headers});
}

function makeLink(label, href, className = 'syn-button') {
  const safe = escapeHtml(href);
  return '<a class="' + className + '" href="' + safe +
    '" hx-get="' + safe +
    '" hx-target="#customer-results" hx-swap="outerHTML" hx-push-url="true">' +
    escapeHtml(label) + '</a>';
}

export function renderResults(state) {
  const {q, sort, page, customers, totalPages} = state;
  const data = customers.slice((page - 1) * LIMIT, page * LIMIT);
  const nextSort = sort === 'name_asc' ? 'name_desc' : 'name_asc';
  const sortHref = queryHref({q, sort: nextSort, page: 1});
  const status = q.trim()
    ? customers.length + ' matching customers for “' + escapeHtml(q.trim()) + '”'
    : customers.length + ' fictional customers';
  const rows = data.map(([name,city,media]) => (
    '<tr><th scope="row">' + escapeHtml(name) + '</th><td>' +
    escapeHtml(city) + '</td><td>' + escapeHtml(media) + '</td></tr>'
  )).join('');
  const table = customers.length
    ? '<div class="syn-table-wrap" role="region" aria-label="Scrollable customer table" tabindex="0">' +
      '<table class="syn-table syn-table--striped syn-table--readable">' +
      '<caption>Fictional outdoor advertising customers</caption><thead><tr>' +
      '<th scope="col" aria-sort="' + (sort === 'name_asc' ? 'ascending' : 'descending') + '">' +
      makeLink('Customer name ' + (sort === 'name_asc' ? '↑' : '↓'), sortHref, 'syn-table-sort') +
      '</th><th scope="col">City</th><th scope="col">Format</th></tr></thead>' +
      '<tbody>' + rows + '</tbody></table></div>'
    : '<p class="syn-alert" role="status">No customers match this search. Try another term.</p>';
  const previous = page > 1 ? makeLink('Previous', queryHref({q,sort,page:page-1})) : '';
  const next = page < totalPages ? makeLink('Next', queryHref({q,sort,page:page+1})) : '';
  return '<section id="customer-results" class="syn-panel syn-stack" aria-live="polite" aria-label="Customer results"' +
    ' data-syn-htmx-transition>' +
    '<p class="syn-caption">' + status + '</p>' + table +
    '<nav class="syn-inline" aria-label="Results pages">' + previous +
    '<span class="syn-caption">Page ' + page + ' of ' + totalPages + '</span>' + next +
    '</nav></section>';
}

function form(state) {
  const q = escapeHtml(state.q);
  return '<form id="customer-search" class="syn-panel syn-stack" action="' + PATH + '" method="get" role="search"' +
    ' hx-get="' + PATH + '" hx-target="#customer-results" hx-swap="outerHTML"' +
    ' hx-trigger="submit, input changed delay:350ms from:#demo-query, change from:#demo-sort"' +
    ' hx-push-url="true" hx-indicator="#demo-search-indicator">' +
    '<label for="demo-query">Search fictional customers</label>' +
    '<input class="syn-input" type="search" id="demo-query" name="q" maxlength="80"' +
    ' placeholder="Try Acme, Media or Chicago" value="' + q + '">' +
    '<label for="demo-sort">Sort by customer name</label>' +
    '<select class="syn-input" id="demo-sort" name="sort">' +
    '<option value="name_asc"' + (state.sort === 'name_asc' ? ' selected' : '') + '>A–Z</option>' +
    '<option value="name_desc"' + (state.sort === 'name_desc' ? ' selected' : '') + '>Z–A</option></select>' +
    '<div class="syn-inline"><button class="syn-button syn-button--primary" type="submit">Search</button>' +
    '<span id="demo-search-indicator" class="syn-htmx-indicator" role="status">Loading results…</span></div></form>';
}

export function renderDocument(state) {
  return '<!doctype html><html lang="en"><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width, initial-scale=1">' +
    '<meta name="robots" content="noindex,follow">' +
    '<meta name="htmx-config" content=' + "'{\"includeIndicatorStyles\":false,\"historyRestoreAsHxRequest\":false}'" + '>' +
    '<title>Customer results — Syntyr HTMX live demo</title>' +
    '<link rel="stylesheet" href="/dist/syntyr.core.css">' +
    '<link rel="stylesheet" href="/dist/syntyr.recipes.css">' +
    '<link rel="stylesheet" href="/integrations/htmx/syntyr.htmx.css">' +
    '<link rel="stylesheet" href="/docs/docs.css">' +
    '<script defer src="/docs/vendor/htmx-2.0.11.min.js"></script></head>' +
    '<body class="syn-root syn-page" data-syn-theme="studio">' +
    '<a class="syn-button docs-skip" href="#demo-main">Skip to live demo</a>' +
    '<div class="syn-shell"><header class="syn-header"><a class="syn-logo" href="/">SYNTYR / CSS</a>' +
    '<nav class="syn-nav" aria-label="Main navigation"><a href="/docs/htmx-components">HTMX recipes</a>' +
    '<a href="/docs/htmx-playground">Live playground</a></nav></header>' +
    '<main class="docs-article-page" id="demo-main">' +
    '<p class="syn-eyebrow">SYNTYR / REAL SERVER RESPONSES</p>' +
    '<h1 class="syn-title">HTMX customer explorer</h1>' +
    '<p class="syn-lede">Read-only fictional data. Search, sort and paginate against a Cloudflare Pages Function.' +
    ' Native GET works without HTMX.</p>' +
    '<p><a href="/docs/htmx-playground">Return to playground introduction</a></p>' +
    '<section class="syn-stack">' + form(state) + renderResults(state) + '</section></main></div></body></html>';
}

export function onCustomersRequest(request) {
  if (request.method !== 'GET') return response('Method not allowed', 405, {'Allow':'GET'});
  const state = readState(request);
  if (!state) return response('<!doctype html><html lang="en"><meta charset="utf-8">' +
    '<title>Invalid demo request</title><body><h1>Invalid demo request</h1>' +
    '<p>Use a search up to 80 characters, an allowed sort value and an existing results page.</p>' +
    '<a href="/docs/htmx-playground">Return to live playground</a></body></html>',400);
  const normalHx = request.headers.get('HX-Request') === 'true' &&
    request.headers.get('HX-History-Restore-Request') !== 'true';
  return response(normalHx ? renderResults(state) : renderDocument(state));
}
