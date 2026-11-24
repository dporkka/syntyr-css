#!/usr/bin/env node
// Optional source-checkout build tool. Nothing is added to the CSS runtime.
import {openSync, fstatSync, readSync, closeSync, constants} from 'node:fs';
import {parseArgs} from 'node:util';
import {customRamp, gridSize, pixelsToAscii, renderLogo, renderPattern, exportArt} from '../tools/ascii-logic.mjs';

const HELP = 'Syntyr ASCII build tool (Node 22+)\n\n'
  +'  node scripts/ascii.mjs pattern <torus|sphere|wave|plasma|rain|radar|torus-3d|sphere-3d|cube-3d|wireframe-3d> [--columns 64] [--rows 24] [--time 0]\n'
  +'  node scripts/ascii.mjs logo <text> [--style block|hash|dot]\n'
  +'  node scripts/ascii.mjs image <file.pgm|file.ppm> [--columns 64] [--dither none|bayer|floyd] [--invert]\n\n'
  +'  pattern/image: --ramp ascii|blocks|braille|binary OR --custom-ramp " .#"\n'
  +'  all modes: --format txt|html|svg --color "#76e7f7"\n'
  +'  Art is written to stdout; errors to stderr. Redirect output to save a file.\n'
  +'  Image mode accepts P2/P3/P5/P6 Netpbm, 8-bit samples, max 16 MiB and 4 million pixels.\n';

const MAX_BYTES=16*1024*1024;
function readBounded(path) {
  const fd=openSync(path,constants.O_RDONLY|constants.O_NONBLOCK);
  try {
    const info=fstatSync(fd);
    if(!info.isFile()||info.size>MAX_BYTES) throw new Error('Image must be a regular file at most 16 MiB');
    const bytes=Buffer.alloc(info.size+1);
    let pos=0;
    while(pos<bytes.length) {
      const n=readSync(fd,bytes,pos,bytes.length-pos,null);
      if(!n) break;
      pos+=n;
    }
    if(pos!==info.size) throw new Error('Image changed while reading');
    return bytes.subarray(0,pos);
  } finally { closeSync(fd); }
}
function parsePNM(bytes) {
  let i=0;
  const ws=b=>b===32||b===9||b===10||b===13||b===11||b===12;
  function skip() {
    while(i<bytes.length) {
      if(ws(bytes[i])) {i++;continue;}
      if(bytes[i]===35) {while(i<bytes.length&&bytes[i]!==10&&bytes[i]!==13)i++;continue;}
      break;
    }
  }
  function token() {
    skip(); const start=i;
    while(i<bytes.length&&!ws(bytes[i])&&bytes[i]!==35) {
      if(++i-start>32) throw new Error('Invalid Netpbm token');
    }
    if(i===start) throw new Error('Incomplete Netpbm image');
    return bytes.toString('latin1',start,i);
  }
  function integer() {
    const t=token();
    if(!/^[0-9]{1,10}$/.test(t)) throw new Error('Invalid Netpbm integer');
    return Number(t);
  }
  const magic=token();
  if(!['P2','P3','P5','P6'].includes(magic)) throw new Error('Use a P2/P3/P5/P6 Netpbm image');
  const width=integer(),height=integer(),max=integer();
  if(!width||!height||width*height>4_000_000||max<1||max>255) throw new Error('Unsupported Netpbm dimensions or sample range');
  const channels=magic==='P3'||magic==='P6'?3:1, count=width*height*channels;
  let samples;
  if(magic==='P5'||magic==='P6') {
    if(!ws(bytes[i])) throw new Error('Missing raster separator');
    // A raw raster begins after exactly one separator byte (or CRLF).
    if(bytes[i]===13&&bytes[i+1]===10&&bytes.length-i-2===count)i+=2;else i++;
    if(bytes.length-i!==count) throw new Error('Unexpected Netpbm raster length');
    samples=bytes.subarray(i);
    if(max<255&&samples.some(v=>v>max)) throw new Error('Netpbm sample exceeds maximum');
  } else {
    samples=new Uint8Array(count);
    for(let j=0;j<count;j++) {
      const v=integer();
      if(v>max) throw new Error('Netpbm sample exceeds maximum');
      samples[j]=v;
    }
    skip();
    if(i!==bytes.length) throw new Error('Unexpected extra Netpbm data');
  }
  return {width,height,max,channels,samples};
}
function sampleImage(image,cols,rows) {
  const {width,height,max,channels,samples}=image, rgba=new Uint8ClampedArray(cols*rows*4);
  for(let y=0;y<rows;y++)for(let x=0;x<cols;x++){
    // Box-average source pixels on shrink; nearest source cell on expansion.
    const x0=Math.floor(x*width/cols), x1=Math.max(x0+1,Math.floor((x+1)*width/cols));
    const y0=Math.floor(y*height/rows), y1=Math.max(y0+1,Math.floor((y+1)*height/rows));
    let r=0,g=0,b=0,n=0;
    for(let sy=y0;sy<y1;sy++)for(let sx=x0;sx<x1;sx++){
      const k=(sy*width+sx)*channels;
      r+=samples[k];g+=samples[k+(channels===3?1:0)];b+=samples[k+(channels===3?2:0)];n++;
    }
    const k=(y*cols+x)*4, scale=255/(max*n);
    rgba[k]=r*scale;rgba[k+1]=g*scale;rgba[k+2]=b*scale;rgba[k+3]=255;
  }
  return rgba;
}
const common={format:{type:'string',default:'txt'},color:{type:'string',default:'#76e7f7'}};
const rampOptions={ramp:{type:'string'},'custom-ramp':{type:'string'},columns:{type:'string',default:'64'}};
const byMode={
  pattern:{...common,...rampOptions,rows:{type:'string',default:'24'},time:{type:'string',default:'0'}},
  logo:{...common,style:{type:'string',default:'block'}},
  image:{...common,...rampOptions,dither:{type:'string',default:'none'},invert:{type:'boolean',default:false}}
};
function whole(value,label,min,max) {
  if(!/^[0-9]+$/.test(value)||Number(value)<min||Number(value)>max)throw new Error(label+' out of range');
  return Number(value);
}
function run(args) {
  if(args.length===0||args.length===1&&args[0]==='--help'){process.stdout.write(HELP);return;}
  const mode=args.shift();
  if(!Object.hasOwn(byMode,mode))throw new Error('Unknown mode; use --help');
  const {values:v,positionals:p}=parseArgs({args,options:byMode[mode],allowPositionals:true,strict:true});
  if(p.length!==1)throw new Error('Provide exactly one source argument');
  if(v.ramp!==undefined&&v['custom-ramp']!==undefined)throw new Error('Choose one glyph ramp');
  if(!['txt','html','svg'].includes(v.format)||!/^#[0-9a-f]{6}$/i.test(v.color))throw new Error('Invalid format or color');
  let art;
  if(mode==='logo')art=renderLogo(p[0],v.style);
  else {
    const ramp=v['custom-ramp']===undefined?(v.ramp??'ascii'):customRamp(v['custom-ramp']);
    const cols=whole(v.columns,'Columns',1,160);
    if(mode==='pattern'){
      const time=Number(v.time);
      if(!v.time.trim()||!Number.isFinite(time)||time<0||time>86400)throw new Error('Time must be 0–86400 seconds');
      art=renderPattern(p[0],cols,whole(v.rows,'Rows',1,100),ramp,time);
    } else {
      const image=parsePNM(readBounded(p[0]));
      const size=gridSize(image.width,image.height,cols);
      art=pixelsToAscii(sampleImage(image,size.cols,size.rows),size.cols,size.rows,ramp,v.invert,v.dither);
    }
  }
  const output=exportArt(art,v.format,v.color);
  // HTML files redirected from stdout need an encoding marker; copied browser fragments remain unchanged.
  process.stdout.write((v.format==='html'?'\uFEFF':'')+output+'\n');
}
try {run(process.argv.slice(2));}
catch(error){process.stderr.write('error: '+error.message+'\n');process.exitCode=1;}
