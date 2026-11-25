/* Optional docs-only editor. Exported sites and Syntyr CSS never run this script. */
(() => {
  const byId = id => document.getElementById(id);
  const theme = byId('theme');
  const intensity = byId('intensity');
  const density = byId('density');
  const radius = byId('radius');
  const typography = byId('typography');
  const spacing = byId('spacing');
  const generatedPreset = byId('generated-preset');
  const copyPreset = byId('copy-preset');
  const presetFeedback = byId('preset-feedback');
  const preview = byId('preview');
  const contrastResult = byId('contrast-result');
  const surfaceContrastResult = byId('contrast-surface-result');
  const backgroundContrastResult = byId('contrast-background-result');
  const mutedContrastResult = byId('contrast-muted-result');
  const generated = byId('generated-css');
  const reset = byId('reset-theme');

  const colors = Object.freeze({
    '--syn-accent': byId('accent'),
    '--syn-on-accent': byId('on-accent'),
    '--syn-bg': byId('page-bg'),
    '--syn-surface': byId('surface'),
    '--syn-text': byId('body-text'),
    '--syn-muted': byId('muted-text')
  });
  // System-installed font stacks only. No network, hosted fonts, or runtime dependency.
  const fonts = Object.freeze({
    system: {},
    editorial: {
      '--syn-font': 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      '--syn-font-ui': 'var(--syn-font)',
      '--syn-font-display': 'Georgia, "Times New Roman", serif'
    },
    technical: {
      '--syn-font': 'ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace',
      '--syn-font-ui': 'var(--syn-font)',
      '--syn-font-display': 'var(--syn-font)'
    }
  });
  // Spacing controls the site's rhythm; density separately controls form/table ergonomics.
  const rhythm = Object.freeze({
    balanced: null,
    tight: ['.25rem', '.5rem', '.75rem', '1.25rem', '1.75rem'],
    airy: ['.5rem', '1rem', '1.5rem', '2.25rem', '3.25rem']
  });
  const adjustableTokens = [
    '--syn-radius', '--syn-panel-radius', '--syn-font', '--syn-font-ui',
    '--syn-font-display', ...Array.from({length: 5}, (_, index) => '--syn-space-' + (index + 1))
  ];

  function luminance(hex) {
    const channels = [1, 3, 5].map(index => parseInt(hex.slice(index, index + 2), 16) / 255);
    const linear = channels.map(value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4);
    return linear[0] * .2126 + linear[1] * .7152 + linear[2] * .0722;
  }

  function contrastRatio(first, second) {
    const a = luminance(first);
    const b = luminance(second);
    return (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
  }

  function reportContrast(node, label, foreground, background) {
    const ratio = contrastRatio(foreground, background);
    const passes = ratio >= 4.5;
    node.dataset.result = passes ? 'pass' : 'fail';
    node.textContent = label + ': ' + ratio.toFixed(2) + ':1 — ' +
      (passes ? 'meets' : 'below') + ' the WCAG AA normal-text 4.5:1 threshold.';
  }

  function render() {
    preview.dataset.synIntensity = intensity.value;
    preview.dataset.synDensity = density.value;
    const selectedFont = fonts[typography.value] || fonts.system;
    const selectedRhythm = rhythm[spacing.value] || null;
    const tokens = {};
    for (const [token, input] of Object.entries(colors)) {
      tokens[token] = input.value;
      preview.style.setProperty(token, input.value);
    }
    for (const token of adjustableTokens) preview.style.removeProperty(token);
    if (radius.value !== 'default') {
      tokens['--syn-radius'] = radius.value;
      tokens['--syn-panel-radius'] = radius.value;
    }
    Object.assign(tokens, selectedFont);
    if (selectedRhythm) {
      selectedRhythm.forEach((value, index) => {
        tokens['--syn-space-' + (index + 1)] = value;
      });
    }
    for (const [token, value] of Object.entries(tokens)) preview.style.setProperty(token, value);
    reportContrast(contrastResult, 'Primary button text contrast',
      colors['--syn-on-accent'].value, colors['--syn-accent'].value);
    reportContrast(backgroundContrastResult, 'Body text on page background',
      colors['--syn-text'].value, colors['--syn-bg'].value);
    reportContrast(surfaceContrastResult, 'Body text on surface',
      colors['--syn-text'].value, colors['--syn-surface'].value);
    reportContrast(mutedContrastResult, 'Muted text on surface',
      colors['--syn-muted'].value, colors['--syn-surface'].value);
    // Fixed selector values and typed color inputs; no imported CSS or user HTML.
    const selector = '.syn-root[data-syn-theme="' + theme.value +
      '"],\n.syn-root [data-syn-theme="' + theme.value + '"]';
    const declarations = Object.entries(tokens).map(([key, value]) => '  ' + key + ': ' + value + ';');
    generated.textContent = '/* Set data-syn-intensity="' + intensity.value +
      '" and data-syn-density="' + density.value + '" on your Syntyr scope. */\n' +
      selector + ' {\n' + declarations.join('\n') + '\n}';
    generatedPreset.textContent = JSON.stringify({
      schema_version: 1, theme: theme.value,
      intensity: intensity.value, density: density.value, radius: radius.value,
      typography: typography.value, spacing: spacing.value, tokens
    }, null, 2);
  }

  function loadThemeDefaults() {
    preview.dataset.synTheme = theme.value;
    for (const token of Object.keys(colors)) preview.style.removeProperty(token);
    const defaults = getComputedStyle(preview);
    for (const [token, input] of Object.entries(colors)) {
      input.value = defaults.getPropertyValue(token).trim();
    }
    render();
  }

  theme.addEventListener('change', loadThemeDefaults);
  for (const select of [intensity, density, radius, typography, spacing])
    select.addEventListener('change', render);
  for (const input of Object.values(colors)) input.addEventListener('input', render);
  reset.addEventListener('click', loadThemeDefaults);
  copyPreset.addEventListener('click', async () => {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(generatedPreset.textContent);
      presetFeedback.textContent = 'Preset JSON copied.';
    } catch {
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(generatedPreset);
      selection.removeAllRanges();
      selection.addRange(range);
      presetFeedback.textContent = 'Preset selected. Use your keyboard to copy it.';
    }
  });
  loadThemeDefaults();
})();
