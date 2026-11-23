/* Docs-only preset UI behavior, isolated without browser or npm dependencies. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';

const source = readFileSync(new URL('../docs/theme-editor.js', import.meta.url), 'utf8');

function createEditor({clipboardAvailable = true} = {}) {
  const ids = ['theme', 'intensity', 'density', 'radius', 'accent', 'on-accent',
    'preview', 'contrast-result', 'generated-css', 'generated-preset',
    'copy-preset', 'preset-feedback', 'reset-theme', 'typography', 'spacing',
    'page-bg', 'surface', 'body-text', 'muted-text',
    'contrast-background-result', 'contrast-surface-result', 'contrast-muted-result'];
  const elements = Object.fromEntries(ids.map(id => [id, {
    id, value: '', textContent: '', dataset: {}, listeners: {},
    addEventListener(event, fn) { this.listeners[event] = fn; },
  }]));
  Object.assign(elements.theme, {value: 'grid'});
  Object.assign(elements.intensity, {value: 'standard'});
  Object.assign(elements.density, {value: 'comfortable'});
  Object.assign(elements.radius, {value: 'default'});
  Object.assign(elements.typography, {value: 'system'});
  Object.assign(elements.spacing, {value: 'balanced'});
  Object.assign(elements.accent, {value: '#76e7f7'});
  Object.assign(elements['on-accent'], {value: '#07121a'});
  const styles = new Map();
  elements.preview.style = {
    setProperty(name, value) { styles.set(name, value); },
    removeProperty(name) { styles.delete(name); },
  };
  const selection = {selected: false, removeAllRanges() {}, addRange() { this.selected = true; }};
  const copied = [];
  const document = {
    getElementById(id) { assert.ok(elements[id], id); return elements[id]; },
    createRange() { return {selectNodeContents() {}}; },
  };
  const navigator = clipboardAvailable
    ? {clipboard: {async writeText(text) { copied.push(text); }}}
    : {};
  runInNewContext(source, {
    document, navigator, window: {getSelection() { return selection; }},
    getComputedStyle() {
      return {getPropertyValue(name) {
        return ({'--syn-accent': '#76e7f7', '--syn-on-accent': '#07121a',
          '--syn-bg':'#080f19', '--syn-surface':'#111f2c',
          '--syn-text':'#edf9ff', '--syn-muted':'#adbfca'})[name] || '#07121a';
      }};
    },
  });
  return {elements, styles, copied, selection};
}

test('preset export tracks density, radius, intensity and colors as configuration', () => {
  const {elements, styles} = createEditor();
  assert.equal(elements.preview.dataset.synDensity, 'comfortable');
  elements.density.value = 'compact';
  elements.density.listeners.change();
  elements.radius.value = '0.75rem';
  elements.radius.listeners.change();
  elements.intensity.value = 'quiet';
  elements.intensity.listeners.change();
  elements.accent.value = '#abcdef';
  elements.accent.listeners.input();

  const preset = JSON.parse(elements['generated-preset'].textContent);
  assert.equal(preset.schema_version, 1);
  assert.equal(preset.theme, 'grid');
  assert.equal(preset.density, 'compact');
  assert.equal(preset.radius, '0.75rem');
  assert.equal(preset.intensity, 'quiet');
  assert.equal(preset.tokens['--syn-accent'], '#abcdef');
  assert.equal(elements.preview.dataset.synDensity, 'compact');
  assert.equal(styles.get('--syn-radius'), '0.75rem');
  assert.equal(styles.get('--syn-panel-radius'), '0.75rem');
  assert.match(elements['generated-css'].textContent, /data-syn-density="compact"/);
  assert.match(elements['generated-css'].textContent, /--syn-panel-radius: 0\.75rem/);

  elements.radius.value = 'default';
  elements.radius.listeners.change();
  assert.equal(styles.has('--syn-radius'), false);
  assert.doesNotMatch(elements['generated-css'].textContent, /--syn-panel-radius:/);
});

test('copy button copies exactly the generated JSON', async () => {
  const {elements, copied} = createEditor();
  await elements['copy-preset'].listeners.click();
  assert.deepEqual(copied, [elements['generated-preset'].textContent]);
  assert.equal(elements['preset-feedback'].textContent, 'Preset JSON copied.');
});

test('copy button selects JSON for manual copying when clipboard is unavailable', async () => {
  const {elements, selection} = createEditor({clipboardAvailable: false});
  await elements['copy-preset'].listeners.click();
  assert.equal(selection.selected, true);
  assert.match(elements['preset-feedback'].textContent, /keyboard to copy/);
});


test('semantic page colors update preview, JSON and all scoped CSS output', () => {
  const {elements, styles} = createEditor();
  const cases = [
    ['page-bg', '--syn-bg', '#101820'],
    ['surface', '--syn-surface', '#253247'],
    ['body-text', '--syn-text', '#ffffff'],
    ['muted-text', '--syn-muted', '#eeeeee'],
  ];
  for (const [id, token, color] of cases) {
    elements[id].value = color;
    elements[id].listeners.input();
    assert.equal(styles.get(token), color);
    assert.equal(JSON.parse(elements['generated-preset'].textContent).tokens[token], color);
    assert.ok(elements['generated-css'].textContent.includes(token + ': ' + color));
  }
  assert.equal(elements['contrast-background-result'].dataset.result, 'pass');
  assert.equal(elements['contrast-surface-result'].dataset.result, 'pass');
  assert.equal(elements['contrast-muted-result'].dataset.result, 'pass');
  elements['body-text'].value = '#253247';
  elements['body-text'].listeners.input();
  assert.equal(elements['contrast-surface-result'].dataset.result, 'fail');
  elements['page-bg'].value = '#253247';
  elements['page-bg'].listeners.input();
  assert.equal(elements['contrast-background-result'].dataset.result, 'fail');
  assert.match(elements['contrast-surface-result'].textContent, /1\.00:1/);

  elements.theme.value = 'noir';
  elements.theme.listeners.change();
  assert.notEqual(elements['surface'].value, '#253247', 'Theme switch restores the new palette defaults');
});

test('typography and spacing presets export token-only overrides without external fonts', () => {
  const {elements, styles} = createEditor();
  elements.typography.value = 'editorial';
  elements.typography.listeners.change();
  elements.spacing.value = 'airy';
  elements.spacing.listeners.change();
  const preset = JSON.parse(elements['generated-preset'].textContent);
  assert.equal(preset.typography, 'editorial');
  assert.equal(preset.spacing, 'airy');
  assert.match(preset.tokens['--syn-font-display'], /Georgia/);
  assert.match(preset.tokens['--syn-font'], /system-ui/);
  assert.equal(preset.tokens['--syn-space-3'], '1.5rem');
  assert.equal(styles.get('--syn-space-3'), '1.5rem');
  assert.ok(elements['generated-css'].textContent.includes('--syn-font-display: Georgia'));
  assert.ok(elements['generated-css'].textContent.includes('--syn-space-3: 1.5rem'));
  assert.doesNotMatch(elements['generated-css'].textContent, /@import|url\(/);
  elements.spacing.value = 'balanced';
  elements.spacing.listeners.change();
  assert.equal(styles.has('--syn-space-3'), false, 'Balanced spacing defers to the base theme');
  elements.typography.value = 'system';
  elements.typography.listeners.change();
  assert.equal(styles.has('--syn-font-display'), false);
});
