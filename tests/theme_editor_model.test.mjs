/* Docs-only preset UI behavior, isolated without browser or npm dependencies. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';

const source = readFileSync(new URL('../docs/theme-editor.js', import.meta.url), 'utf8');

function createEditor({clipboardAvailable = true} = {}) {
  const ids = ['theme', 'intensity', 'density', 'radius', 'accent', 'on-accent',
    'preview', 'contrast-result', 'generated-css', 'generated-preset',
    'copy-preset', 'preset-feedback', 'reset-theme'];
  const elements = Object.fromEntries(ids.map(id => [id, {
    id, value: '', textContent: '', dataset: {}, listeners: {},
    addEventListener(event, fn) { this.listeners[event] = fn; },
  }]));
  Object.assign(elements.theme, {value: 'grid'});
  Object.assign(elements.intensity, {value: 'standard'});
  Object.assign(elements.density, {value: 'comfortable'});
  Object.assign(elements.radius, {value: 'default'});
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
        return name === '--syn-accent' ? '#76e7f7' : '#07121a';
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
