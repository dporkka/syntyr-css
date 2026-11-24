import test from 'node:test';
import assert from 'node:assert/strict';
import {interactiveFrame,normalizePointer,scrollProgress} from '../tools/ascii-interactive.mjs';

test('pointer normalization and scroll progress are clamped',()=>{
  assert.deepEqual(normalizePointer(50,50,{left:0,top:0,width:100,height:100}),{x:0,y:0});
  assert.deepEqual(normalizePointer(300,-10,{left:0,top:0,width:100,height:100}),{x:1,y:-1});
  assert.deepEqual(normalizePointer(50,50,{left:0,top:0,width:0,height:0}),{x:0,y:0});
  assert.equal(scrollProgress({top:800,height:200},800),0);
  assert.equal(scrollProgress({top:300,height:200},800),.5);
  assert.equal(scrollProgress({top:-200,height:200},800),1);
});
test('interactive frames are bounded deterministic and respond to both axes',()=>{
  for(const kind of ['orbit','particles','distortion','radar','scroll']){
    const neutral=interactiveFrame(kind,64,24,{x:0,y:0,progress:.5});
    assert.equal(neutral,interactiveFrame(kind,64,24,{x:0,y:0,progress:.5}));
    assert.equal(neutral.split('\n').length,24);
    assert.ok(neutral.split('\n').every(r=>r.length===64));
    assert.ok(neutral.trim().length>10);
    const changed=interactiveFrame(kind,64,24,{x:.8,y:-.7,progress:.9});
    assert.notEqual(neutral,changed,kind);
  }
  assert.notEqual(interactiveFrame('orbit',64,24,{x:0,y:0}),interactiveFrame('orbit',64,24,{x:0,y:1}));
  assert.notEqual(interactiveFrame('orbit',64,24,{x:0,y:0}),interactiveFrame('orbit',64,24,{x:1,y:0}));
  assert.throws(()=>interactiveFrame('orbit',81,24,{}));
  assert.throws(()=>interactiveFrame('unknown',64,24,{}));
});
