import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from '../server.mjs';
import { field, notice, button, table, pagination, renderPage } from '../components.mjs';

async function get(path, options) {
  const server = createServer();
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  try {
    const response = await fetch(`http://127.0.0.1:${server.address().port}${path}`, options);
    return { status: response.status, body: await response.text(), headers: response.headers };
  } finally {
    await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  }
}

test('reusable components escape plain text and attribute values', () => {
  const html = field({ id: `x\" onfocus=\"alert(1)`, name: 'q', label: '<search>', value: '<img src=x onerror=alert(1)>', help: 'Try &amp;', error: '' });
  assert.match(html, /for="x&amp;quot;|for="x&quot;/); // quote escaped in attribute context
  assert.match(html, /&lt;img src=x onerror=alert\(1\)&gt;/);
  assert.ok(!html.includes('<img'));
  assert.ok(!html.includes('onfocus="alert(1)"'));
  assert.match(notice({message: '<script>bad</script>', danger: true}), /&lt;script&gt;bad&lt;\/script&gt;/);
  assert.match(button({label: '<OK>', primary: true, submit: true}), /&lt;OK&gt;/);
  assert.match(table([{title: '<b>', description: 'A & B'}]), /A &amp; B/);
});

test('pagination rejects unsafe or cross-origin links', () => {
  for (const href of ['javascript:alert(1)', '//evil.example/path', '/\\evil.example', '/\u000ajavascript:']) {
    assert.throws(() => pagination({page: 2, total: 3, prevURL: href}), /Unsafe pagination URL/);
  }
});

test('validation links the described error to the input', () => {
  const html = field({id: 'resource-query', name: 'q', label: 'Search', value: '', error: 'Please revise.'});
  assert.match(html, /data-syn-state="error"/);
  assert.match(html, /aria-invalid="true"/);
  assert.match(html, /aria-describedby="resource-query-error"/);
  assert.match(html, /id="resource-query-error"/);
  assert.ok(!html.includes('aria-describedby="resource-query-help"'));
});

test('table and pagination retain their native semantic contracts', () => {
  const html = table([{title: 'Inventory', description: 'Assets'}]) + pagination({page: 2, total: 3, prevURL: '/', nextURL: '/?q=%26&page=3'});
  for (const contract of ['class="syn-table"', '<caption>', 'scope="col"', 'scope="row"', 'aria-current="page"', 'aria-label="Resource pages"', 'rel="prev"', 'rel="next"', '&amp;page=3']) assert.ok(html.includes(contract), contract);
  assert.match(table([]), /No matching resources/);
});

test('server generates a complete HTML page, escapes search data and preserves encoded filters', async () => {
  const result = await get('/?q=%26&page=1');
  assert.equal(result.status, 200);
  assert.match(result.body, /class="syn-root/);
  assert.match(result.body, /name="q"/);
  assert.match(result.body, /value="&amp;"/);
  assert.match(result.body, /href="\/\?q=%26&amp;page=2"|href="\/\?page=2&amp;q=%26"/);
  assert.ok(!result.body.includes('<script'));
  assert.equal(result.headers.get('cache-control'), 'no-store');
  assert.equal(result.headers.get('x-content-type-options'), 'nosniff');
  const malicious = await get('/?q=%3Csvg%20onload%3Dalert(1)%3E');
  assert.ok(!malicious.body.includes('<svg'));
  assert.ok(malicious.body.includes('&lt;svg'));
});

test('invalid queries and pagination report server errors without executable markup', async () => {
  const tooLong = await get('/?q=' + 'x'.repeat(81));
  assert.equal(tooLong.status, 400);
  assert.match(tooLong.body, /aria-invalid="true"/);
  assert.match(tooLong.body, /role="alert"/);
  assert.match(tooLong.body, /id="resource-query-error"/);
  for (const path of ['/?page=zero', '/?page=-1', '/?page=999']) {
    const response = await get(path);
    assert.equal(response.status, 400, path);
  }
});

test('HTTP handling is explicitly GET/HEAD-only with one CSS asset', async () => {
  assert.equal((await get('/unknown')).status, 404);
  const post = await get('/', {method:'POST'});
  assert.equal(post.status, 405);
  assert.equal(post.headers.get('allow'), 'GET, HEAD');
  assert.equal((await get('/', {method:'HEAD'})).body, '');
  const css = await get('/assets/syntyr.core.css');
  assert.equal(css.status, 200);
  assert.match(css.headers.get('content-type'), /text\/css/);
  assert.equal((await get('/assets/../README.md')).status, 404);
});

test('renderPage assembles component functions instead of injecting a browser runtime', () => {
  const html = renderPage({query: {id: 'search', name: 'q', label: 'Search', value: ''}, notice: {message: 'Ready'}, searchButton: {label: 'Go', submit: true}, records: [], pager: {page: 1, total: 1}});
  assert.match(html, /<form[^>]*method="get"/);
  assert.ok(!html.includes('<script'));
});

test('rejected Node search does not expose results or actionable pagination', async () => {
  const query = '&' + ' '.repeat(79) + 'X';
  const res = await get('/?q=' + encodeURIComponent(query));
  assert.equal(res.status, 400);
  assert.match(res.body, /aria-invalid="true"/);
  assert.match(res.body, /id="resource-query-error"/);
  assert.doesNotMatch(res.body, /<table class="syn-table"|aria-label="Resource pages"|rel="next"/);
  const valid = await get('/?q=%26');
  assert.equal(valid.status, 200);
  assert.match(valid.body, /rel="next"/);
});

test('malformed Node query percent sequences are rejected', async () => {
  for (const path of ['/?q=CRM&page=%ZZ', '/?q=%ZZ', '/?q=CRM%', '/?page=2&q=%ZZ']) {
    assert.equal((await get(path)).status, 400, path);
  }
});
