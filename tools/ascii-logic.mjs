// Pure local ASCII tool logic. No network, DOM or runtime dependency.
export const ramps = Object.freeze({
  ascii: ' .:-=+*#%@',
  blocks: ' ░▒▓█',
  braille: ' ⠁⠂⠄⠒⠶⠷⠿',
  binary: ' 01'
});
const clamp = (n, min, max) => Math.max(min, Math.min(max, n));
export function customRamp(value) {
  if (typeof value !== 'string') throw new RangeError('Enter a character ramp');
  const chars=Array.from(value);
  if(chars.length<2||chars.length>32||new Set(chars).size!==chars.length||
     chars.some(c=>!(/^[ -~]$/u.test(c)||/^[\u2580-\u259f\u2800-\u28ff]$/u.test(c))))
    throw new RangeError('Use 2–32 distinct ASCII, block or Braille glyphs, light to dark');
  return chars;
}
function glyphs(name) {
  if(Array.isArray(name)) return customRamp(name.join(''));
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
export function pixelsToAscii(rgba, cols, rows, rampName, invert=false, dither='none') {
  validateGrid(cols,rows);
  if (rgba.length !== cols*rows*4) throw new RangeError('Pixel count mismatch');
  if(!['none','bayer','floyd'].includes(dither)) throw new RangeError('Unknown dithering mode');
  const ramp=glyphs(rampName), result=[], levels=ramp.length-1;
  const values=new Float64Array(cols*rows);
  for(let i=0;i<values.length;i++) {
    const j=i*4, lum=(.2126*rgba[j]+.7152*rgba[j+1]+.0722*rgba[j+2])/255*(rgba[j+3]/255);
    values[i]=invert?1-lum:lum;
  }
  const matrix=[0,8,2,10,12,4,14,6,3,11,1,9,15,7,13,5];
  const diffuse=(x,y,error,weight)=>{
    if(x>=0&&x<cols&&y>=0&&y<rows) values[y*cols+x]+=error*weight/16;
  };
  for(let y=0;y<rows;y++) {
    let line='';
    for(let x=0;x<cols;x++) {
      const v=clamp(values[y*cols+x],0,1);
      const offset=dither==='bayer'?((matrix[(y%4)*4+x%4]+.5)/16-.5)/levels:0;
      const level=Math.round(clamp(v+offset,0,1)*levels);
      line+=ramp[level];
      if(dither==='floyd') {
        const error=v-level/levels;
        diffuse(x+1,y,error,7); diffuse(x-1,y+1,error,3);
        diffuse(x,y+1,error,5); diffuse(x+1,y+1,error,1);
      }
    }
    result.push(line);
  }
  return result.join('\n');
}
// Small fixed meshes: generated once, projected afresh per frame. Depth is
// reciprocal camera-space z, interpolated in screen space for solid triangles.
const shapes3d = new Set(['torus-3d','sphere-3d','cube-3d','wireframe-3d']);
function makeSurface(kind) {
  const vertices=[], triangles=[], nu=40, nv=24;
  for(let u=0;u<=nu;u++) for(let v=0;v<=nv;v++) {
    const a=u/nu*2*Math.PI, b=v/nv*(kind==='torus-3d'?2*Math.PI:Math.PI);
    const ca=Math.cos(a),sa=Math.sin(a),cb=Math.cos(b),sb=Math.sin(b);
    if(kind==='torus-3d') {
      vertices.push([(1+.38*cb)*ca,(1+.38*cb)*sa,.38*sb,cb*ca,cb*sa,sb]);
    } else {
      vertices.push([1.25*sb*ca,1.25*cb,1.25*sb*sa,sb*ca,cb,sb*sa]);
    }
  }
  for(let u=0;u<nu;u++) for(let v=0;v<nv;v++) {
    const a=u*(nv+1)+v,b=a+nv+1;
    triangles.push([a,b,a+1],[b,b+1,a+1]);
  }
  return {vertices,triangles};
}
function makeCube() {
  const vertices=[],triangles=[];
  for(let axis=0;axis<3;axis++) for(const sign of [-1,1]) {
    const start=vertices.length;
    for(const [u,v] of [[-1,-1],[1,-1],[1,1],[-1,1]]) {
      const p=[0,0,0],n=[0,0,0];
      p[axis]=sign*.85;p[(axis+1)%3]=u*.85;p[(axis+2)%3]=v*.85;n[axis]=sign;
      vertices.push([...p,...n]);
    }
    triangles.push([start,start+1,start+2],[start,start+2,start+3]);
  }
  return {vertices,triangles};
}
const meshes={
  'torus-3d':makeSurface('torus-3d'),
  'sphere-3d':makeSurface('sphere-3d'),
  'cube-3d':makeCube()
};
const wireVertices=Array.from({length:8},(_,i)=>[i&1?.85:-.85,i&2?.85:-.85,i&4?.85:-.85]);
const wireEdges=wireVertices.flatMap((_,i)=>[1,2,4].filter(bit=>(i&bit)===0).map(bit=>[i,i|bit]));
function render3D(kind,cols,rows,ramp,time) {
  const cells=Array(cols*rows).fill(ramp[0]), depth=new Float64Array(cells.length);
  const ax=.45+time*.7, ay=.35+time*.53;
  const cx=Math.cos(ax),sx=Math.sin(ax),cy=Math.cos(ay),sy=Math.sin(ay);
  const scale=Math.min(cols/2,rows)*1.45;
  function rotate(x,y,z) {
    const yy=y*cx-z*sx, zz=y*sx+z*cx;
    return [x*cy+zz*sy,yy,-x*sy+zz*cy];
  }
  function project(p) {
    const [x,y,z]=rotate(...p.slice(0,3)), q=1/(5+z);
    return [(cols-1)/2+2*scale*x*q,(rows-1)/2-scale*y*q,q];
  }
  function plot(x,y,z,shade) {
    if(x<0||x>=cols||y<0||y>=rows)return;
    const i=y*cols+x;
    if(z>depth[i]) {
      depth[i]=z;
      cells[i]=ramp[Math.max(1,Math.round(clamp(shade,0,1)*(ramp.length-1)))];
    }
  }
  if(kind==='wireframe-3d') {
    // Transparent wireframe: intentionally shows rear edges as well.
    const points=wireVertices.map(project);
    for(const [a,b] of wireEdges) {
      const p=points[a],q=points[b],steps=Math.max(1,Math.ceil(Math.max(Math.abs(q[0]-p[0]),Math.abs(q[1]-p[1]))));
      for(let i=0;i<=steps;i++) {
        const t=i/steps,z=p[2]+(q[2]-p[2])*t;
        plot(Math.round(p[0]+(q[0]-p[0])*t),Math.round(p[1]+(q[1]-p[1])*t),z,clamp((z-.15)*11, .25,1));
      }
    }
  } else {
    const {vertices,triangles}=meshes[kind],points=vertices.map(project);
    const shades=vertices.map(p=>{
      const [x,y,z]=rotate(...p.slice(3));
      return .15+.85*Math.max(0,-.4*x+.55*y-.73*z);
    });
    const edge=(a,b,x,y)=>(b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]);
    for(const [a,b,c] of triangles) {
      const p=points[a],q=points[b],r=points[c],area=edge(p,q,r[0],r[1]);
      if(Math.abs(area)<1e-9)continue;
      const minX=Math.max(0,Math.ceil(Math.min(p[0],q[0],r[0]))),maxX=Math.min(cols-1,Math.floor(Math.max(p[0],q[0],r[0])));
      const minY=Math.max(0,Math.ceil(Math.min(p[1],q[1],r[1]))),maxY=Math.min(rows-1,Math.floor(Math.max(p[1],q[1],r[1])));
      for(let y=minY;y<=maxY;y++)for(let x=minX;x<=maxX;x++){
        const w0=edge(q,r,x,y)/area,w1=edge(r,p,x,y)/area,w2=1-w0-w1;
        if(w0< -1e-8||w1< -1e-8||w2< -1e-8)continue;
        const z=w0*p[2]+w1*q[2]+w2*r[2];
        const shade=(w0*p[2]*shades[a]+w1*q[2]*shades[b]+w2*r[2]*shades[c])/z;
        plot(x,y,z,shade);
      }
    }
  }
  return Array.from({length:rows},(_,y)=>cells.slice(y*cols,(y+1)*cols).join('')).join('\n');
}
export function renderPattern(kind,cols,rows,rampName,time=0) {
  validateGrid(cols,rows);
  if ((!shapes3d.has(kind)&&!['sphere','torus','wave','plasma','rain','radar'].includes(kind)) || !Number.isFinite(time))
    throw new RangeError('Unknown pattern or time');
  const ramp=glyphs(rampName), result=[];
  if(shapes3d.has(kind))return render3D(kind,cols,rows,ramp,time);
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

const alphabet=Object.freeze({
 A:[14,17,31,17,17], B:[30,17,30,17,30], C:[15,16,16,16,15],
 D:[30,17,17,17,30], E:[31,16,30,16,31], F:[31,16,30,16,16],
 G:[15,16,19,17,15], H:[17,17,31,17,17], I:[31,4,4,4,31],
 J:[7,2,2,18,12], K:[17,18,28,18,17], L:[16,16,16,16,31],
 M:[17,27,21,17,17], N:[17,25,21,19,17], O:[14,17,17,17,14],
 P:[30,17,30,16,16], Q:[14,17,21,18,13], R:[30,17,30,18,17],
 S:[15,16,14,1,30], T:[31,4,4,4,4], U:[17,17,17,17,14],
 V:[17,17,17,10,4], W:[17,17,21,27,17], X:[17,10,4,10,17],
 Y:[17,10,4,4,4], Z:[31,2,4,8,31],
 0:[14,19,21,25,14], 1:[4,12,4,4,14], 2:[14,17,2,4,31],
 3:[30,1,14,1,30], 4:[18,18,31,2,2], 5:[31,16,30,1,30],
 6:[14,16,30,17,14], 7:[31,1,2,4,8], 8:[14,17,14,17,14],
 9:[14,17,15,1,14], ' ':[0,0,0,0,0], '-':[0,0,31,0,0]
});
export function renderLogo(text,style='block') {
  if(typeof text!=='string'||!/^[- A-Za-z0-9]{1,24}$/.test(text)||!text.trim())
    throw new RangeError('Enter 1–24 letters, digits, spaces or hyphens');
  const fills={block:'█',hash:'#',dot:'●'};
  if(!Object.hasOwn(fills,style)) throw new RangeError('Unknown logo style');
  return Array.from({length:5},(_,y)=>Array.from(text.toUpperCase(),c=>
    Array.from({length:5},(_,x)=>alphabet[c][y]&(16>>x)?fills[style]:' ').join('')
  ).join(' ')).join('\n');
}
