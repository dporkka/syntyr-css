/** Optional dev-only compiler smoke. No mobile renderer is exercised here. */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { compile } from "tailwindcss";

const root = new URL("../../", import.meta.url);
const tokens = JSON.parse(readFileSync(new URL("metadata/mobile/syntyr.tokens.json", root), "utf8"));
const cases = [
  ["bg", "background-color", "color-syntyr", "surface"],
  ["border", "border-color", "color-syntyr", "frame"],
  ["bg", "background-color", "color-syntyr", "accent"],
  ["text", "color", "color-syntyr", "text"],
  ["text", "color", "color-syntyr", "on-accent"],
  ["p", "padding", "spacing-syntyr", "3"],
  ["min-h", "min-height", "spacing-syntyr", "control"],
  ["text", "font-size", "text-syntyr", "base"],
  ["text", "font-size", "text-syntyr", "sm"],
  ["rounded", "border-radius", "radius-syntyr", ""],
];
const utility = ([prefix, , , role]) => [prefix, "syntyr", role].filter(Boolean).join("-");
for (const [name, palette] of Object.entries(tokens.themes)) {
  const source = readFileSync(new URL(`integrations/react-native/tailwind/${name}.css`, root), "utf8");
  const compiler = await compile(source + "\n@tailwind utilities;");
  const css = compiler.build(cases.map(utility));
  for (const entry of cases) {
    const [, property, namespace, role] = entry;
    const variable = "--" + [namespace, role].filter(Boolean).join("-");
    assert.ok(css.includes(`.${utility(entry)} {`), `${name}: missing ${utility(entry)}`);
    assert.ok(css.includes(`${property}: var(${variable});`), `${name}: missing ${property} mapping`);
  }
  assert.ok(css.includes(`--color-syntyr-surface: ${palette.colors.surface};`));
  assert.ok(css.includes(`--radius-syntyr: ${palette.radius}px;`));
  console.log(`PASS ${name}: Tailwind v4 utility compilation`);
}
