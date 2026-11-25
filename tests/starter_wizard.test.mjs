import assert from 'node:assert/strict';
import test from 'node:test';
import { createStarter, createPlaygroundHandoff } from '../docs/starter-wizard.mjs';

test('creates an offline-first published-alpha.4 HTML starter', () => {
  const result = createStarter({ kind: 'saas', theme: 'studio', stack: 'html' });
  assert.match(result.html, /<!doctype html>/i);
  assert.match(result.html, /href="\.\/syntyr\.core\.css"/);
  assert.match(result.html, /data-syn-theme="studio"/);
  assert.match(result.html, /id="next-step"/);
  assert.doesNotMatch(result.html, /<script\b/i);
  assert.match(result.instructions, /0\.3\.0-alpha\.4/);
  assert.match(result.instructions, /self-host/i);
});

test('provides appropriate admin markup and an integration-specific handoff', () => {
  const result = createStarter({ kind: 'admin', theme: 'grid', stack: 'go' });
  assert.match(result.html, /data-syn-theme="grid"/);
  assert.match(result.html, /Operations console/);
  assert.match(result.html, /href="#tasks"/);
  assert.match(result.instructions, /html\/template/);
  const react = createStarter({ kind: 'business', theme: 'noir', stack: 'react' });
  assert.match(react.html, /Contact/);
  assert.match(react.instructions, /className/);
});

test('does not interpolate untrusted arbitrary values into generated HTML', () => {
  assert.throws(() => createStarter({ kind: '<img src=x>', theme: 'studio', stack: 'html' }), /Unsupported/);
  assert.throws(() => createStarter({ kind: 'saas', theme: 'themed" onload="alert(1)', stack: 'html' }), /Unsupported/);
  assert.throws(() => createStarter({ kind: 'saas', theme: 'studio', stack: 'unexpected' }), /Unsupported/);
});

test('starter handoff carries only validated choices and preserves editable fragment', () => {
  const starter = createStarter({kind:'business', theme:'noir', stack:'react'});
  assert.match(starter.fragment, /Contact us/);
  assert.doesNotMatch(starter.fragment, /<html|<script/i);
  const href = createPlaygroundHandoff({kind:'business', theme:'noir', stack:'react'});
  assert.equal(href, 'playground.html#starter=business&theme=noir&stack=react');
  assert.ok(!href.includes('<'));
  assert.throws(() => createPlaygroundHandoff({kind:'saas', theme:'grid', stack:'http://unsafe'}), /Unsupported/);
});

test('Django and HTMX handoffs use the published CSS and host-owned behavior', () => {
  for (const stack of ['django', 'htmx']) {
    const selection = {kind:'saas', theme:'studio', stack};
    const result = createStarter(selection);
    assert.match(result.html, /href="\.\/syntyr\.core\.css"/);
    assert.doesNotMatch(result.html, /<script\b/i);
    assert.match(result.instructions, stack === 'django' ? /staticfiles/ : /ordinary GET/);
    assert.equal(createPlaygroundHandoff(selection), 'playground.html#starter=saas&theme=studio&stack='+stack);
  }
});
