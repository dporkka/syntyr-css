// Optional native browser companion. Copy this and ascii-logic.mjs together.
import {renderPattern,ramps} from './ascii-logic.mjs';
const clamp=(v,min,max)=>Math.max(min,Math.min(max,Number.isFinite(v)?v:0));
const kinds=new Set(['orbit','particles','distortion','radar','scroll']);
export function normalizePointer(x,y,rect){
  if(!(rect.width>0&&rect.height>0))return {x:0,y:0};
  return {x:clamp((x-rect.left)/rect.width*2-1,-1,1),y:clamp((y-rect.top)/rect.height*2-1,-1,1)};
}
export function scrollProgress(rect,height){
  return height>0&&rect.height>0?clamp((height-rect.top)/(height+rect.height),0,1):0;
}
export function interactiveFrame(kind,cols,rows,state={}){
  if(!kinds.has(kind)||!Number.isInteger(cols)||!Number.isInteger(rows)||cols<1||cols>80||rows<1||rows>32)throw new RangeError('Invalid interactive geometry');
  const x=clamp(state.x,-1,1),y=clamp(state.y,-1,1),p=clamp(state.progress??.5,0,1);
  if(kind==='orbit')return renderPattern('torus-3d',cols,rows,'ascii',0,{pitch:.45+y*1.1,yaw:.35+x*1.4});
  const chars=ramps.ascii;
  return Array.from({length:rows},(_,j)=>Array.from({length:cols},(_,i)=>{
    const u=(i+.5)/cols*2-1,v=(j+.5)/rows*2-1;
    const dx=u-x,dy=v-y,d=Math.hypot(dx,dy);
    let value=0;
    if(kind==='particles'){
      const seed=(Math.sin(i*127.1+j*311.7)*43758.5453)%1;
      const noise=(seed+1)%1;
      value=noise>.78?clamp(.22+(1-Math.min(1,d))*1.3,0,1):0;
    }else if(kind==='distortion'){
      const wave=Math.sin(u*14+v*6+Math.exp(-d*d*5)*5);
      value=clamp(1-Math.abs(wave)*2,0,1)*(.4+.6*Math.exp(-d*d));
    }else if(kind==='radar'){
      const r=Math.hypot(u,v),beam=Math.atan2(y||.001,x||.001),a=Math.atan2(v,u);
      const difference=Math.abs(Math.atan2(Math.sin(a-beam),Math.cos(a-beam)));
      value=r<.95?Math.max(Math.abs(Math.sin(r*16))<.17?.38:0,Math.exp(-difference*5)*.9,Math.abs(u)<.03||Math.abs(v)<.03?.25:0):0;
    }else{
      value=(Math.sin(u*10+v*6+p*9)+1)/2*clamp(1-Math.abs(v-(p*2-1))*.65,0,1);
    }
    return chars[Math.round(clamp(value,0,1)*(chars.length-1))];
  }).join('')).join('\n');
}

// Nothing runs until an explicit activation. Event-driven only, no perpetual
// frame loop, no global pointer capture. Disable restores the literal fallback.
export function attachAsciiEffect({root,art,button,kind,cols=64,rows=24}){
  if(!root?.contains(art)||!root.contains(button)||art.getAttribute('aria-hidden')!=='true'||
     art.children.length||button.tagName!=='BUTTON')throw new TypeError('Expected decorative plain-text art and a native button');
  interactiveFrame(kind,cols,rows);
  const doc=root.ownerDocument,win=doc.defaultView;
  const motion=win.matchMedia('(prefers-reduced-motion: reduce)');
  const contrast=win.matchMedia('(prefers-contrast: more)');
  const forced=win.matchMedia('(forced-colors: active)');
  const abort=new AbortController(),opts={signal:abort.signal};
  const fallback=art.textContent;
  let active=false,raf=0,last=0,timeout=0,state={x:0,y:0,progress:.5};
  const allowed=()=>!motion.matches&&!contrast.matches&&!forced.matches&&!doc.hidden;
  function cancel(){if(raf)win.cancelAnimationFrame(raf);if(timeout)win.clearTimeout(timeout);raf=timeout=0;}
  function sync(){button.disabled=!allowed();button.setAttribute('aria-pressed',String(active));}
  function stop(){active=false;cancel();art.textContent=fallback;sync();}
  function paint(now){raf=0;if(!active||!allowed()){stop();return;}last=now;art.textContent=interactiveFrame(kind,cols,rows,state);}
  function schedule(){
    if(!active||!allowed()||raf||timeout)return;
    const wait=Math.max(0,84-(win.performance.now()-last));
    if(wait)timeout=win.setTimeout(()=>{timeout=0;if(active&&allowed())raf=win.requestAnimationFrame(paint);},wait);
    else raf=win.requestAnimationFrame(paint);
  }
  function scroll(){if(!active)return;state={x:0,y:0,progress:scrollProgress(root.getBoundingClientRect(),win.innerHeight)};schedule();}
  button.addEventListener('click',()=>{
    if(active){stop();return;}
    if(!allowed())return;
    active=true;state={x:0,y:0,progress:.5};sync();
    if(kind==='scroll')scroll();else schedule();
  },opts);
  if(kind==='scroll')win.addEventListener('scroll',scroll,{...opts,passive:true});
  else{
    root.addEventListener('pointermove',e=>{if(!active||e.pointerType==='touch')return;state=normalizePointer(e.clientX,e.clientY,root.getBoundingClientRect());schedule();},{...opts,passive:true});
    root.addEventListener('pointerleave',()=>{state={x:0,y:0};schedule();},opts);
  }
  const preference=()=>{if(!allowed())stop();else sync();};
  for(const query of [motion,contrast,forced])query.addEventListener('change',preference,opts);
  doc.addEventListener('visibilitychange',preference,opts);
  sync();
  return {destroy(){stop();abort.abort();button.disabled=true;}};
}
