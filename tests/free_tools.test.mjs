import test from 'node:test';
import assert from 'node:assert/strict';
import {
  normalizeHex, contrastRatio, contrastRatings, bestTextColor,
  themeTokens, fluidClamp
} from '../tools/logic.mjs';

test('contrast: known WCAG black white reference is 21:1', () => {
  assert.equal(contrastRatio('#000', '#FFFFFF'), 21);
  assert.equal(contrastRatio('#fff', '#fff'), 1);
  assert.equal(normalizeHex('#AbC'), '#aabbcc');
});

test('contrast: rejects malformed CSS color tokens', () => {
  for (const value of ['red', '123456', '#12', '#xyz', '#11223344', '']) {
    assert.throws(() => normalizeHex(value), /hex color/i);
  }
});

test('contrast: reports WCAG AA and AAA thresholds accurately', () => {
  assert.deepEqual(contrastRatings(7), { aaNormal: true, aaLarge: true, aaaNormal: true, aaaLarge: true });
  assert.deepEqual(contrastRatings(4.5), { aaNormal: true, aaLarge: true, aaaNormal: false, aaaLarge: true });
  assert.deepEqual(contrastRatings(3), { aaNormal: false, aaLarge: true, aaaNormal: false, aaaLarge: false });
  assert.equal(bestTextColor('#ffffff'), '#000000');
  assert.equal(bestTextColor('#000000'), '#ffffff');
});

test('theme exports only known Syntyr tokens with safe hex values', () => {
  const generated = themeTokens({ theme:'studio', bg:'#080f19', surface:'#111c2b', accent:'#76e7f7' });
  assert.match(generated.css, /\.syn-root\[data-syn-theme="studio"\]/);
  assert.match(generated.css, /--syn-bg: #080f19;/);
  assert.match(generated.css, /--syn-on-accent: #000000;/);
  assert.ok(generated.textContrast >= 4.5);
  assert.ok(generated.buttonContrast >= 4.5);
  assert.throws(() => themeTokens({theme:'evil"]{}', bg:'#fff',surface:'#fff',accent:'#fff'}), /theme/i);
});

test('fluid clamp interpolates correctly at endpoints with a 16px root', () => {
  const value = fluidClamp({ minSize:16, maxSize:32, minViewport:320, maxViewport:1440 });
  assert.match(value, /^clamp\(1rem, calc\(/);
  assert.match(value, /, 2rem\)$/);
  assert.equal(fluidClamp({ minSize:16, maxSize:16, minViewport:320, maxViewport:1440 }), '1rem');
  assert.match(fluidClamp({ minSize:8, maxSize:48, minViewport:320, maxViewport:1440 }), /calc\(-0\.2143rem \+ 3\.5714vw\)/);
  assert.throws(() => fluidClamp({ minSize:32, maxSize:16, minViewport:320, maxViewport:1440 }), /size/i);
  assert.throws(() => fluidClamp({ minSize:16, maxSize:32, minViewport:1440, maxViewport:320 }), /viewport/i);
});
