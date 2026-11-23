/* Optional multi-page site projects: published output requires only HTML and CSS. */
import {createBlock,createDefaultDocument,parseDocument,exportHtml,MAX_PROJECT_BYTES} from './page-builder-model.mjs';
export const SITE_SCHEMA_VERSION='syntyr.site.v1';
const MAX_PAGES=10;
const SLUG=/^[a-z][a-z0-9-]{0,39}$/;
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const keysOnly=(value,allowed)=>Object.keys(value).every(key=>allowed.includes(key));

export function createSiteProject(home=createDefaultDocument()) {
 return parseSiteProject({schema:SITE_SCHEMA_VERSION,pages:[{slug:'',document:home}],shared:{header:null,footer:null}});
}
function validLayout(block,type) {
 if(block===null)return null;
 if(!object(block)||block.type!==type)throw new Error('Shared '+type+' must be a '+type+' block');
 return parseDocument({...createDefaultDocument(),blocks:[block]}).blocks[0];
}
export function parseSiteProject(input) {
 let candidate;
 if(typeof input==='string'){
  if(new TextEncoder().encode(input).byteLength>MAX_PROJECT_BYTES)throw new Error('Site project exceeds 32 MiB limit');
  try{candidate=JSON.parse(input);}catch{throw new Error('Invalid site project JSON');}
 }else candidate=input;
 if(!object(candidate)||candidate.schema!==SITE_SCHEMA_VERSION)throw new Error('Unsupported site project schema');
 if(!keysOnly(candidate,['schema','pages','shared']))throw new Error('Unknown site project property');
 if(!Array.isArray(candidate.pages)||candidate.pages.length<1||candidate.pages.length>MAX_PAGES)
  throw new Error('Site must have between 1 and 10 pages');
 if(!object(candidate.shared)||!keysOnly(candidate.shared,['header','footer']))
  throw new Error('Invalid shared site layouts');
 const seen=new Set();
 const pages=candidate.pages.map(p=>{
  if(!object(p)||!keysOnly(p,['slug','document'])||typeof p.slug!=='string'||(p.slug!==''&&!SLUG.test(p.slug)))
   throw new Error('Invalid page slug or path');
  if(seen.has(p.slug))throw new Error('Duplicate page slug: '+p.slug);
  seen.add(p.slug);
  return {slug:p.slug,document:parseDocument(p.document)};
 });
 if(!seen.has(''))throw new Error('Site must contain a home page');
 const mediaByName = new Map();
 for (const page of pages) for (const [name, data] of Object.entries(page.document.media)) {
  if (mediaByName.has(name) && mediaByName.get(name) !== data)
   throw new Error('Conflicting uploaded image asset across pages: ' + name);
  mediaByName.set(name, data);
 }
 if(new TextEncoder().encode(JSON.stringify(candidate)).byteLength>MAX_PROJECT_BYTES)
  throw new Error('Site project exceeds 32 MiB limit');
 return {schema:SITE_SCHEMA_VERSION,pages,shared:{
  header:validLayout(candidate.shared.header??null,'header'),
  footer:validLayout(candidate.shared.footer??null,'footer')
 }};
}
export function addSitePage(site,slug) {
 const next=parseSiteProject(site);
 if(typeof slug!=='string'||!SLUG.test(slug))throw new Error('Invalid page slug');
 if(next.pages.some(p=>p.slug===slug))throw new Error('Duplicate page slug');
 if(next.pages.length>=MAX_PAGES)throw new Error('Site has reached the 10 page limit');
 const document=createDefaultDocument();
 document.title=slug.split('-').map(part=>part[0].toUpperCase()+part.slice(1)).join(' ');
 next.pages.push({slug,document});
 return parseSiteProject(next);
}
export function removeSitePage(site,slug) {
 if(slug==='')throw new Error('Cannot remove the home page');
 const next=parseSiteProject(site);
 const index=next.pages.findIndex(p=>p.slug===slug);
 if(index<0)throw new Error('Unknown page slug');
 next.pages.splice(index,1);
 return parseSiteProject(next);
}
export function updateSitePage(site,slug,document) {
 const next=parseSiteProject(site);
 const p=next.pages.find(p=>p.slug===slug);
 if(!p)throw new Error('Unknown page slug');
 p.document=parseDocument(document);
 return parseSiteProject(next);
}
export function setSharedLayout(site,part,block) {
 if(!['header','footer'].includes(part))throw new Error('Unknown shared layout');
 const next=parseSiteProject(site);
 next.shared[part]=validLayout(block,part);
 return parseSiteProject(next);
}
export function exportSitePages(site,{previewAssets=false}={}) {
 const next=parseSiteProject(site);
 return next.pages.map(({slug,document})=>({
  name:slug?slug+'/index.html':'index.html',
  content:exportHtml(document,{
   previewAssets,sharedHeader:next.shared.header,sharedFooter:next.shared.footer,
   stylesheetHref:slug?'../syntyr.all.css':'syntyr.all.css',
   assetPrefix:slug?'../assets/':'assets/'
  })
 }));
}
