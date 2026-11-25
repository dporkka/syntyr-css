import test from "node:test";
import assert from "node:assert/strict";
import {spawnSync} from "node:child_process";
import {fileURLToPath} from "node:url";
import {planIntent, listIntents, compose} from "../scripts/compose.mjs";

const release = "0.3.0-alpha.5";
const input = {release, title:"CRM dashboard", theme:"studio",
  requirements:["pipeline", "metrics", "inventory-search", "account-management"]};

test("CRM requirements select honest canonical static sections", () => {
  const p = planIntent(input);
  assert.deepEqual(p, planIntent(input));
  assert.equal(p.ready, true);
  assert.deepEqual(p.composition.sections.map(s=>s.section_id),
    ["crm-workspace","metric-overview","resource-workspace","resource-crud"]);
  assert.equal(p.coverage.length, 4);
  assert.ok(p.coverage.every(c=>c.status==="presentation-only" && c.host_requirements.length));
  assert.deepEqual(p.unresolved, []);
  assert.match(compose(p.composition).html,/Deal pipeline/);
});

test("unknown requirements remain unresolved and cannot be silently discarded", () => {
  const p = planIntent({...input, requirements:["pipeline","live-map","searchable-combobox"]});
  assert.equal(p.ready,false);
  assert.equal(p.composition,null);
  assert.deepEqual(p.unresolved,["live-map","searchable-combobox"]);
  assert.equal(p.coverage[0].section_id,"crm-workspace");
});

test("deduplicate section IDs without hiding requirements or changing order", () => {
  const p = planIntent({...input,requirements:["inventory-search","record-search","metrics"]});
  assert.deepEqual(p.composition.sections.map(s=>s.section_id),["resource-workspace","metric-overview"]);
  assert.equal(p.coverage.length,3);
});

test("supported intents are discoverable and compose against current registry", () => {
  const catalog=listIntents(release);
  assert.ok(catalog.intents.length>=10);
  for(const i of catalog.intents) {
    const p=planIntent({...input,requirements:[i.id]});
    assert.equal(p.ready,true,i.id);
    assert.match(compose(p.composition).html,/<main/);
    assert.ok(i.host_requirements.length || i.status==="static-content");
  }
});

test("invalid intent plan shape, version or size rejected", () => {
  for(const v of [{...input,release:"latest"},{...input,requirements:[]},
    {...input,requirements:["pipeline","pipeline"]},{...input,requirements:Array(51).fill("pipeline")},
    {...input,requirements:["Pipeline"]},{...input,theme:"unknown"},
    {...input,html:"<script>"},{...input,requirements:[{id:"pipeline"}]}])
    assert.throws(()=>planIntent(v));
});

test("CLI plan and intent catalog are accessible without rendering unsupported plans", () => {
  const path=fileURLToPath(new URL("../scripts/compose.mjs",import.meta.url));
  const run=(args,data)=>spawnSync(process.execPath,[path,...args],{input:data,encoding:"utf8"});
  const res=run(["--plan"],JSON.stringify(input));
  assert.equal(res.status,0,res.stderr);
  assert.deepEqual(JSON.parse(res.stdout),planIntent(input));
  const list=run(["--list-intents",release],"");
  assert.equal(list.status,0,list.stderr);
  assert.deepEqual(JSON.parse(list.stdout),listIntents(release));
  const unsupported=run(["--plan"],JSON.stringify({...input,requirements:["live-map"]}));
  assert.equal(unsupported.status,2,unsupported.stderr);
  assert.equal(JSON.parse(unsupported.stdout).composition,null);
});
