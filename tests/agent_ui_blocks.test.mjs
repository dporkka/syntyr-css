import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { compose, listSections } from "../scripts/compose.mjs";

test("agent UI blocks resolve from canonical registry and compose safely", () => {
  const release = "0.3.0-alpha.5";
  const ids = ["ai-conversation", "ai-tool-run", "ai-approval"];
  const entries = listSections(release).sections;
  for (const id of ids) {
    const entry = entries.find(section => section.id === id);
    assert.ok(entry, id);
    assert.deepEqual(entry.required_stylesheets, ["syntyr.core.css"]);
    const item = JSON.parse(readFileSync(new URL("../registry/r/" + id + ".json", import.meta.url)));
    const source = readFileSync(new URL("../blocks/snippets/" + id + ".html", import.meta.url), "utf8").trim();
    assert.ok(item.files.some(file => file.content.trim() === source), id);
  }
  const result = compose({release, title:"Agent console", theme:"studio",
    sections: [...ids, "ai-approval"].map(section_id => ({section_id}))});
  assert.doesNotMatch(result.html, /<script\b|<form\b/i);
  assert.match(result.html, /<details>/);
  const buttons = [...result.html.matchAll(/<button\b[^>]*>/g)].map(match => match[0]);
  assert.equal(buttons.length, 4);
  assert.ok(buttons.every(button => /\bdisabled\b/.test(button) && /type="button"/.test(button)));
  const htmlIds = [...result.html.matchAll(/\sid="([^"]+)"/g)].map(match => match[1]);
  assert.equal(htmlIds.length, new Set(htmlIds).size);
});
