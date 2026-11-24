import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {renderLogo, renderPattern, exportArt} from '../tools/ascii-logic.mjs';
const cli=(...args)=>spawnSync(process.execPath,['scripts/ascii.mjs',...args],{encoding:'utf8'});
test('CLI help and logo produce clean stdout',()=>{
  assert.match(cli('--help').stdout,/pattern/);
  const r=cli('logo','SYNTYR','--style','hash','--format','svg','--color','#abcdef');
  assert.equal(r.status,0,r.stderr);
  assert.equal(r.stdout,exportArt(renderLogo('SYNTYR','hash'),'svg','#abcdef')+'\n');
  assert.equal(r.stderr,'');
});
test('procedural generation matches browser logic and validates flags',()=>{
  const r=cli('pattern','torus','--columns','32','--rows','16','--ramp','blocks','--time','1');
  assert.equal(r.status,0,r.stderr);
  assert.equal(r.stdout,renderPattern('torus',32,16,'blocks',1)+'\n');
  for(const args of [['pattern','torus','--columns','999'],['pattern','torus','--bogus'],['logo','<bad>'],['pattern','torus','--time','Infinity'],['logo','X','--rows','5']]){
    const bad=cli(...args); assert.notEqual(bad.status,0); assert.equal(bad.stdout,''); assert.match(bad.stderr,/error:/i);
  }
});
test('local PGM and PPM images convert; malformed input fails closed',()=>{
  const dir=mkdtempSync(join(tmpdir(),'syntyr-ascii-'));
  try {
    const pgm=join(dir,'a.pgm'), ppm=join(dir,'a.ppm');
    writeFileSync(pgm,'P2\n# example\n4 2\n255\n0 255 0 255\n0 255 0 255\n');
    writeFileSync(ppm,Buffer.concat([Buffer.from('P6\n2 2\n255\n'),Buffer.from([0,0,0,255,255,255,0,0,0,255,255,255])]));
    for(const f of [pgm,ppm]){
      const r=cli('image',f,'--columns','4','--custom-ramp',' X');
      assert.equal(r.status,0,r.stderr); assert.match(r.stdout,/X/); assert.match(r.stdout,/ /);
    }
    writeFileSync(pgm,'P2\n4 2\n255\n0 255');
    assert.notEqual(cli('image',pgm).status,0);
    writeFileSync(pgm,'P2\n999999999 999999999\n255\n0');
    assert.notEqual(cli('image',pgm).status,0);
    assert.notEqual(cli('image',dir).status,0);
    assert.notEqual(cli('image',join(dir,'missing')).status,0);
  }finally{rmSync(dir,{recursive:true,force:true});}
});

test('all four Netpbm formats and UTF-8 export behave consistently',()=>{
  const dir=mkdtempSync(join(tmpdir(),'syntyr-ascii-'));
  try{
    const inputs=[
      Buffer.from('P2\n2 1\n15\n0 15\n'),
      Buffer.from('P3\n2 1\n15\n0 0 0 15 15 15\n'),
      Buffer.concat([Buffer.from('P5\n2 1\n15\n'),Buffer.from([0,15])]),
      Buffer.concat([Buffer.from('P6\n2 1\n15\n'),Buffer.from([0,0,0,15,15,15])])
    ];
    for(const [i,data] of inputs.entries()){
      const f=join(dir,String(i));writeFileSync(f,data);
      const r=cli('image',f,'--columns','2','--ramp','blocks');
      assert.equal(r.status,0,r.stderr);assert.equal(r.stdout,' █\n');
    }
    const f=join(dir,'space');writeFileSync(f,Buffer.concat([Buffer.from('P5\n2 1\n255\n'),Buffer.from([32,255])]));
    assert.equal(cli('image',f,'--columns','2','--ramp','blocks').stdout,'░█\n');
    const html=cli('logo','A','--format','html');
    assert.equal(html.status,0,html.stderr);
    assert.equal(html.stdout.charCodeAt(0),0xfeff);
    assert.match(html.stdout,/█/);
    const bad=cli('pattern','torus','--ramp','ascii','--custom-ramp',' .#');
    assert.notEqual(bad.status,0);
  }finally{rmSync(dir,{recursive:true,force:true});}
});

test('raw Netpbm header comments do not consume the first raster byte',()=>{
  const dir=mkdtempSync(join(tmpdir(),'syntyr-ascii-comment-'));
  try{
    for(const [magic,pixels] of [['P5',[35,255]],['P6',[35,35,35,255,255,255]]]){
      const f=join(dir,magic);
      writeFileSync(f,Buffer.concat([Buffer.from(magic+'\n2 1\n255# final comment\n'),Buffer.from(pixels)]));
      const r=cli('image',f,'--columns','2','--ramp','blocks');
      assert.equal(r.status,0,r.stderr);
      const expected=r.stdout;
      writeFileSync(f,Buffer.concat([Buffer.from(magic+'\n2 1\n255\n'),Buffer.from(pixels)]));
      assert.equal(cli('image',f,'--columns','2','--ramp','blocks').stdout,expected);
    }
    const f=join(dir,'truncated');
    writeFileSync(f,'P5\n1 1\n255# no separator');
    assert.notEqual(cli('image',f).status,0);
  }finally{rmSync(dir,{recursive:true,force:true});}
});
