import {attachAsciiEffect} from './ascii-interactive.mjs';
const controllers=[];
for(const root of document.querySelectorAll('[data-ascii-effect]')){
  controllers.push(attachAsciiEffect({root,art:root.querySelector('pre'),button:root.querySelector('button'),kind:root.dataset.asciiEffect,cols:56,rows:20}));
}
window.addEventListener('pagehide',event=>{if(!event.persisted)controllers.forEach(c=>c.destroy());});
