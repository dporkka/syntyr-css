// Optional browser enhancements on Syntyr's static tools landing pages.
// The Syntyr CSS distribution is entirely usable without this script.
import { normalizeHex, contrastRatio, contrastRatings, bestTextColor, themeTokens, fluidClamp } from './logic.mjs';

const byId = (id) => document.getElementById(id);
const decimal = (number) => number.toFixed(2);
const status = (element, message, result) => {
  element.textContent = message;
  if (result) element.dataset.result = result;
  else delete element.dataset.result;
};

async function copyOutput(sourceId, statusId) {
  const feedback = byId(statusId);
  try {
    if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
    await navigator.clipboard.writeText(byId(sourceId).textContent);
    status(feedback, 'Copied to clipboard.', 'pass');
  } catch {
    status(feedback, 'Clipboard unavailable. Select and copy the code above.', 'fail');
  }
}

function bindCopy() {
  for (const button of document.querySelectorAll('[data-copy]')) {
    button.addEventListener('click', () => copyOutput(button.dataset.copy, button.dataset.feedback));
  }
}

function setupContrast() {
  const foreground = byId('foreground');
  const background = byId('background');
  const preview = byId('contrast-preview');
  const ratioLabel = byId('contrast-ratio');
  const outcomes = byId('contrast-outcomes');
  const css = byId('contrast-code');
  const explain = byId('contrast-explain');
  function render() {
    try {
      const fg = normalizeHex(foreground.value);
      const bg = normalizeHex(background.value);
      const ratio = contrastRatio(fg, bg);
      const passes = contrastRatings(ratio);
      preview.style.color = fg;
      preview.style.backgroundColor = bg;
      ratioLabel.textContent = `${decimal(ratio)}:1 contrast ratio`;
      status(explain, passes.aaNormal
        ? 'Passes WCAG 2.2 AA minimum contrast for normal text (color pair only).'
        : 'Below WCAG 2.2 AA for normal text. Try the recommended text color.', passes.aaNormal ? 'pass' : 'fail');
      const options = [
        ['AA normal text', passes.aaNormal, '4.5:1 minimum'],
        ['AA large text', passes.aaLarge, '3:1 minimum'],
        ['AAA normal text', passes.aaaNormal, '7:1 minimum'],
        ['AAA large text', passes.aaaLarge, '4.5:1 minimum']
      ];
      outcomes.replaceChildren(...options.map(([name, pass, threshold]) => {
        const li = document.createElement('li');
        li.dataset.pass = String(pass);
        li.append(document.createTextNode(`${pass ? 'Pass' : 'Fail'} · ${name}`));
        const note = document.createElement('span');
        note.textContent = threshold;
        li.append(note);
        return li;
      }));
      css.textContent = `/* CSS color pair — test in the actual UI. */\ncolor: ${fg};\nbackground-color: ${bg};`;
    } catch (error) {
      status(explain, error.message, 'fail');
    }
  }
  byId('contrast-suggest').addEventListener('click', () => {
    foreground.value = bestTextColor(background.value);
    render();
  });
  foreground.addEventListener('input', render);
  background.addEventListener('input', render);
  render();
}

function setupTheme() {
  const form = byId('theme-form');
  const preview = byId('theme-preview');
  const output = byId('theme-code');
  const report = byId('theme-report');
  function render() {
    try {
      const result = themeTokens({
        theme: byId('theme-base').value,
        bg: byId('theme-bg').value,
        surface: byId('theme-surface').value,
        accent: byId('theme-accent').value
      });
      preview.dataset.synTheme = byId('theme-base').value;
      for (const [token, value] of [
        ['--syn-bg', byId('theme-bg').value],
        ['--syn-surface', byId('theme-surface').value],
        ['--syn-text', result.text],
        ['--syn-accent', byId('theme-accent').value],
        ['--syn-on-accent', result.onAccent]
      ]) preview.style.setProperty(token, value);
      output.textContent = result.css;
      const pass = result.surfaceContrast >= 4.5;
      status(report, `Text on background: ${decimal(result.textContrast)}:1 · text on surface: ${decimal(result.surfaceContrast)}:1 · button text: ${decimal(result.buttonContrast)}:1. ${pass ? 'These pairs meet AA normal-text contrast.' : 'Surface text is below AA normal-text contrast; adjust the surface color.'}`, pass ? 'pass' : 'fail');
    } catch (error) {
      status(report, error.message, 'fail');
    }
  }
  form.addEventListener('input', render);
  form.addEventListener('change', render);
  render();
}

function setupClamp() {
  const form = byId('clamp-form');
  const result = byId('clamp-code');
  const preview = byId('clamp-preview');
  const feedback = byId('clamp-report');
  function render() {
    try {
      const value = fluidClamp({
        minSize: byId('min-size').value,
        maxSize: byId('max-size').value,
        minViewport: byId('min-viewport').value,
        maxViewport: byId('max-viewport').value,
      });
      result.textContent = `/* Paste into any stylesheet. Assumes a 16px root font size. */\n.fluid-heading {\n  font-size: ${value};\n}`;
      preview.style.fontSize = value;
      status(feedback, `Generated: ${value}`, 'pass');
    } catch (error) {
      result.textContent = 'Enter valid minimum and maximum values to generate CSS.';
      status(feedback, error.message, 'fail');
    }
  }
  form.addEventListener('input', render);
  render();
}

function setupResponsive() {
  const viewport = byId('viewport-width');
  const preset = byId('viewport-preset');
  const frame = byId('responsive-frame');
  const editor = byId('responsive-html');
  const report = byId('responsive-report');
  function resize() {
    const size = Number(viewport.value);
    if (!Number.isInteger(size) || size < 240 || size > 1920) {
      status(report, 'Choose a width between 240px and 1920px.', 'fail');
      return;
    }
    frame.style.width = `${size}px`;
    status(report, `Preview viewport: ${size}px. Scroll horizontally to inspect wider breakpoints.`, 'pass');
  }
  function render() {
    const snippet = editor.value;
    // A sandbox with no allow-* tokens blocks scripts, forms and top navigation.
    // The inherited site CSP also prevents third-party resources and connections.
    frame.srcdoc = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="/dist/syntyr.core.css"><style>body{margin:0;padding:1rem}img{max-width:100%}</style></head><body class="syn-root syn-page" data-syn-theme="studio">${snippet}</body></html>`;
    resize();
  }
  preset.addEventListener('change', () => { viewport.value = preset.value; resize(); });
  viewport.addEventListener('input', () => { preset.value = ''; resize(); });
  editor.addEventListener('input', render);
  render();
}

bindCopy();
const tool = document.body.dataset.tool;
if (tool === 'contrast') setupContrast();
if (tool === 'theme') setupTheme();
if (tool === 'clamp') setupClamp();
if (tool === 'responsive') setupResponsive();
