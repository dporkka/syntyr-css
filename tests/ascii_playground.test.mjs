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

test('custom ramps preserve spaces and reject multi-cell or control glyphs', async () => {
  const { customRamp } = await import('../tools/ascii-logic.mjs');
  assert.deepEqual(customRamp(' .+#'), [' ','.','+','#']);
  for(const bad of ['x','aaaa','x\nz',' 😀','a\u0301b','x\u202Ey','x漢']) assert.throws(()=>customRamp(bad));
  assert.equal(pixelsToAscii(Uint8ClampedArray.from([255,255,255,255]),1,1,[' ','X']), 'X');
});

test('Bayer and Floyd–Steinberg distribute intermediate tones deterministically', () => {
  const pixels=Uint8ClampedArray.from(Array.from({length:16},()=>[128,128,128,255]).flat());
  for(const mode of ['bayer','floyd']) {
    const art=pixelsToAscii(pixels,4,4,[' ','1'],false,mode);
    assert.equal(art,pixelsToAscii(pixels,4,4,[' ','1'],false,mode));
    assert.ok(art.includes(' ')&&art.includes('1'));
    assert.equal(art.split('\n').length,4);
    assert.equal(pixelsToAscii(new Uint8ClampedArray(64),4,4,[' ','1'],false,mode),'    \n    \n    \n    ');
  }
  assert.throws(()=>pixelsToAscii(pixels,4,4,'binary',false,'unknown'));
});

test('logo text has predictable five-row geometry and safe fallback', async () => {
  const { renderLogo }=await import('../tools/ascii-logic.mjs');
  const text=renderLogo('AB','block');
  assert.equal(text.split('\n').length,5);
  assert.ok(text.split('\n').every(r=>r.length===11));
  assert.match(text,/█/);
  assert.match(renderLogo('a','hash'),/#/);
  assert.throws(()=>renderLogo('a'.repeat(25),'block'));
  assert.throws(()=>renderLogo('<script>','block'));
  assert.throws(()=>renderLogo('A','unknown'));
});
