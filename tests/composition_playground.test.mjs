import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {createComposer} from "../docs/composition-model.mjs";
import {compose,planIntent,listIntents} from "../scripts/compose.mjs";
const manifest=JSON.parse(readFileSync(new URL("../metadata/section-composer.v1.json",import.meta.url),"utf8"));
const release="0.3.0-alpha.5";
test("browser and CLI share identical intent planning and canonical output",()=>{
 const browser=createComposer(manifest,release);
 assert.deepEqual(browser.listIntents(release),listIntents(release));
 const input={release,title:"CRM",theme:"noir",requirements:["pipeline","metrics","inventory-search","account-management"]};
 const plan=browser.planIntent(input);
 assert.deepEqual(plan,planIntent(input));
 assert.deepEqual(browser.compose(plan.composition),compose(plan.composition));
 assert.equal(browser.planIntent({...input,requirements:["live-map"]}).ready,false);
});
test("browser rejects mismatched candidate or manifest",()=>{
 assert.throws(()=>createComposer({...manifest,source_version:"other"},release));
 assert.throws(()=>createComposer(manifest,"other"));
});
