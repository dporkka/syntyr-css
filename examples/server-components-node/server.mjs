// Runnable, optional Node.js stdlib example; no packages or client JS required.
import { readFileSync } from 'node:fs';
import { createServer as httpCreateServer } from 'node:http';
import { fileURLToPath } from 'node:url';
import { renderPage } from './components.mjs';

const css = readFileSync(fileURLToPath(new URL('../../dist/syntyr.core.css', import.meta.url)));
const resources = [
  { title: 'Billing', description: 'Invoices & statements' },
  { title: 'CRM', description: 'Accounts & contacts' },
  { title: 'Inventory', description: 'Assets & availability' },
  { title: 'Operations', description: 'Work orders and inspections' },
  { title: 'Proposals', description: 'Contracts and approvals' },
  { title: 'Reporting', description: 'Revenue and campaign summaries' },
];
const pageSize = 2;
const maxQueryLength = 80;

function pageHref(query, page) {
  const params = new URLSearchParams();
  if (query) params.set('q', query);
  if (page > 1) params.set('page', String(page));
  const encoded = params.toString();
  return encoded ? `/?${encoded}` : '/';
}

export function pageData(query, rawPage = '') {
  const truncated = Array.from(query).slice(0, maxQueryLength).join('');
  const invalidQuery = Array.from(query).length > maxQueryLength;
  const filtered = resources.filter(({title, description}) =>
    `${title} ${description}`.toLowerCase().includes(truncated.trim().toLowerCase()));
  const total = Math.max(1, Math.ceil(filtered.length / pageSize));
  const parsed = Number(rawPage);
  const invalidPage = rawPage !== '' && (!/^\d+$/.test(rawPage) || !Number.isSafeInteger(parsed) || parsed < 1 || parsed > total);
  const page = invalidPage || rawPage === '' ? 1 : parsed;
  const pager = {
    page, total,
    prevURL: page > 1 ? pageHref(truncated, page - 1) : '',
    nextURL: page < total ? pageHref(truncated, page + 1) : '',
  };
  return {
    status: invalidQuery || invalidPage ? 400 : 200,
    // Invalid search state is for display only; never expose derived results
    // or links from a silently truncated, rejected filter.
    showResults: !invalidQuery && !invalidPage,
    query: {
      id: 'resource-query', name: 'q', label: 'Find a resource', value: truncated,
      help: 'Search titles and descriptions.',
      error: invalidQuery ? 'Search must be at most 80 characters.' : '',
    },
    notice: invalidQuery
      ? {message: 'Correct the search field and try again.', danger: true}
      : invalidPage ? {message: 'Page number is invalid for these results.', danger: true}
        : {message: 'Filtered on the server. No browser JavaScript required.', danger: false},
    searchButton: {label: 'Search', primary: true, submit: true},
    records: invalidQuery || invalidPage ? [] : filtered.slice((page-1)*pageSize, page*pageSize),
    pager: invalidQuery || invalidPage ? {page: 1, total: 1, prevURL: '', nextURL: ''} : pager,
  };
}

export function createServer() {
  return httpCreateServer((req, res) => {
    res.setHeader('X-Content-Type-Options', 'nosniff');
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      res.writeHead(405, {'Allow': 'GET, HEAD', 'Content-Type': 'text/plain; charset=utf-8'});
      res.end('Method not allowed');
      return;
    }
    let url;
    try {
      url = new URL(req.url, 'http://localhost');
    } catch {
      res.writeHead(400);
      res.end();
      return;
    }
    // URLSearchParams tolerates bad percent sequences; reject them rather
    // than silently changing the query's meaning on native GET requests.
    if (/%(?![0-9a-f]{2})/i.test(url.search)) {
      res.writeHead(400, {'Content-Type': 'text/plain; charset=utf-8'});
      res.end(req.method === 'HEAD' ? undefined : 'Invalid query encoding');
      return;
    }
    if (url.pathname === '/assets/syntyr.core.css') {
      res.writeHead(200, {'Content-Type': 'text/css; charset=utf-8', 'Cache-Control': 'public, max-age=3600'});
      res.end(req.method === 'HEAD' ? undefined : css);
      return;
    }
    if (url.pathname !== '/') {
      res.writeHead(404, {'Content-Type': 'text/plain; charset=utf-8'});
      res.end(req.method === 'HEAD' ? undefined : 'Not found');
      return;
    }
    const data = pageData(url.searchParams.get('q') ?? '', url.searchParams.get('page') ?? '');
    const html = renderPage(data);
    res.writeHead(data.status, {'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store'});
    res.end(req.method === 'HEAD' ? undefined : html);
  });
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const address = process.env.SYNTYR_ADDR || '127.0.0.1';
  const port = Number(process.env.SYNTYR_PORT || 8768);
  createServer().listen(port, address, () => {
    console.log(`Syntyr Node.js server components at http://${address}:${port}/`);
  });
}
