import test from 'node:test';
import assert from 'node:assert/strict';
import { copyText, enhanceCopyButtons } from '../src/copy.mjs';

function fixture({ target = { textContent: '  <button>Hi</button>\n' }, fail = false } = {}) {
  const listeners = new Map();
  const elements = new Map([['copy-source', target], ['copy-status', { textContent: '' }]]);
  const document = { getElementById: id => elements.get(id) ?? null, querySelectorAll: () => [button] };
  const button = {
    dataset: { synCopyTarget: 'copy-source', synCopyStatus: 'copy-status' },
    ownerDocument: document, hidden: true, disabled: false,
    addEventListener: (name, fn) => listeners.set(name, fn),
    removeEventListener: name => listeners.delete(name),
  };
  const writes = [];
  const clipboard = { async writeText(text) {
    writes.push(text);
    if (fail) throw Error('Permission denied');
  }};
  return { document, button, elements, clipboard, writes, listeners,
    click: () => listeners.get('click')?.({ preventDefault() {} }) };
}

test('copyText sends the exact string only after a successful native clipboard write', async () => {
  const writes = [];
  await copyText('  <unsafe>＆ café\n', { writeText: async value => { writes.push(value); } });
  assert.deepEqual(writes, ['  <unsafe>＆ café\n']);
  await assert.rejects(copyText('missing', undefined), /clipboard/i);
});

test('enhancement is opt-in and announces success after the clipboard resolves', async () => {
  const f = fixture();
  const detach = enhanceCopyButtons(f.document, f.clipboard);
  assert.equal(f.button.hidden, false);
  await f.click();
  assert.deepEqual(f.writes, ['  <button>Hi</button>\n']);
  assert.equal(f.elements.get('copy-status').textContent, 'Copied to clipboard.');
  assert.equal(f.button.disabled, false);
  detach();
  assert.equal(f.button.hidden, true);
  assert.equal(f.listeners.size, 0);
});

test('failure is reported, never claimed to be a successful copy', async () => {
  const f = fixture({ fail: true });
  enhanceCopyButtons(f.document, f.clipboard);
  await f.click();
  assert.equal(f.elements.get('copy-status').textContent, 'Copy failed. Select and copy the text manually.');
  assert.equal(f.button.disabled, false);
});

test('copies current input value rather than stale HTML/default value', async () => {
  const f = fixture({ target: { tagName: 'TEXTAREA', value: 'edited', textContent: 'old' } });
  enhanceCopyButtons(f.document, f.clipboard);
  await f.click();
  assert.deepEqual(f.writes, ['edited']);
});

test('missing target or status prevents a misleading active copy button', () => {
  const f = fixture();
  f.elements.delete('copy-source');
  assert.equal(enhanceCopyButtons(f.document, f.clipboard) instanceof Function, true);
  assert.equal(f.button.hidden, true);
  assert.equal(f.listeners.size, 0);
});

test('double enhancement does not create duplicate listeners or event callbacks', async () => {
  const f = fixture();
  const a = enhanceCopyButtons(f.document, f.clipboard);
  const b = enhanceCopyButtons(f.document, f.clipboard);
  await f.click();
  assert.deepEqual(f.writes, ['  <button>Hi</button>\n']);
  b();
  assert.equal(f.listeners.size, 1);
  a();
  assert.equal(f.listeners.size, 0);
});

test('no DOM or clipboard globals required to import or call the enhancement', () => {
  assert.equal(typeof enhanceCopyButtons(undefined, undefined), 'function');
});

test('copy activation prevents accidental form submission even during async writes', async () => {
  const f = fixture();
  enhanceCopyButtons(f.document, f.clipboard);
  let prevented = 0;
  await f.listeners.get('click')({ preventDefault() { prevented++; } });
  assert.equal(prevented, 1);
  assert.equal(f.writes[0], f.elements.get('copy-source').textContent);
});

test('cleanup invalidates pending clipboard completion before remount', async () => {
  const f = fixture();
  let finishOld;
  let finishNew;
  const oldClipboard = { writeText: () => new Promise(resolve => { finishOld = resolve; }) };
  const newClipboard = { writeText: () => new Promise(resolve => { finishNew = resolve; }) };
  const detachOld = enhanceCopyButtons(f.document, oldClipboard);
  const oldClick = f.click();
  assert.equal(f.button.disabled, true);

  detachOld();
  assert.equal(f.button.disabled, false, 'cleanup must unlock its pending button');
  assert.equal(f.button.hidden, true);

  const detachNew = enhanceCopyButtons(f.document, newClipboard);
  const newClick = f.click();
  assert.equal(f.button.disabled, true);
  finishOld();
  await oldClick;
  assert.equal(f.button.disabled, true, 'stale finally must not unlock current copy');
  assert.equal(f.elements.get('copy-status').textContent, '', 'stale success must not announce');

  finishNew();
  await newClick;
  assert.equal(f.button.disabled, false);
  assert.equal(f.elements.get('copy-status').textContent, 'Copied to clipboard.');
  detachNew();
});

test('a button enabled after mounting stays enabled after a completed copy', async () => {
  const f = fixture();
  f.button.disabled = true;
  const detach = enhanceCopyButtons(f.document, f.clipboard);
  f.button.disabled = false; // The host enabled its own control after mount.
  await f.click();
  assert.equal(f.button.disabled, false);
  assert.equal(f.elements.get('copy-status').textContent, 'Copied to clipboard.');
  detach();
});
