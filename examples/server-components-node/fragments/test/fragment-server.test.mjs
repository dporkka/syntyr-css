import test from 'node:test';
import assert from 'node:assert/strict';
import { createFragmentServer } from '../server.mjs';

async function request(path, { method = 'GET', headers = {} } = {}) {
  const server = createFragmentServer();
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  try {
    const response = await fetch(`http://127.0.0.1:${server.address().port}${path}`, { method, headers, redirect: 'manual' });
    return { status: response.status, body: await response.text(), headers: response.headers };
  } finally {
    await new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
  }
}

test('HTMX full-page fallback and history restores return complete documents', async () => {
  const full = await request('/htmx?q=CRM');
  assert.equal(full.status, 200);
  assert.match(full.body, /<!doctype html>/i);
  assert.match(full.body, /class="syn-root/);
  assert.match(full.body, /action="\/htmx" method="get"/);
  assert.match(full.body, /hx-get="\/htmx"/);
  assert.match(full.body, /hx-target="#resource-workspace"/);
  assert.match(full.body, /id="resource-workspace"/);
  assert.match(full.body, /<table class="syn-table">/);
  assert.match(full.body, /value="CRM"/);
  assert.equal(full.headers.get('vary'), 'HX-Request, HX-History-Restore-Request');
  assert.equal(full.headers.get('cache-control'), 'no-store');
  const restore = await request('/htmx?q=CRM', { headers: { 'HX-Request': 'true', 'HX-History-Restore-Request': 'true' } });
  assert.match(restore.body, /<!doctype html>/i);
});

test('HTMX fragment is composed from existing server HTML components', async () => {
  const fragment = await request('/htmx?q=CRM', { headers: { 'HX-Request': 'true' } });
  assert.equal(fragment.status, 200);
  assert.doesNotMatch(fragment.body, /<html|<!doctype|<script/i);
  for (const contract of ['id="resource-workspace"', 'class="syn-field"', 'class="syn-input"', 'class="syn-table"', 'aria-label="Resource pages"', 'scope="row"', 'action="/htmx"']) {
    assert.ok(fragment.body.includes(contract), contract);
  }
  assert.equal(fragment.headers.get('vary'), 'HX-Request, HX-History-Restore-Request');
});

test('pagination links stay on their own route and retain encoded filters', async () => {
  for (const mode of ['htmx', 'datastar']) {
    const full = await request(`/${mode}`);
    assert.ok(full.body.includes(`href="/${mode}?page=2"`));
    assert.ok(!full.body.includes('href="/?page=2"'));
    const second = await request(`/${mode}?page=2`);
    assert.equal(second.status, 200);
    assert.ok(second.body.includes(`href="/${mode}"`));
    const encoded = await request(`/${mode}?q=%26`);
    assert.ok(encoded.body.includes(`href="/${mode}?q=%26&amp;page=2"`));
  }
});

test('HTMX uses explicit opt-in 422 swapping for server-side validation', async () => {
  const invalidQuery = '/htmx?q=' + 'a'.repeat(81);
  const native = await request(invalidQuery);
  const enhanced = await request(invalidQuery, { headers: { 'HX-Request': 'true' } });
  assert.equal(native.status, 400);
  assert.match(native.body, /<!doctype html>/i);
  assert.equal(enhanced.status, 422);
  assert.equal(enhanced.headers.get('x-syntyr-validation'), 'invalid');
  assert.match(enhanced.body, /aria-invalid="true"/);
  assert.match(enhanced.body, /aria-describedby="resource-query-error"/);
  assert.match(enhanced.body, /id="resource-query-error"/);
  assert.match(enhanced.body, /role="alert"/);
  const script = await request('/scripts/htmx-validation.js');
  assert.equal(script.status, 200);
  assert.match(script.headers.get('content-type'), /javascript/);
  assert.match(script.body, /htmx:beforeSwap/);
  assert.match(script.body, /X-Syntyr-Validation/);
  assert.match(script.body, /status === 422/);
});

test('Datastar responds with ordinary HTML for native GET and SSE for signals', async () => {
  const full = await request('/datastar?q=Inventory');
  assert.equal(full.status, 200);
  assert.match(full.body, /<!doctype html>/i);
  assert.match(full.body, /action="\/datastar" method="get"/);
  assert.match(full.body, /data-bind:q/);
  assert.match(full.body, /data-on:submit/);
  assert.match(full.body, /value="Inventory"/);
  const signals = encodeURIComponent(JSON.stringify({ q: 'Inventory' }));
  const sse = await request(`/datastar?datastar=${signals}`, { headers: { Accept: 'text/event-stream' } });
  assert.equal(sse.status, 200);
  assert.match(sse.headers.get('content-type'), /text\/event-stream/);
  assert.equal(sse.headers.get('vary'), 'Accept');
  assert.equal(sse.headers.get('cache-control'), 'no-store');
  assert.ok(sse.body.startsWith('event: datastar-patch-elements\ndata: elements <'));
  assert.ok(sse.body.endsWith('\n\n'));
  assert.doesNotMatch(sse.body, /<html|<script/i);
  assert.match(sse.body, /id="resource-workspace"/);
  assert.match(sse.body, /class="syn-table"/);
  assert.match(sse.body, /value="Inventory"/);
});

test('Datastar treats signals as untrusted data and protects SSE event framing', async () => {
  const malicious = '<img src=x onerror=alert(1)>\r\nevent: injected\n\ndata: evil';
  const signals = encodeURIComponent(JSON.stringify({ q: malicious }));
  const sse = await request(`/datastar?datastar=${signals}`, { headers: { Accept: 'text/event-stream' } });
  assert.equal(sse.status, 200);
  assert.match(sse.body, /&lt;img/);
  assert.doesNotMatch(sse.body, /<img|onerror="alert/);
  const lines = sse.body.trimEnd().split('\n');
  assert.equal(lines.length, 2);
  assert.equal(lines.filter(line => line.startsWith('event:')).length, 1);
  assert.equal(lines.filter(line => line.startsWith('data:')).length, 1);
  const error = await request(`/datastar?datastar=${encodeURIComponent(JSON.stringify({q: 'x'.repeat(81)}))}`, { headers: { Accept: 'text/event-stream' } });
  assert.equal(error.status, 200);
  assert.match(error.body, /aria-invalid="true"/);
  assert.match(error.body, /role="alert"/);
  for (const payload of ['{', '[]', '{"q":42}', 'x'.repeat(4097)]) {
    const rejected = await request(`/datastar?datastar=${encodeURIComponent(payload)}`, { headers: { Accept: 'text/event-stream' } });
    assert.equal(rejected.status, 400);
    assert.doesNotMatch(rejected.body, /datastar-patch-elements/);
  }
});

test('HTTP methods, root paths and static assets are allowlisted', async () => {
  assert.equal((await request('/unknown')).status, 404);
  const post = await request('/htmx', { method: 'POST' });
  assert.equal(post.status, 405);
  assert.equal(post.headers.get('allow'), 'GET, HEAD');
  const head = await request('/datastar', { method: 'HEAD' });
  assert.equal(head.status, 200);
  assert.equal(head.body, '');
  const css = await request('/assets/syntyr.core.css');
  assert.equal(css.status, 200);
  assert.match(css.headers.get('content-type'), /text\/css/);
  assert.equal((await request('/assets/README.md')).status, 404);
  assert.equal((await request('/assets/../README.md')).status, 404);
  assert.equal((await request('/')).status, 302);
});

test('rejected fragment searches retain accessible errors but no stale results or pagination', async () => {
  const invalid = '&' + ' '.repeat(79) + 'X';
  const htmx = await request('/htmx?q=' + encodeURIComponent(invalid), {headers: {'HX-Request':'true'}});
  assert.equal(htmx.status, 422);
  assert.match(htmx.body, /aria-invalid="true"/);
  assert.match(htmx.body, /id="resource-query-error"/);
  assert.doesNotMatch(htmx.body, /<table class="syn-table"|aria-label="Resource pages"|rel="next"/);
  const native = await request('/datastar?q=' + encodeURIComponent(invalid));
  assert.equal(native.status, 400);
  assert.doesNotMatch(native.body, /<table class="syn-table"|aria-label="Resource pages"/);
  const signals = encodeURIComponent(JSON.stringify({q: invalid}));
  const sse = await request('/datastar?datastar=' + signals, {headers: {Accept:'text/event-stream'}});
  assert.equal(sse.status, 200);
  assert.match(sse.body, /aria-invalid="true"/);
  assert.doesNotMatch(sse.body, /<table class="syn-table"|aria-label="Resource pages"|rel="next"/);
  for (const mode of ['htmx','datastar']) {
    const valid = await request(`/${mode}?q=%26`);
    assert.equal(valid.status, 200);
    assert.match(valid.body, /rel="next"/);
  }
});

test('fragment routes reject invalid percent encoding instead of changing the query', async () => {
  for (const path of ['/htmx?q=CRM&page=%ZZ','/htmx?q=%ZZ','/datastar?q=%ZZ','/datastar?q=CRM%']) {
    assert.equal((await request(path)).status,400,path);
  }
});
