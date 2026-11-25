import assert from "node:assert/strict";
import { test } from "node:test";
import { createElement as h } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { Badge, Button, Card, Input, Select, SyntyrRoot, Textarea } from "../dist/index.js";

test("SSR renders theme scope and native controls", () => {
  const html = renderToStaticMarkup(
    h(SyntyrRoot, { theme: "noir", id: "app" },
      h(Card, { elevated: true },
        h(Badge, { accent: true }, "Active"),
        h(Button, { variant: "primary", "aria-label": "Save" }, "Save"))),
  );
  for (const part of ['class="syn-root"', 'data-syn-theme="noir"',
    'class="syn-panel syn-panel--raised"', 'class="syn-badge syn-badge--accent"',
    'class="syn-button syn-button--primary"', 'type="button"']) {
    assert.ok(html.includes(part), part);
  }
});
test("button preserves native submission, disabled state, app classes", () => {
  const html = renderToStaticMarkup(
    h(Button, { type: "submit", disabled: true, className: "customer-save" }, "Save"));
  assert.match(html, /type="submit"/);
  assert.match(html, /disabled=""/);
  assert.match(html, /class="syn-button customer-save"/);
});
test("form fields preserve native labels and validation", () => {
  const html = renderToStaticMarkup(
    h(SyntyrRoot, {},
      h("label", { htmlFor: "name" }, "Name"),
      h(Input, { id: "name", required: true, "aria-invalid": true }),
      h(Select, { id: "status" }, h("option", { value: "active" }, "Active")),
      h(Textarea, { id: "notes", rows: 3 })));
  for (const part of ['for="name"', 'required=""', 'aria-invalid="true"',
    'class="syn-select"', 'class="syn-textarea"']) {
    assert.ok(html.includes(part), part);
  }
});
