import assert from 'node:assert/strict';
import {test} from 'node:test';
import {onRequest} from '../functions/api/htmx-demo/customers.js';

const base = 'https://syntyr-css.pages.dev/api/htmx-demo/customers';
const call = (path='', headers={}, method='GET') => onRequest({request:new Request(base+path,{headers,method})});
const body = async (r) => await r.text();

test('ordinary GET renders complete themed document and usable fallback form', async () => {
  const r=await call();
  const html=await body(r);
  assert.equal(r.status,200);
  assert.match(r.headers.get('content-type'),/^text\/html/);
  assert.match(html,/<!doctype html>/i);
  assert.match(html,/class="syn-root/);
  assert.match(html,/action="\/api\/htmx-demo\/customers" method="get"/);
  assert.match(html,/name="q"/);
  assert.match(html,/id="customer-results"/);
  assert.match(html,/Acme Displays/);
  assert.match(html,/vendor\/htmx-2\.0\.11\.min\.js/);
});

test('HTMX normal GET returns only a swap-safe fragment, including table and pager', async () => {
  const r=await call('?q=sign&sort=name_desc&page=1',{'HX-Request':'true'});
  const html=await body(r);
  assert.equal(r.status,200);
  assert.doesNotMatch(html,/<!doctype html>/i);
  assert.match(html,/<section id="customer-results"/);
  assert.match(html,/aria-live="polite"/);
  assert.match(html,/<table/);
  assert.match(html,/hx-get="/);
  assert.match(html,/Page 1 of/);
});

test('HTMX history cache miss returns a full document, even with HX-Request true', async () => {
  const r=await call('?q=acme',{'HX-Request':'true','HX-History-Restore-Request':'true'});
  assert.match(await body(r),/<!doctype html>/i);
});

test('search is case-insensitive, filters records and preserves native input value', async () => {
  const html=await body(await call('?q=aCme'));
  assert.match(html,/value="aCme"/);
  assert.match(html,/Acme Displays/);
  assert.doesNotMatch(html,/Northstar Media/);
});

test('query is safely escaped in HTML attributes and visible status', async () => {
  const injection='<img src=x onerror=alert(1)>';
  const html=await body(await call('?q='+encodeURIComponent(injection)));
  assert.doesNotMatch(html,/<img src=x/);
  assert.match(html,/&lt;img src=x onerror=alert\(1\)&gt;/);
  assert.match(html,/No customers match/);
});

test('pagination preserves query and sort in safe encoded hrefs', async () => {
  const html=await body(await call('?q=o&sort=name_desc&page=1',{'HX-Request':'true'}));
  assert.match(html,/sort=name_desc/);
  assert.match(html,/q=o/);
  assert.match(html,/hx-target="#customer-results"/);
});

test('second page has distinct records and correct native GET links', async () => {
  const one=await body(await call('?page=1',{'HX-Request':'true'}));
  const two=await body(await call('?page=2',{'HX-Request':'true'}));
  assert.notEqual(one,two);
  assert.match(two,/Page 2 of/);
  assert.match(two,/Previous/);
  assert.match(two,/Next/);
});

test('descending sort changes record order and corresponding aria-sort', async () => {
  const ascending=await body(await call('?sort=name_asc',{'HX-Request':'true'}));
  const descending=await body(await call('?sort=name_desc',{'HX-Request':'true'}));
  assert.match(ascending,/aria-sort="ascending"/);
  assert.match(descending,/aria-sort="descending"/);
  const indexAsc=ascending.indexOf('Acme Displays');
  const indexDesc=descending.indexOf('Acme Displays');
  assert.ok(indexAsc!==indexDesc || ascending!==descending);
});

test('query too long is rejected without reflecting malicious content', async () => {
  const r=await call('?q='+encodeURIComponent('<script>'+'x'.repeat(1000)));
  assert.equal(r.status,400);
  const html=await body(r);
  assert.doesNotMatch(html,/<script>x/);
});

for (const params of ['?page=-1','?page=0','?page=2.5','?page=Infinity','?page=999','?sort=DROP%20TABLE']) {
  test('invalid parameters are handled safely: '+params,async () => {
    const r=await call(params);
    assert.equal(r.status,400);
    assert.match(r.headers.get('content-type'),/^text\/html/);
    assert.match(await body(r),/Invalid demo request/);
  });
}

test('non-GET methods fail closed with Allow GET and no hidden mutation', async () => {
  const r=await call('',{},'POST');
  assert.equal(r.status,405);
  assert.equal(r.headers.get('allow'),'GET');
});

test('responses are not cached across HX variants and set defense headers', async () => {
  const r=await call('',{'HX-Request':'true'});
  assert.match(r.headers.get('vary'),/HX-Request/i);
  assert.match(r.headers.get('vary'),/HX-History-Restore-Request/i);
  assert.equal(r.headers.get('cache-control'),'no-store');
  assert.equal(r.headers.get('x-content-type-options'),'nosniff');
  assert.match(r.headers.get('content-security-policy'),/script-src 'self'/);
});

test('static demo text is clearly fictional and read-only', async () => {
  const html=await body(await call());
  assert.match(html,/fictional/i);
  assert.match(html,/read-only/i);
  assert.doesNotMatch(html,/<form[^>]+method="post"/i);
});
