/* Optional portable multi-page & reusable component projects. Exported HTML has no editor runtime. */
import {createDefaultDocument,parseDocument,exportHtml,MAX_PROJECT_BYTES} from './page-builder-model.mjs';

export const SITE_SCHEMA_VERSION='syntyr.site.v1';
const MAX_PAGES=10;
const MAX_COMPONENTS=20;
const MAX_INSTANCES=200;
const SLUG=/^[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,39}$/;
const SYNCED_TYPES=new Set(['hero','features','split','quote','faq','cta']);
const object=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const keysOnly=(value,allowed)=>Object.keys(value).every(key=>allowed.includes(key));
const sameInstance=(a,slug,blockId)=>a.slug===slug&&a.blockId===blockId;

export function createSiteProject(home=createDefaultDocument()) {
 return parseSiteProject({schema:SITE_SCHEMA_VERSION,pages:[{slug:'',document:home}],shared:{header:null,footer:null}});
}
function validLayout(block,type) {
 if(block===null)return null;
 if(!object(block)||block.type!==type)throw new Error('Shared '+type+' must be a '+type+' block');
 return parseDocument({...createDefaultDocument(),blocks:[block]}).blocks[0];
}
function validateMaster(block) {
 if(!object(block)||!SYNCED_TYPES.has(block.type))
  throw new Error('Reusable component must use an approved native block type');
 return parseDocument({...createDefaultDocument(),blocks:[block]}).blocks[0];
}
function findPage(site,slug) {
 const page=site.pages.find(p=>p.slug===slug);
 if(!page)throw new Error('Unknown site page slug');
 return page;
}
function findMaster(site,id) {
 const component=site.components.find(c=>c.id===id);
 if(!component)throw new Error('Unknown reusable component');
 return component;
}
function findPlacement(site,slug,blockId) {
 const placement=site.instances.find(i=>sameInstance(i,slug,blockId));
 if(!placement)throw new Error('Unknown reusable component instance');
 return placement;
}

export function parseSiteProject(input) {
 let candidate;
 if(typeof input==='string'){
  if(new TextEncoder().encode(input).byteLength>MAX_PROJECT_BYTES)throw new Error('Site project exceeds 32 MiB limit');
  try{candidate=JSON.parse(input);}catch{throw new Error('Invalid site project JSON');}
 }else candidate=input;
 if(!object(candidate)||candidate.schema!==SITE_SCHEMA_VERSION)throw new Error('Unsupported site project schema');
 if(!keysOnly(candidate,['schema','pages','shared','components','instances']))
  throw new Error('Unknown site project property');
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
 const mediaByName=new Map();
 for(const page of pages)for(const [name,data] of Object.entries(page.document.media)){
  if(mediaByName.has(name)&&mediaByName.get(name)!==data)
   throw new Error('Conflicting uploaded image asset across pages: '+name);
  mediaByName.set(name,data);
 }
 const rawComponents=candidate.components===undefined?[]:candidate.components;
 if(!Array.isArray(rawComponents)||rawComponents.length>MAX_COMPONENTS)
  throw new Error('Site supports at most 20 reusable components');
 const ids=new Set();
 const components=rawComponents.map(item=>{
  if(!object(item)||!keysOnly(item,['id','name','block'])||
     typeof item.id!=='string'||!SLUG.test(item.id))
   throw new Error('Invalid reusable component id');
  if(ids.has(item.id))throw new Error('Duplicate reusable component id');
  ids.add(item.id);
  if(typeof item.name!=='string'||!item.name.trim()||item.name.length>100)
   throw new Error('Invalid reusable component name');
  return {id:item.id,name:item.name,block:validateMaster(item.block)};
 });
 const componentIndex=new Map(components.map(item=>[item.id,item]));
 const rawInstances=candidate.instances===undefined?[]:candidate.instances;
 if(!Array.isArray(rawInstances)||rawInstances.length>MAX_INSTANCES)
  throw new Error('Site supports at most 200 reusable instances');
 const placed=new Set();
 const pageIndex=new Map(pages.map(item=>[item.slug,item]));
 const instances=rawInstances.map(item=>{
  if(!object(item)||!keysOnly(item,['slug','blockId','componentId','overrides'])||
     typeof item.slug!=='string'||typeof item.blockId!=='string'||typeof item.componentId!=='string')
   throw new Error('Invalid reusable component instance');
  const key=item.slug+'\0'+item.blockId;
  if(placed.has(key))throw new Error('Duplicate reusable component instance');
  placed.add(key);
  const page=pageIndex.get(item.slug);
  if(!page)throw new Error('Unknown reusable instance page');
  const block=page.document.blocks.find(block=>block.id===item.blockId);
  if(!block)throw new Error('Unknown reusable instance block');
  const master=componentIndex.get(item.componentId);
  if(!master)throw new Error('Unknown reusable component reference');
  if(block.type!==master.block.type)throw new Error('Reusable component instance type mismatch');
  const overrides=item.overrides===undefined?{}:item.overrides;
  if(!object(overrides))throw new Error('Invalid reusable component overrides');
  for(const [field,value] of Object.entries(overrides)){
   if(!Object.hasOwn(master.block.props,field))throw new Error('Unknown reusable component override field');
   if(typeof value!=='string')throw new Error('Reusable component override must be a string');
   if(value.length>5000)throw new Error('Reusable component override too long');
  }
  block.props={...master.block.props,...overrides};
  return {slug:item.slug,blockId:item.blockId,componentId:item.componentId,overrides:{...overrides}};
 });
 if(new TextEncoder().encode(JSON.stringify(candidate)).byteLength>MAX_PROJECT_BYTES)
  throw new Error('Site project exceeds 32 MiB limit');
 return {schema:SITE_SCHEMA_VERSION,pages,shared:{
  header:validLayout(candidate.shared.header??null,'header'),
  footer:validLayout(candidate.shared.footer??null,'footer')
 },components,instances};
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
 next.instances=next.instances.filter(item=>item.slug!==slug);
 return parseSiteProject(next);
}
export function updateSitePage(site,slug,document) {
 const next=parseSiteProject(site);
 const page=findPage(next,slug);
 page.document=parseDocument(document);
 next.instances=next.instances.filter(item=>item.slug!==slug||page.document.blocks.some(block=>block.id===item.blockId&&block.type===findMaster(next,item.componentId).block.type));
 return parseSiteProject(next);
}
export function setSharedLayout(site,part,block) {
 if(!['header','footer'].includes(part))throw new Error('Unknown shared layout');
 const next=parseSiteProject(site);
 next.shared[part]=validLayout(block,part);
 return parseSiteProject(next);
}

export function saveSyncedComponent(site,{id,name,slug,blockId}) {
 const next=parseSiteProject(site);
 if(typeof id!=='string'||!SLUG.test(id))throw new Error('Invalid reusable component id');
 if(next.components.some(c=>c.id===id))throw new Error('Duplicate reusable component id');
 if(typeof name!=='string'||!name.trim()||name.length>100)throw new Error('Invalid reusable component name');
 if(next.components.length>=MAX_COMPONENTS)throw new Error('20 reusable component limit reached');
 if(next.instances.some(i=>sameInstance(i,slug,blockId)))throw new Error('Block is already linked');
 const original=findPage(next,slug).document.blocks.find(b=>b.id===blockId);
 if(!original)throw new Error('Unknown block for reusable component');
 const master=validateMaster({...original,id:'master-'+id});
 next.components.push({id,name,block:master});
 next.instances.push({slug,blockId,componentId:id,overrides:{}});
 return parseSiteProject(next);
}
export function insertSyncedComponent(site,slug,componentId,blockId) {
 const next=parseSiteProject(site);
 const master=findMaster(next,componentId);
 const page=findPage(next,slug);
 if(typeof blockId!=='string'||!/^[a-zA-Z0-9_-]{1,64}$/.test(blockId))throw new Error('Invalid instance block id');
 if(page.document.blocks.some(block=>block.id===blockId))throw new Error('Duplicate instance block id');
 if(page.document.blocks.length>=50)throw new Error('Page block limit reached');
 next.instances.push({slug,blockId,componentId,overrides:{}});
 page.document.blocks.push({id:blockId,type:master.block.type,props:{...master.block.props}});
 return parseSiteProject(next);
}
export function updateSyncedComponent(site,componentId,props) {
 const next=parseSiteProject(site);
 const master=findMaster(next,componentId);
 master.block=validateMaster({...master.block,props});
 return parseSiteProject(next);
}
export function setSyncedOverride(site,slug,blockId,field,value) {
 const next=parseSiteProject(site);
 const instance=findPlacement(next,slug,blockId);
 const master=findMaster(next,instance.componentId);
 if(typeof field!=='string'||!Object.hasOwn(master.block.props,field))
  throw new Error('Unknown reusable component override field');
 if(value===null)delete instance.overrides[field];
 else {
  if(typeof value!=='string')throw new Error('Reusable component override must be a string');
  if(value.length>5000)throw new Error('Reusable component override too long');
  instance.overrides[field]=value;
 }
 return parseSiteProject(next);
}
export function detachSyncedInstance(site,slug,blockId) {
 const next=parseSiteProject(site);
 if(!next.instances.some(i=>sameInstance(i,slug,blockId)))throw new Error('Unknown reusable component instance');
 next.instances=next.instances.filter(i=>!sameInstance(i,slug,blockId));
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
