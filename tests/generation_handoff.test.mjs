import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import * as model from "../docs/page-builder-model.mjs";
import {createComposer} from "../docs/composition-model.mjs";

const release = "0.3.0-alpha.5";
const manifest = JSON.parse(readFileSync(new URL("../metadata/section-composer.v1.json", import.meta.url)));
const composer = createComposer(manifest, release);
function response() {
  const plan = composer.planIntent({release, title:"CRM", theme:"noir", requirements:["pipeline","metrics"]});
  return {release, status:"generated", stage:"complete", plan, preflight:{valid:true},
    validation:{diagnostics:[]}, output:composer.compose(plan.composition)};
}

test("generation response imports only the editable canonical project", () => {
  const result = response();
  result.output.html = '<script>alert("untrusted")</script>';
  const page = model.parseDocument(model.extractGeneratedProject(result));
  assert.deepEqual(page, result.output.project);
  assert.doesNotMatch(model.exportHtml(page), /<script\b|untrusted/);
  assert.equal(page.blocks.length, 2);
});

test("blocked or mismatched generation responses cannot import even with a project", () => {
  for (const result of [
    {...response(), status:"blocked"},
    {...response(), stage:"planning"},
    {...response(), release:"0.3.0-alpha.4"},
    {...response(), output:{...response().output, release:"0.3.0-alpha.4"}},
    {...response(), output:{html:"<script>evil</script>"}},
  ]) assert.throws(() => model.extractGeneratedProject(result));
});

test("normal projects retain existing import path and generated props are revalidated", () => {
  const page = model.createDefaultDocument();
  assert.equal(model.extractGeneratedProject(page), page);
  const result = response();
  result.output.project.blocks[0].type = "section:invented";
  assert.throws(() => model.parseDocument(model.extractGeneratedProject(result)), /Unknown block/);
});
