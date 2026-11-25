// Optional, copy-owned HTML fragment demo: server controls data and responses;
// Syntyr provides presentation-only CSS and semantic HTML classes.
import { readFileSync } from 'node:fs';
import { createServer as createHTTPServer } from 'node:http';
import { fileURLToPath } from 'node:url';
import { field, notice, button, table, pagination } from '../components.mjs';
import { pageData } from '../server.mjs';

// Allowlist the only static assets this standalone demo serves.
const assets = new Map([
  ['/assets/syntyr.core.css', {
    body: readFileSync(fileURLToPath(new URL('../../../dist/syntyr.core.css', import.meta.url))),
    type: 'text/css; charset=utf-8',
  }],
  ['/scripts/htmx-validation.js', {
    body: readFileSync(fileURLToPath(new URL('./htmx-validation.js', import.meta.url))),
    type: 'text/javascript; charset=utf-8',
  }],
]);

const htmlType = 'text/html; charset=utf-8';
const streamType = 'text/event-stream; charset=utf-8';

function response(res, status, type, body, { head = false, headers = {} } = {}) {
  res.writeHead(status, {
    'Content-Type': type,
    'X-Content-Type-Options': 'nosniff',
    'Cache-Control': 'no-store',
    ...headers,
  });
  res.end(head ? undefined : body);
}

function scopedPageHref(route, href) {
  if (!href) return '';
  // pageData emits only same-origin root links. Keep links within the selected
  // demo route so navigation never falls through to the other Node example.
  if (href !== '/' && !href.startsWith('/?')) throw new TypeError('Unexpected pagination path');
  return route + href.slice(1);
}

export function renderWorkspace(mode, data) {
  const isHtmx = mode === 'htmx';
  const path = `/${mode}`;
  // Stable wrapper is replaced atomically. Neither framework owns the
  // outer .syn-root, and the same components render initial and updated HTML.
  const attributes = isHtmx
    ? 'hx-get="/htmx" hx-target="#resource-workspace" hx-swap="outerHTML" hx-push-url="true"'
    : `data-indicator:_fetching="" data-on:submit="!$_fetching && @get('/datastar')" data-attr:aria-busy="String($_fetching)"`;
  const input = isHtmx ? field(data.query) : field(data.query).replace(
    'type="search"', 'type="search" data-bind:q=""',
  );
  const submit = isHtmx ? button(data.searchButton) : button(data.searchButton).replace(
    'type="submit"', 'type="submit" data-attr:disabled="$_fetching" data-attr:data-syn-state="$_fetching ? \'loading\' : null"',
  );
  return `<div id="resource-workspace" class="syn-stack">
    <form class="syn-form" action="${path}" method="get" role="search" ${attributes}>
      ${input}
      ${submit}
      ${isHtmx ? '' : '<output role="status" data-show="$_fetching" style="display:none">Searching…</output>'}
    </form>
    ${notice(data.notice)}
    ${data.showResults === false ? '' : `<section id="resource-results" class="syn-stack" role="region" aria-label="Search results" aria-live="polite">
      ${table(data.records)}
      ${pagination({
        ...data.pager,
        prevURL: scopedPageHref(path, data.pager.prevURL),
        nextURL: scopedPageHref(path, data.pager.nextURL),
      })}
    </section>`}
  </div>`;
}

export function renderDocument(mode, data) {
  const scripts = mode === 'htmx'
    ? `<script defer src="https://unpkg.com/htmx.org@2.0.8/dist/htmx.min.js"></script>
       <script defer src="/scripts/htmx-validation.js"></script>`
    : '<script type="module" src="https://cdn.jsdelivr.net/gh/starfederation/datastar@v1.0.5/bundles/datastar.js"></script>';
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Syntyr component fragments — ${mode === 'htmx' ? 'HTMX' : 'Datastar'}</title>
  <link rel="stylesheet" href="/assets/syntyr.core.css">
  ${scripts}
</head>
<body class="syn-root syn-page" data-syn-theme="studio">
  <main class="syn-shell syn-stack">
    <header><h1 class="syn-heading">Syntyr server HTML fragments</h1>
      <p>Native GET search with optional ${mode === 'htmx' ? 'HTMX' : 'Datastar'} enhancement.</p>
      <nav aria-label="Examples" class="syn-inline"><a href="/htmx">HTMX</a><a href="/datastar">Datastar</a></nav>
    </header>
    ${renderWorkspace(mode, data)}
  </main>
</body>
</html>`;
}

function parseSignals(raw) {
  // Limit parsing work and reject malformed / wrong-shape data. No arbitrary
  // serialized signal object is ever inserted into HTML or JavaScript.
  if (raw === null || raw.length > 4096) return null;
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object' || typeof parsed.q !== 'string') return null;
    return parsed.q;
  } catch {
    return null;
  }
}

function ssePatch(html) {
  // SSE fields are line-based; escaping HTML is not sufficient to prevent
  // CR/LF injection into SSE record boundaries. Flatten the final markup.
  return `event: datastar-patch-elements\ndata: elements ${html.replace(/[\r\n]/g, ' ')}\n\n`;
}

export function createFragmentServer() {
  return createHTTPServer((req, res) => {
    const head = req.method === 'HEAD';
    if (req.method !== 'GET' && !head) {
      response(res, 405, 'text/plain; charset=utf-8', 'Method not allowed', {
        headers: { Allow: 'GET, HEAD' },
      });
      return;
    }
    let url;
    try { url = new URL(req.url, 'http://localhost'); }
    catch { response(res, 400, 'text/plain; charset=utf-8', 'Bad request', { head }); return; }
    // URLSearchParams tolerates malformed percent escapes. Reject ambiguous
    // query encoding for both native GET and enhanced fragment/SSE requests.
    if (/%(?![0-9a-f]{2})/i.test(url.search)) {
      response(res, 400, 'text/plain; charset=utf-8', 'Invalid query encoding', { head });
      return;
    }
    if (url.pathname === '/') {
      response(res, 302, 'text/plain; charset=utf-8', '', { head, headers: { Location: '/htmx' } });
      return;
    }
    const asset = assets.get(url.pathname);
    if (asset) {
      response(res, 200, asset.type, asset.body, { head });
      return;
    }
    if (url.pathname !== '/htmx' && url.pathname !== '/datastar') {
      response(res, 404, 'text/plain; charset=utf-8', 'Not found', { head });
      return;
    }
    const mode = url.pathname.slice(1);
    if (mode === 'htmx') {
      const data = pageData(url.searchParams.get('q') ?? '', url.searchParams.get('page') ?? '');
      const fragment = req.headers['hx-request']?.toLowerCase() === 'true'
        && req.headers['hx-history-restore-request']?.toLowerCase() !== 'true';
      const isError = data.status !== 200;
      response(res, fragment && isError ? 422 : data.status, htmlType,
        fragment ? renderWorkspace(mode, data) : renderDocument(mode, data), {
          head,
          headers: {
            Vary: 'HX-Request, HX-History-Restore-Request',
            ...(fragment && isError ? { 'X-Syntyr-Validation': 'invalid' } : {}),
          },
        });
      return;
    }
    const isStream = req.headers.accept?.toLowerCase().includes('text/event-stream') === true;
    const q = isStream ? parseSignals(url.searchParams.get('datastar')) : url.searchParams.get('q') ?? '';
    if (q === null) {
      response(res, 400, 'text/plain; charset=utf-8', 'Invalid Datastar signals', { head, headers: { Vary: 'Accept' } });
      return;
    }
    const data = pageData(q, isStream ? '' : url.searchParams.get('page') ?? '');
    const body = isStream ? ssePatch(renderWorkspace(mode, data)) : renderDocument(mode, data);
    response(res, isStream ? 200 : data.status, isStream ? streamType : htmlType, body,
      { head, headers: { Vary: 'Accept' } });
  });
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const addr = process.env.SYNTYR_ADDR || '127.0.0.1';
  const port = Number(process.env.SYNTYR_PORT || 8770);
  createFragmentServer().listen(port, addr, () => {
    console.log(`Syntyr HTML fragment demo at http://${addr}:${port}/htmx and /datastar`);
  });
}
