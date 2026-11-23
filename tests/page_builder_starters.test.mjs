import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {registerSectionManifest,parseDocument,exportHtml,requiredAssets} from "../docs/page-builder-model.mjs";
import {STARTER_PAGES,createStarterPage} from "../docs/page-builder-starters.mjs";

registerSectionManifest(JSON.parse(readFileSync(new URL("../metadata/section-composer.v1.json",import.meta.url))));
const expected=["portfolio","agency","saas","small-business"];
test("four practical starter pages are deterministic, editable, and distinguishable",()=>{
  assert.deepEqual(STARTER_PAGES.map(x=>x.id),expected);
  for(const id of expected){
    const page=createStarterPage(id);
    assert.equal(page.schema,"syntyr.page.v1");
    assert.deepEqual(parseDocument(JSON.stringify(page)),page);
    assert.ok(page.blocks.length>=5 && page.blocks.length<=12);
    assert.equal(page.blocks[0].type,"hero");
    assert.equal(page.blocks.filter(x=>x.type==="hero").length,1);
    assert.equal(new Set(page.blocks.map(x=>x.id)).size,page.blocks.length);
    assert.ok(page.title.length>0 && page.description.length>0);
    assert.match(exportHtml(page),/<h1\b/);
    assert.match(exportHtml(page),/href="#block-starter-1"/);
    assert.match(exportHtml(page),/id="block-starter-1"/);
    assert.doesNotMatch(exportHtml(page),/<script\b|<iframe\b| onerror=/i);
    assert.deepEqual(requiredAssets(page),[...new Set(requiredAssets(page))].sort());
    assert.equal(Object.keys(page.media).length,0);
  }
  assert.throws(()=>createStarterPage("unknown"),/starter/i);
});
test("starter preview and copy ownership avoid fake reviews and inflated claims",()=>{
  for(const starter of STARTER_PAGES){
    assert.match(starter.description,/example|starter|layout/i);
    const html=exportHtml(createStarterPage(starter.id));
    // Starter labels and samples must not claim real customer endorsements.
    assert.doesNotMatch(html, /trusted by 10,000|five star|verified customer|award-winning/i);
  }
});
