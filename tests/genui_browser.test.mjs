import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { validateJson, GenUIError, renderJson } from '../integrations/genui/browser.mjs';

const spec = (root) => JSON.stringify({version: 1, root});
const node = (type, props = {}) => ({type, props});
test('accepts every catalog component and the documented fixture', () => {
  const catalog = JSON.parse(readFileSync(new URL('../integrations/genui/catalog.json', import.meta.url)));
  const roots = [
    {type:'Panel',children:[node('Divider')]},
    {type:'Stack',children:[node('Divider')]},
    {type:'Grid',children:[node('Divider')]},
    node('Heading',{text:'Title',level:2}), node('Text',{text:'<script>'}),
    node('Badge',{text:'Beta'}), node('Metric',{label:'MRR',value:'$100'}),
    node('List',{items:['A']}), node('Table',{caption:'Data',columns:['A'],rows:[['B']]}),
    node('Progress',{label:'Done',value:1,max:2}),
    {type:'Details',props:{summary:'More'},children:[node('Divider')]},node('Divider')
  ];
  assert.deepEqual(roots.map(x=>x.type).sort(),Object.keys(catalog.components).sort());
  for(const root of roots) assert.deepEqual(validateJson(spec(root)).root,root);
  validateJson(readFileSync(new URL('../integrations/genui/example.json',import.meta.url),'utf8'));
});
test('rejects malformed, duplicate, noninteger, and unsupported properties', () => {
  for(const bad of [
    '{"version":1,"version":1,"root":{"type":"Divider"}}',
    '{"version":1,"root":{"type":"Text","props":{"text":"a","t\\u0065xt":"b"}}}',
    '{"version":1.0,"root":{"type":"Divider"}}',
    '{"version":1,"root":{"type":"Heading","props":{"text":"a","level":2e0}}}',
    '{"version":1,"root":{"type":"Text","props":{"text":"\\ud800"}}}',
    'null', '[]', '{', '{"version":true,"root":{"type":"Divider"}}',
    spec(node('constructor')),spec(node('Text',{text:'x',style:'evil'})),
    spec(node('Text',{text:'x',__proto__:null,onclick:'evil'})),
    spec(node('Progress',{label:'A',value:2,max:1})),
    spec(node('Table',{caption:'A',columns:['A'],rows:[['A','B']]})),
    spec({type:'Text',props:{text:'a'},children:[]}),
  ]) assert.throws(()=>validateJson(bad),GenUIError,bad);
});
test('enforces text, nesting, nodes and UTF-8 byte bounds', () => {
  assert.throws(()=>validateJson(spec(node('Text',{text:'x'.repeat(4001)}))),GenUIError);
  validateJson(spec(node('Text',{text:'😀'.repeat(4000)})));
  let root=node('Divider');
  for(let i=0;i<12;i++) root={type:'Stack',children:[root]};
  assert.throws(()=>validateJson(spec(root)),GenUIError);
  assert.throws(()=>validateJson(spec({type:'Stack',children:Array(256).fill(node('Divider'))})),GenUIError);
  assert.throws(()=>validateJson(' '.repeat(262145)),GenUIError);
  assert.throws(()=>validateJson(spec({type:'Stack',children:Array.from({length:20},()=>node('Text',{text:'😀'.repeat(4000)}))})),GenUIError);
});
test('does not touch a DOM when input fails validation', () => {
  assert.throws(()=>renderJson(spec(node('Script')),null),GenUIError);
});
