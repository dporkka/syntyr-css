// Pure local ASCII tool logic. No network, DOM or runtime dependency.
export const ramps = Object.freeze({
  ascii: ' .:-=+*#%@',
  blocks: ' ░▒▓█',
  braille: ' ⠁⠂⠄⠒⠶⠷⠿',
  binary: ' 01'
});
const clamp = (n, min, max) => Math.max(min, Math.min(max, n));
function glyphs(name) {
  if (!Object.hasOwn(ramps, name)) throw new RangeError('Unknown character set');
  return Array.from(ramps[name]);
}
function validateGrid(cols, rows) {
  if (!Number.isInteger(cols) || !Number.isInteger(rows) || cols < 1 || cols > 160 || rows < 1 || rows > 100)
    throw new RangeError('Grid must be 1–160 columns and 1–100 rows');
}
export function gridSize(width, height, columns) {
  if (![width,height].every(n=>Number.isFinite(n)&&n>0) || !Number.isInteger(columns) || columns<1 || columns>160)
    throw new RangeError('Invalid image dimensions or columns');
  const ratio = height / width * .5;
  const cols = Math.max(1, Math.min(columns, Math.floor(100 / ratio)));
  return {cols, rows:clamp(Math.round(cols*ratio),1,100)};
}
export function pixelsToAscii(rgba, cols, rows, rampName, invert=false) {
  validateGrid(cols,rows);
  if (rgba.length !== cols*rows*4) throw new RangeError('Pixel count mismatch');
  const ramp=glyphs(rampName), result=[];
  for(let y=0;y<rows;y++) {
    let line='';
    for(let x=0;x<cols;x++) {
      const i=(y*cols+x)*4;
      const lum=(.2126*rgba[i]+.7152*rgba[i+1]+.0722*rgba[i+2])/255*(rgba[i+3]/255);
      line+=ramp[Math.round(clamp(invert?1-lum:lum,0,1)*(ramp.length-1))];
    }
    result.push(line);
  }
  return result.join('\n');
}
export function renderPattern(kind,cols,rows,rampName,time=0) {
  validateGrid(cols,rows);
  if (!['sphere','torus','wave','plasma','rain','radar'].includes(kind) || !Number.isFinite(time))
    throw new RangeError('Unknown pattern or time');
  const ramp=glyphs(rampName), result=[];
  for(let y=0;y<rows;y++) {
    let line='';
    for(let x=0;x<cols;x++) {
      const u=(x+.5-cols/2)/(rows||1)*1.8, v=(y+.5-rows/2)/rows*3.6;
      const r=Math.hypot(u,v), a=Math.atan2(v,u);
      let value=0;
      switch(kind) {
        case 'sphere': if(r<1.25) value=.15+.85*clamp((Math.sqrt(1-(r/1.25)**2)+.35*u*Math.cos(time)+.35*v*Math.sin(time))/1.25,0,1); break;
        case 'torus': {
          const tilt=.65+.25*Math.cos(time), distance=Math.hypot(u,v/tilt);
          value=clamp(1-Math.abs(distance-.95)*3.5,0,1)*(.6+.4*Math.cos(a+time)); break;
        }
        case 'wave': value=clamp(1-Math.abs(v-.55*Math.sin(u*4-time)-.2*Math.sin(u*9+time))*3.5,0,1); break;
        case 'plasma': value=(Math.sin(u*6+time)+Math.sin(v*6-time)+Math.sin(r*8-time*2)+3)/6; break;
        case 'rain': {
          const offset=((Math.sin(x*127.1)*43758.5453)%1+1)%1;
          const head=(offset*(rows+12)+time*(5+x%4))%(rows+12);
          value=clamp(1-(head-y)/12,0,1)*(head>=y?1:0); break;
        }
        case 'radar': if(r<1.45) {
          const beam=((time-a)%(2*Math.PI)+2*Math.PI)%(2*Math.PI);
          value=Math.max(Math.exp(-beam*2.5)*.8,Math.abs(Math.sin(r*13))<.13?.5:0,Math.abs(u)<.045||Math.abs(v)<.045?.35:0);
        } break;
      }
      line+=ramp[Math.round(clamp(value,0,1)*(ramp.length-1))];
    }
    result.push(line);
  }
  return result.join('\n');
}
const escape = value=>value.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
export function exportArt(art,format,color) {
  if(typeof art!=='string'||art.length>17000||!/^#[0-9a-f]{6}$/i.test(color)) throw new RangeError('Invalid art or color');
  if(format==='txt') return art;
  const safe=escape(art);
  if(format==='html') return '<pre style="color:'+color+';background:#080e14;font:12px/1.5 monospace;white-space:pre;overflow:auto;font-variant-ligatures:none" aria-hidden="true">'+safe+'</pre>\n<!-- Add a meaningful text alternative if this art conveys information. -->';
  if(format==='svg') {
    const lines=art.split('\n'), width=Math.max(1,...lines.map(line=>Array.from(line).length))*8+16, height=lines.length*16+16;
    return '<svg xmlns="http://www.w3.org/2000/svg" width="'+width+'" height="'+height+'" viewBox="0 0 '+width+' '+height+'" role="img" aria-label="ASCII artwork"><rect width="100%" height="100%" fill="#080e14"/><g fill="'+color+'" font-family="monospace" font-size="13" xml:space="preserve">'+lines.map((line,i)=>'<text x="8" y="'+(19+i*16)+'">'+escape(line)+'</text>').join('')+'</g></svg>';
  }
  throw new RangeError('Unknown export format');
}
