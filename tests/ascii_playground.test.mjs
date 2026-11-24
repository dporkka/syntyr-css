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

test('3D geometry is deterministic, perspective-scaled, bounded and rotates',()=>{
  for(const kind of ['torus-3d','sphere-3d','cube-3d','wireframe-3d']){
    const art=renderPattern(kind,80,30,'ascii',0);
    assert.equal(art,renderPattern(kind,80,30,'ascii',0));
    const lines=art.split('\n');
    assert.equal(lines.length,30);
    assert.ok(lines.every(line=>line.length===80));
    assert.ok([...art].every(c=>c==='\n'||ramps.ascii.includes(c)));
    assert.ok(art.trim().length>30);
    assert.equal(lines[0].trim(),'');
    assert.equal(lines.at(-1).trim(),'');
    if(kind!=='sphere-3d') assert.notEqual(art,renderPattern(kind,80,30,'ascii',1.2));
    const tiny=renderPattern(kind,1,1,'blocks',0);
    assert.equal(tiny.length,1);
  }
  const torus=renderPattern('torus-3d',80,30,'blocks',0).split('\n');
  const sphere=renderPattern('sphere-3d',80,30,'blocks',0).split('\n');
  assert.equal(torus[15][40],' ');
  assert.notEqual(sphere[15][40],' ');
  const cube=renderPattern('cube-3d',80,30,'ascii',0);
  assert.ok(new Set(cube.replace(/\s/g,'')).size>=2,'lit cube has multiple face intensities');
  assert.throws(()=>renderPattern('cube-3d',161,30,'ascii',0));
  assert.throws(()=>renderPattern('cube-3d',80,30,'ascii',NaN));
});

test('RGB image cells preserve density and composite alpha against black',async()=>{
  const {pixelsToColorAscii}=await import('../tools/ascii-logic.mjs');
  const rgba=Uint8ClampedArray.from([255,0,0,255,0,255,0,128,0,0,255,0,255,255,255,255]);
  const frame=pixelsToColorAscii(rgba,2,2,'blocks',false,'bayer');
  assert.equal(frame.art,pixelsToAscii(rgba,2,2,'blocks',false,'bayer'));
  assert.deepEqual([...frame.colors],[255,0,0,0,128,0,0,0,0,255,255,255]);
  const flipped=pixelsToColorAscii(rgba,2,2,'blocks',true);
  assert.deepEqual([...flipped.colors],[...frame.colors]);
  assert.notEqual(flipped.art,pixelsToAscii(rgba,2,2,'blocks'));
  assert.throws(()=>pixelsToColorAscii(rgba,1,1,'blocks'));
});
test('colored export groups runs, escapes markup and resets ANSI terminal state',()=>{
  const colors=Uint8Array.from([255,0,0,255,0,0,0,128,0,0,0,255]);
  const art='<&\n>█';
  const html=exportArt(art,'html','#abcdef',colors);
  assert.match(html,/<span style="color:#ff0000">&lt;&amp;<\/span>/);
  assert.match(html,/#008000/);
  assert.match(html,/&gt;/);
  const svg=exportArt(art,'svg','#abcdef',colors);
  assert.match(svg,/<tspan fill="#ff0000">&lt;&amp;<\/tspan>/);
  assert.match(svg,/#0000ff/);
  assert.equal(exportArt(art,'txt','#abcdef',colors),art);
  const ansi=exportArt(art,'ansi','#abcdef',colors);
  assert.equal(ansi,'\x1b[38;2;255;0;0m<&\x1b[0m\n\x1b[38;2;0;128;0m>\x1b[38;2;0;0;255m█\x1b[0m');
  assert.equal(exportArt('X','ansi','#abcdef'),'\x1b[38;2;171;205;239mX\x1b[0m');
  assert.throws(()=>exportArt('\x1b[31m','ansi','#abcdef'));
  assert.throws(()=>exportArt('x','html','#abcdef',Uint8Array.from([1,2])));
  assert.throws(()=>exportArt('x','svg','#abcdef',['bad',2,3]));
});
