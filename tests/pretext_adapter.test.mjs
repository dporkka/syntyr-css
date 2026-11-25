import assert from "node:assert/strict";
import test from "node:test";
import { inspectText, predictWithPretext } from "../integrations/pretext/audit.mjs";

const css = {
  fontSize: "16px", fontFamily: '"Inter", sans-serif', fontStyle: "normal",
  fontWeight: "400", lineHeight: "24px", letterSpacing: "normal",
  whiteSpace: "normal", wordBreak: "normal", overflowWrap: "break-word",
  paddingLeft: "8px", paddingRight: "8px", borderLeftWidth: "1px",
  borderRightWidth: "1px", textWrapStyle: "auto", fontVariationSettings: "normal",
  fontFeatureSettings: "normal"
};
function element(overrides = {}, styles = {}) {
  const rects = overrides.rects || [{top: 2, bottom: 18}, {top: 26, bottom: 42}];
  return {
    textContent: "Syntyr a readable label", childElementCount: 0,
    scrollWidth: 216, clientWidth: 216, scrollHeight: 48, clientHeight: 48,
    getBoundingClientRect: () => ({width: 218, height: 48}),
    ownerDocument: {
      defaultView: {getComputedStyle: () => ({...css, ...styles})},
      createRange: () => ({selectNodeContents() {}, getClientRects: () => rects})
    },
    ...overrides
  };
}
test("reports distinct visual text lines and horizontal overflow", () => {
  const result = inspectText(element({scrollWidth: 243}));
  assert.equal(result.actualLines, 2);
  assert.equal(result.overflowInline, true);
  assert.equal(result.overflowBlock, false);
});
test("pretext predictor consumes content width rather than border-box width", () => {
  let prepared, layoutArgs;
  const pretext = {
    prepare: (...args) => { prepared = args; return "handle"; },
    layout: (...args) => { layoutArgs = args; return {lineCount: 2, height: 48}; }
  };
  const result = predictWithPretext(element(), pretext);
  assert.equal(result.status, "measured");
  assert.deepEqual(layoutArgs, ["handle", 200, 24]);
  assert.equal(prepared[0], "Syntyr a readable label");
  assert.equal(prepared[2].wordBreak, "normal");
});
test("skips unsupported balanced wrapping rather than declaring false mismatch", () => {
  const result = predictWithPretext(element({}, {textWrapStyle: "balance"}), {
    prepare: () => { throw new Error("must not run"); }, layout: () => {}
  });
  assert.equal(result.status, "skipped");
});
test("skips rich inline content, where layout has different assumptions", () => {
  const result = predictWithPretext(element({childElementCount: 1}), {
    prepare: () => { throw new Error("must not run"); }, layout: () => {}
  });
  assert.equal(result.status, "skipped");
});

test("uses untransformed client width excluding scrollbar space and padding", () => {
  const pretext = {
    prepare: () => "handle",
    layout: (_handle, width) => { assert.equal(width, 169); return {lineCount: 2, height: 48}; }
  };
  const result = predictWithPretext(element({clientWidth: 185, getBoundingClientRect: () => ({width: 400, height: 48})}), pretext);
  assert.equal(result.contentWidth, 169);
});
test("skips normal overflow-wrap for a long identifier", () => {
  const result = predictWithPretext(element({textContent: "a".repeat(100)}, {overflowWrap: "normal"}), {
    prepare: () => { throw new Error("must not predict"); }, layout: () => {}
  });
  assert.equal(result.status, "skipped");
  assert.equal(result.reason, "unsupported-overflow-wrap");
});

test("groups mixed-font fragments on one visual line without merging adjacent lines", () => {
  const rects = [{top: 2, bottom: 18}, {top: 4, bottom: 20}, {top: 0, bottom: 22}, {top: 26, bottom: 42}];
  assert.equal(inspectText(element({rects})).actualLines, 2);
});
test("skips CSS text transformation and nondefault word spacing", () => {
  const pretext = {prepare: () => { throw new Error("must not predict"); }, layout: () => {}};
  for (const [styles, reason] of [
    [{textTransform: "uppercase"}, "unsupported-text-transform"],
    [{wordSpacing: "40px"}, "unsupported-word-spacing"]
  ]) {
    const report = predictWithPretext(element({}, styles), pretext);
    assert.equal(report.status, "skipped");
    assert.equal(report.reason, reason);
  }
});
test("accepts explicit zero word spacing and untransformed text", () => {
  const pretext = {prepare: () => "handle", layout: () => ({lineCount: 2, height: 48})};
  assert.equal(predictWithPretext(element({}, {textTransform: "none", wordSpacing: "0px"}), pretext).status, "measured");
});

test("counts tightly spaced adjacent lines even when glyph rectangles overlap", () => {
  const rects = [{top: 0, bottom: 40}, {top: 10, bottom: 50}];
  assert.equal(inspectText(element({rects}, {fontSize: "40px", lineHeight: "10px"})).actualLines, 2);
});

test("declines ambiguous mixed-font line counts when line boxes are shorter than glyphs", () => {
  const rects = [{top: 2, bottom: 18}, {top: 4, bottom: 20}, {top: 0, bottom: 22}];
  const sample = element({rects}, {fontSize: "16px", lineHeight: "4px"});
  assert.equal(inspectText(sample).actualLines, null);
  const result = predictWithPretext(sample, {
    prepare: () => { throw new Error("must not predict ambiguous layout"); }, layout: () => {}
  });
  assert.equal(result.status, "skipped");
  assert.equal(result.reason, "ambiguous-line-fragments");
});
