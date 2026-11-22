// Browser-only utilities for the optional Syntyr free-tools pages.
// No network requests, external packages, or dependency on Syntyr's runtime.
export function normalizeHex(value) {
  if (typeof value !== 'string' || !/^#(?:[\da-f]{3}|[\da-f]{6})$/i.test(value)) {
    throw new TypeError('Enter a hex color (#RGB or #RRGGBB).');
  }
  const digits = value.slice(1).toLowerCase();
  return '#' + (digits.length === 3 ? [...digits].map((part) => part + part).join('') : digits);
}

function channel(value) {
  const srgb = value / 255;
  return srgb <= 0.04045 ? srgb / 12.92 : ((srgb + 0.055) / 1.055) ** 2.4;
}

export function luminance(hex) {
  const color = normalizeHex(hex);
  const red = channel(parseInt(color.slice(1, 3), 16));
  const green = channel(parseInt(color.slice(3, 5), 16));
  const blue = channel(parseInt(color.slice(5, 7), 16));
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
}

export function contrastRatio(first, second) {
  const a = luminance(first);
  const b = luminance(second);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}

export function contrastRatings(ratio) {
  if (!Number.isFinite(ratio) || ratio < 1 || ratio > 21) throw new RangeError('Invalid contrast ratio.');
  const meets = (threshold) => ratio + 1e-10 >= threshold;
  return { aaNormal: meets(4.5), aaLarge: meets(3), aaaNormal: meets(7), aaaLarge: meets(4.5) };
}

export function bestTextColor(background) {
  return contrastRatio('#000000', background) >= contrastRatio('#ffffff', background)
    ? '#000000' : '#ffffff';
}

const THEMES = new Set(['studio', 'noir', 'grid', 'minimal', 'industrial', 'corporate', 'terminal']);

export function themeTokens({ theme = 'studio', bg, surface, accent }) {
  if (!THEMES.has(theme)) throw new TypeError('Unsupported Syntyr base theme.');
  const background = normalizeHex(bg);
  const surfaceColor = normalizeHex(surface);
  const accentColor = normalizeHex(accent);
  const text = bestTextColor(background);
  const onAccent = bestTextColor(accentColor);
  const textContrast = contrastRatio(background, text);
  const surfaceContrast = contrastRatio(surfaceColor, text);
  const buttonContrast = contrastRatio(accentColor, onAccent);
  const css = `/* Add after Syntyr CSS. Preview uses the unreleased source candidate. */
/* Verify links, borders, focus indicators and interactive states separately. */
.syn-root[data-syn-theme="${theme}"] {
  --syn-bg: ${background};
  --syn-surface: ${surfaceColor};
  --syn-text: ${text};
  --syn-accent: ${accentColor};
  --syn-on-accent: ${onAccent};
}`;
  return { css, text, onAccent, textContrast, surfaceContrast, buttonContrast };
}

function finite(value, label) {
  const n = typeof value === 'number' ? value : Number(value);
  if (!Number.isFinite(n)) throw new TypeError(`Enter a valid ${label}.`);
  return n;
}

function format(number) {
  const value = Math.round(number * 10000) / 10000;
  return String(Object.is(value, -0) ? 0 : value);
}

export function fluidClamp({ minSize, maxSize, minViewport, maxViewport, rootSize = 16 }) {
  const min = finite(minSize, 'minimum size');
  const max = finite(maxSize, 'maximum size');
  const vMin = finite(minViewport, 'minimum viewport');
  const vMax = finite(maxViewport, 'maximum viewport');
  const root = finite(rootSize, 'root size');
  if (min <= 0 || max < min || max > 512) throw new RangeError('Invalid size range: use 0 < minimum <= maximum <= 512 px.');
  if (vMin < 240 || vMax <= vMin || vMax > 7680) throw new RangeError('Invalid viewport range: use 240 <= minimum < maximum <= 7680 px.');
  if (root < 8 || root > 32) throw new RangeError('Root size must be 8 to 32 px.');
  if (max === min) return `${format(min / root)}rem`;
  const slope = (max - min) / (vMax - vMin);
  const intercept = (min - slope * vMin) / root;
  // A negative intercept must remain negative; the vw coefficient is positive.
  const middle = `${format(intercept)}rem + ${format(slope * 100)}vw`;
  return `clamp(${format(min / root)}rem, calc(${middle}), ${format(max / root)}rem)`;
}
