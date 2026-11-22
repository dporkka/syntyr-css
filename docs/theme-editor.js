/* Optional documentation-only enhancement. Distributed SYNTYR CSS needs no JS. */
(() => {
  const theme = document.getElementById('theme');
  const accent = document.getElementById('accent');
  const intensity = document.getElementById('intensity');
  const density = document.getElementById('density');
  const radius = document.getElementById('radius');
  const generatedPreset = document.getElementById('generated-preset');
  const copyPreset = document.getElementById('copy-preset');
  const presetFeedback = document.getElementById('preset-feedback');
  const onAccent = document.getElementById('on-accent');
  const preview = document.getElementById('preview');
  const contrastResult = document.getElementById('contrast-result');
  const generated = document.getElementById('generated-css');
  const reset = document.getElementById('reset-theme');

  function luminance(hex) {
    const channels = [1, 3, 5].map((index) => parseInt(hex.slice(index, index + 2), 16) / 255);
    const linear = channels.map((value) => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4);
    return linear[0] * 0.2126 + linear[1] * 0.7152 + linear[2] * 0.0722;
  }

  function contrastRatio(first, second) {
    const a = luminance(first);
    const b = luminance(second);
    return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  }

  function render() {
    preview.dataset.synIntensity = intensity.value;
    preview.dataset.synDensity = density.value;
    if (radius.value === 'default') {
      preview.style.removeProperty('--syn-radius');
      preview.style.removeProperty('--syn-panel-radius');
    } else {
      preview.style.setProperty('--syn-radius', radius.value);
      preview.style.setProperty('--syn-panel-radius', radius.value);
    }
    preview.style.setProperty('--syn-accent', accent.value);
    preview.style.setProperty('--syn-on-accent', onAccent.value);
    const ratio = contrastRatio(accent.value, onAccent.value);
    const passes = ratio >= 4.5;
    contrastResult.dataset.result = passes ? 'pass' : 'fail';
    contrastResult.textContent = `Primary button text contrast: ${ratio.toFixed(2)}:1 — ${passes ? 'meets' : 'below'} the WCAG AA normal-text 4.5:1 threshold.`;
    const radiusCss = radius.value === 'default' ? '' : `\n  --syn-radius: ${radius.value};\n  --syn-panel-radius: ${radius.value};`;
    generated.textContent = `/* Set data-syn-intensity="${intensity.value}" and data-syn-density="${density.value}" on your Syntyr root or nested region. */\n.syn-root[data-syn-theme="${theme.value}"],\n.syn-root [data-syn-theme="${theme.value}"] {\n  --syn-accent: ${accent.value};\n  --syn-on-accent: ${onAccent.value};${radiusCss}\n}`;
    generatedPreset.textContent = JSON.stringify({
      schema_version: 1,
      theme: theme.value,
      intensity: intensity.value,
      density: density.value,
      radius: radius.value,
      tokens: {'--syn-accent': accent.value, '--syn-on-accent': onAccent.value},
    }, null, 2);
  }

  function loadThemeDefaults() {
    preview.dataset.synTheme = theme.value;
    preview.style.removeProperty('--syn-accent');
    preview.style.removeProperty('--syn-on-accent');
    const defaults = getComputedStyle(preview);
    accent.value = defaults.getPropertyValue('--syn-accent').trim();
    onAccent.value = defaults.getPropertyValue('--syn-on-accent').trim();
    render();
  }

  theme.addEventListener('change', loadThemeDefaults);
  intensity.addEventListener('change', render);
  density.addEventListener('change', render);
  radius.addEventListener('change', render);
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
  accent.addEventListener('input', render);
  onAccent.addEventListener('input', render);
  reset.addEventListener('click', loadThemeDefaults);
  loadThemeDefaults();
})();
