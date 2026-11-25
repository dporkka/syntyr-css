# Pretext development adapter (optional)

Syntyr's distributed CSS, theme system, and Console Kit do **not** require Pretext or any JavaScript. This integration is for teams that need to predict plain-text line counts at different widths during browser-based development and compare the predictions with browser layout.

## Use in an existing JavaScript test harness

Install [Pretext](https://github.com/chenglou/pretext) in **your own development project** with `npm install --save-dev @chenglou/pretext`. From a browser test module (or your bundler), import:

```js
import * as pretext from "@chenglou/pretext";
import { predictWithPretext } from "./integrations/pretext/audit.mjs";

await document.fonts.ready;
const element = document.querySelector(".syn-root .syn-body");
// Match Pretext’s supported wrapping policy on the sample under test.
element.style.overflowWrap = "break-word";
const report = predictWithPretext(element, pretext);
if (report.status === "measured" && report.differs) {
  console.warn("Review browser vs predictive line breaks:", report);
}
if (report.overflowInline || report.overflowBlock) {
  console.warn("Text may be clipped or overflow its box:", report);
}
```

The adapter obtains computed font size, line height, spacing and **content width**; it calls Pretext's `prepare()` and `layout()` APIs, then compares the predictive line count with the browser's text range rectangles. Unlike Pretext's hot-path reuse pattern, this one-shot adapter prepares on every call: run it for occasional diagnostics, **not** on every animation frame or for many virtualization rows. For high-frequency prediction, cache `prepare()` per text, font and options and call `layout()` for each new width.

Predictions require explicit `overflow-wrap: break-word` and are skipped for rich inline elements, other wrapping policies (including `normal` and `anywhere`), CSS font variations, CSS text transforms, and nonzero word spacing. Width is derived from the untransformed client box minus horizontal padding, so borders, classic scrollbars and transforms do not inflate the available text width. A prediction is **not** an accessibility result or a browser layout guarantee. Also consider language, font fallback, browser minimum font sizes, optical sizing, hyphenation, variable fonts and bidirectional text. Native DOM rendering and browser inspection remain authoritative.

## No dependency leakage

- There is no import from this module in Syntyr's stylesheet build, published CSS, or public playground.
- No npm package is installed or locked by Syntyr for this integration.
- Run its dependency-free contract tests with `node --test tests/pretext_adapter.test.mjs` (optional, developer-only).
- The public [component playground](../../docs/playground.html#typography-title) measures DOM wrapping independently and works without Pretext.
- Pretext has its own licensing and notices; **do not vendor or redistribute its code** without preserving its requirements.

The free core stays CSS-first. Avoid creating a paid stand-alone predictive text engine; evaluate a paid editorial composition pack only if buyers demonstrate demand for design assets rather than a measurement dependency.
