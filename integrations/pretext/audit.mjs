/**
 * Optional developer-only Pretext adapter. Never imported by Syntyr CSS.
 * Supply an installed @chenglou/pretext namespace from your own build tool.
 * Browser DOM metrics are authoritative; predictions are advisory.
 */
export function inspectText(element) {
  if (!element?.ownerDocument?.createRange) throw new TypeError("Expected a browser Element");
  const range = element.ownerDocument.createRange();
  range.selectNodeContents(element);
  // Font fallback may give fragments on one line different top coordinates.
  // Group overlapping text bands using their midpoints, not exact tops.
  const lineHeight = Number.parseFloat(element.ownerDocument.defaultView.getComputedStyle(element).lineHeight);
  const halfLine = Number.isFinite(lineHeight) && lineHeight > 0 ? lineHeight / 2 : Infinity;
  const bands = [];
  const fragments = Array.from(range.getClientRects(), rect => ({
    center: (rect.top + rect.bottom) / 2, height: rect.bottom - rect.top
  })).filter(rect => rect.height > 0).sort((a, b) => a.center - b.center);
  // Range rectangles do not expose line-box identity. Avoid false precision
  // when unusually short line boxes overlap mixed font metrics.
  const ambiguous = Number.isFinite(lineHeight) && fragments.some(f => f.height > lineHeight) &&
    fragments.some(f => Math.abs(f.height - fragments[0].height) > 0.5);
  for (const fragment of fragments) {
    const band = bands[bands.length - 1];
    if (!band || fragment.center - band.center >= Math.min(fragment.height / 2, band.height / 2, halfLine))
      bands.push(fragment);
  }
  return {
    actualLines: element.textContent?.length ? (ambiguous ? null : bands.length) : 0,
    height: element.getBoundingClientRect().height,
    overflowInline: element.scrollWidth > element.clientWidth + 1,
    overflowBlock: element.scrollHeight > element.clientHeight + 1
  };
}

function skip(reason, measured) {
  return {status: "skipped", reason, ...measured};
}

/** Run only for ordinary, single-font text. Rich content needs a rich-inline API. */
export function predictWithPretext(element, pretext) {
  const measured = inspectText(element);
  if (!pretext || typeof pretext.prepare !== "function" || typeof pretext.layout !== "function")
    throw new TypeError("Supply the @chenglou/pretext module");
  if (element.childElementCount) return skip("rich-inline-content", measured);
  if (measured.actualLines === null) return skip("ambiguous-line-fragments", measured);
  const style = element.ownerDocument.defaultView.getComputedStyle(element);
  if (!["normal", "pre-wrap"].includes(style.whiteSpace))
    return skip("unsupported-white-space", measured);
  if (!["normal", "keep-all"].includes(style.wordBreak))
    return skip("unsupported-word-break", measured);
  if (style.overflowWrap !== "break-word")
    return skip("unsupported-overflow-wrap", measured);
  if (["balance", "pretty"].includes(style.textWrapStyle) ||
      /\b(balance|pretty)\b/.test(style.textWrap || ""))
    return skip("browser-text-wrap-optimization", measured);
  if (style.textTransform && style.textTransform !== "none")
    return skip("unsupported-text-transform", measured);
  if (style.wordSpacing && style.wordSpacing !== "normal" && Number.parseFloat(style.wordSpacing) !== 0)
    return skip("unsupported-word-spacing", measured);
  if (style.fontVariationSettings && style.fontVariationSettings !== "normal")
    return skip("font-variation-settings", measured);
  if (style.fontFeatureSettings && style.fontFeatureSettings !== "normal")
    return skip("font-feature-settings", measured);
  const lineHeight = Number.parseFloat(style.lineHeight);
  const fontSize = Number.parseFloat(style.fontSize);
  const letterSpacing = style.letterSpacing === "normal" ? 0 : Number.parseFloat(style.letterSpacing);
  if (![lineHeight, fontSize, letterSpacing].every(Number.isFinite) || lineHeight <= 0 || fontSize <= 0)
    return skip("unresolved-font-metrics", measured);
  // clientWidth excludes transforms, borders, and classic scrollbar space.
  const contentWidth = element.clientWidth - ["paddingLeft", "paddingRight"]
    .reduce((sum, key) => sum + (Number.parseFloat(style[key]) || 0), 0);
  if (contentWidth <= 0) return skip("no-content-width", measured);
  const font = `${style.fontStyle || "normal"} ${style.fontWeight || "400"} ${style.fontSize} ${style.fontFamily}`;
  const prepared = pretext.prepare(element.textContent || "", font, {
    whiteSpace: style.whiteSpace, wordBreak: style.wordBreak, letterSpacing
  });
  const result = pretext.layout(prepared, contentWidth, lineHeight);
  return {
    status: "measured", ...measured, predictedLines: result.lineCount,
    predictedHeight: result.height, contentWidth,
    differs: result.lineCount !== measured.actualLines
  };
}
