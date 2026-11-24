import test from 'node:test';
import assert from 'node:assert/strict';
import { gridSize, pixelsToAscii, renderPattern, exportArt, ramps } from '../tools/ascii-logic.mjs';

test('image grid preserves character aspect and caps workload', () => {
  assert.deepEqual(gridSize(800, 400, 80), {cols:80, rows:20});
  assert.deepEqual(gridSize(100, 1000, 100), {cols:20, rows:100});
  assert.throws(() => gridSize(0, 200, 80));
  assert.throws(() => gridSize(800, 400, 2000));
});
test('conversion respects luminance, alpha, inversion and exact rows', () => {
  const rgba = Uint8ClampedArray.from([0,0,0,255,255,255,255,255,255,255,255,0,128,128,128,255]);
  assert.equal(pixelsToAscii(rgba,2,2,'blocks'), ' █\n ▒');
  assert.equal(pixelsToAscii(rgba,2,2,'blocks',true), '█ \n█▒');
  assert.throws(() => pixelsToAscii(rgba,3,2,'blocks'));
});
test('procedural fields are deterministic, bounded, and use chosen glyphs', () => {
  for (const kind of ['sphere','torus','wave','plasma','rain','radar']) {
    const art = renderPattern(kind,48,24,'braille',0);
    assert.equal(art,renderPattern(kind,48,24,'braille',0));
    assert.equal(art.split('\n').length,24);
    assert.ok(art.split('\n').every(row=>Array.from(row).length===48));
    assert.ok([...art].every(c=>c==='\n'||ramps.braille.includes(c)));
    assert.notEqual(art.trim(),'');
  }
  assert.notEqual(renderPattern('wave',48,24,'ascii',0),renderPattern('wave',48,24,'ascii',1));
});
test('exports escape markup and reject injected colors', () => {
  assert.equal(exportArt('<&>','txt','#abcdef'),' <&>'.trim());
  assert.match(exportArt('<&>','html','#abcdef'),/&lt;&amp;&gt;/);
  assert.match(exportArt('<&>','svg','#abcdef'),/&lt;&amp;&gt;/);
  assert.throws(()=>exportArt('x','svg','red" onload="alert(1)'));
  assert.throws(()=>exportArt('x','js','#abcdef'));
});
