import { gridSize, pixelsToAscii, renderPattern, exportArt, customRamp, renderLogo } from './ascii-logic.mjs';
const $ = id => document.getElementById(id);
const source=$('source'), pattern=$('pattern'), ramp=$('ramp'), columns=$('columns'), color=$('color'), invert=$('invert'), format=$('format');
const preview=$('preview'), output=$('export'), status=$('status');
const motion=matchMedia('(prefers-reduced-motion: reduce)');
let bitmap=null, loadVersion=0, art='', playing=false, raf=0, start=0, last=0, loading=false;
function setStatus(message) { status.textContent=message; }
function syncActions() {
  $('play').disabled=source.value!=='pattern'||motion.matches||playing||!art;
  $('stop').disabled=!playing;
  $('copy').disabled=$('download').disabled=!art||playing||loading;
}
function syncExport() { output.value=art?exportArt(art,format.value,color.value):''; syncActions(); }
function draw(time=0) {
  try { return drawFrame(time); } catch(error) {
    art=''; preview.textContent='No preview'; $('dimensions').textContent='Invalid settings';
    syncExport(); setStatus(error.message);
    return false;
  }
}
function drawFrame(time=0) {
  const cols=Number(columns.value);
  $('columns-value').value=String(cols);
  let size;
  const chosenRamp=source.value!=='logo'&&ramp.value==='custom'?customRamp($('custom-ramp').value):ramp.value;
  if(source.value==='logo') {
    art=renderLogo($('logo-text').value,$('logo-style').value);
    size={cols:art.split('\n')[0].length,rows:5};
  } else if(source.value==='image') {
    if(!bitmap||loading) { art=''; preview.textContent=loading?'Decoding image…':'Choose a local image.'; $('dimensions').textContent='No image ready'; syncExport(); return false; }
    size=gridSize(bitmap.width,bitmap.height,cols);
    const canvas=document.createElement('canvas'); canvas.width=size.cols; canvas.height=size.rows;
    const ctx=canvas.getContext('2d',{willReadFrequently:true});
    ctx.drawImage(bitmap,0,0,size.cols,size.rows);
    art=pixelsToAscii(ctx.getImageData(0,0,size.cols,size.rows).data,size.cols,size.rows,chosenRamp,invert.checked,$('dither').value);
  } else {
    size={cols,rows:Math.min(100,Math.max(8,Math.round(cols*.38)))};
    art=renderPattern(pattern.value,size.cols,size.rows,chosenRamp,time);
  }
  preview.textContent=art;
  preview.style.color=color.value;
  $('dimensions').textContent=size.cols+' columns × '+size.rows+' rows';
  if(!playing) syncExport();
  return true;
}
function stop(message='') {
  if(!playing) return;
  playing=false; cancelAnimationFrame(raf); syncExport();
  if(message) setStatus(message);
}
function tick(now) {
  if(!playing) return;
  if(now-start>=5000) { stop('Animation finished. Current frame ready to export.'); return; }
  if(now-last>=84) { draw((now-start)/1000); last=now; }
  raf=requestAnimationFrame(tick);
}
$('play').addEventListener('click',()=>{
  if(motion.matches||source.value!=='pattern'||playing||!art) return;
  playing=true; start=performance.now(); last=0; syncActions(); setStatus('Animating for five seconds.');
  raf=requestAnimationFrame(tick);
});
$('stop').addEventListener('click',()=>stop('Animation stopped. Current frame ready to export.'));
motion.addEventListener('change',()=>{if(motion.matches) stop('Reduced motion enabled.'); syncActions();});
document.addEventListener('visibilitychange',()=>{if(document.hidden) stop();});
function syncFields() {
  const imageMode=source.value==='image', logoMode=source.value==='logo';
  $('image-field').hidden=$('invert-field').hidden=$('dither-field').hidden=!imageMode;
  $('logo-field').hidden=$('logo-style-field').hidden=!logoMode;
  $('pattern-field').hidden=source.value!=='pattern';
  $('columns-field').hidden=$('ramp-field').hidden=logoMode;
  $('custom-field').hidden=logoMode||ramp.value!=='custom';
}
source.addEventListener('change',()=>{ stop(); syncFields(); setStatus(''); draw(); });
for(const control of [pattern,ramp,columns,color,invert,$('custom-ramp'),$('dither'),$('logo-text'),$('logo-style')])
  control.addEventListener('input',()=>{stop();syncFields();setStatus('');draw();});
format.addEventListener('change',syncExport);
$('image').addEventListener('change',async()=>{
  const version=++loadVersion, file=$('image').files[0];
  bitmap?.close(); bitmap=null; loading=false; stop();
  if(!file) { draw(); return; }
  if(!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>10*1024*1024) {
    draw(); setStatus('Choose a PNG, JPEG or WebP image no larger than 10 MB.'); return;
  }
  loading=true; draw(); setStatus('Decoding locally.');
  try {
    const decoded=await createImageBitmap(file);
    if(version!==loadVersion) { decoded.close(); return; }
    if(decoded.width*decoded.height>40_000_000) { decoded.close(); throw new Error('Image exceeds 40 megapixels.'); }
    bitmap=decoded; loading=false;
    if(draw()&&source.value==='image') setStatus('Image converted locally.');
  } catch(error) {
    if(version!==loadVersion) return;
    loading=false; bitmap?.close(); bitmap=null; draw(); setStatus('Could not convert image. '+error.message);
  }
});
$('copy').addEventListener('click',async()=>{
  try { await navigator.clipboard.writeText(output.value); setStatus('Output copied.'); }
  catch { output.focus(); output.select(); setStatus('Clipboard unavailable. Select and copy the output manually.'); }
});
$('download').addEventListener('click',()=>{
  if(!art||playing||loading) return;
  const mime={txt:'text/plain',html:'text/html',svg:'image/svg+xml'}[format.value];
  const url=URL.createObjectURL(new Blob([output.value],{type:mime+';charset=utf-8'}));
  const a=document.createElement('a'); a.href=url; a.download='syntyr-ascii.'+format.value; a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
});
$('ascii-controls').disabled=false;
syncFields(); draw();
