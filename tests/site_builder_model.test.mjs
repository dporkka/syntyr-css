import test from 'node:test';
import assert from 'node:assert/strict';
import {createBlock,createDefaultDocument} from '../docs/page-builder-model.mjs';
import {SITE_SCHEMA_VERSION,createSiteProject,parseSiteProject,addSitePage,removeSitePage,updateSitePage,setSharedLayout,exportSitePages} from '../docs/site-builder-model.mjs';
import {createStoredZip} from '../docs/page-builder-zip.mjs';

test('converts legacy page to versioned site preserving content',()=>{
 const original=createDefaultDocument();original.blocks[0].props.title='Welcome';
 const site=createSiteProject(original);assert.equal(site.schema,SITE_SCHEMA_VERSION);
 assert.deepEqual(site.pages.map(p=>p.slug),['']);
 assert.deepEqual(site.pages[0].document,original);
 assert.deepEqual(parseSiteProject(JSON.stringify(site)),site);
});
test('exports pages with shared header footer and path-correct stylesheet',()=>{
 let site=addSitePage(createSiteProject(),'about');
 const about=structuredClone(site.pages[1].document);about.title='About Us';about.blocks[0].props.title='About Content';
 site=updateSitePage(site,'about',about);
 const header=createBlock('header','site-header');header.props.brand='Syntyr & Co';header.props.linkHref='/about/';
 site=setSharedLayout(site,'header',header);
 const footer=createBlock('footer','site-footer');footer.props.brand='Shared footer';
 site=setSharedLayout(site,'footer',footer);
 const files=new Map(exportSitePages(site).map(f=>[f.name,f.content]));
 assert.deepEqual([...files.keys()],['index.html','about/index.html']);
 for(const html of files.values()){
  assert.match(html,/Syntyr &amp; Co/);assert.match(html,/Shared footer/);
  assert.match(html,/href="\/about\/"/);assert.doesNotMatch(html,/<script\b/i);
 }
 assert.match(files.get('index.html'),/href="syntyr\.all\.css"/);
 assert.match(files.get('about/index.html'),/href="\.\.\/syntyr\.all\.css"/);
 assert.match(files.get('about/index.html'),/About Content/);
 assert.doesNotMatch(files.get('index.html'),/About Content/);
 assert.ok(createStoredZip([...exportSitePages(site),{name:'syntyr.all.css',content:'body{}'}]) instanceof Uint8Array);
});
test('rejects traversal, duplicate slug and deletion of home',()=>{
 let site=createSiteProject();
 for(const slug of ['../secret','/about','about/../bad','ABOUT','a\\b','','a.html','admin?x=1'])
  assert.throws(()=>addSitePage(site,slug),/slug|path|route/i);
 site=addSitePage(site,'about');
 assert.throws(()=>addSitePage(site,'about'),/duplicate/i);
 assert.throws(()=>removeSitePage(site,''),/home/i);
 site.pages[0].slug='another';assert.throws(()=>parseSiteProject(site),/home/i);
});
test('rejects untrusted shared layouts and unknown site properties',()=>{
 const site=createSiteProject();
 assert.throws(()=>setSharedLayout(site,'header',createBlock('hero','wrong')),/header/i);
 assert.throws(()=>setSharedLayout(site,'footer',{type:'footer',id:'x',props:{brand:'<script>'}}),/field/i);
 site.unrecognized='yes';assert.throws(()=>parseSiteProject(site),/unknown/i);
});
test('caps pages at ten and ZIP forbids unsafe nested paths',()=>{
 let site=createSiteProject();for(let i=0;i<9;i++)site=addSitePage(site,`page-${i}`);
 assert.throws(()=>addSitePage(site,'extra'),/10|limit/i);
 for(const name of ['../secrets/index.html','a/b/index.html','ABOUT/index.html'])
  assert.throws(()=>createStoredZip([{name,content:'x'}]),/path/i);
});

test('site rejects colliding asset names with different image contents',()=>{
 let site=addSitePage(createSiteProject(),'about');
 const name='custom-'+ 'a'.repeat(64) + '.png';
 const prefix=[137,80,78,71,13,10,26,10];
 const img=extra=>'data:image/png;base64,'+Buffer.from([...prefix,0,0,0,extra]).toString('base64');
 site.pages[0].document.media[name]=img(1);
 site.pages[1].document.media[name]=img(2);
 assert.throws(()=>parseSiteProject(site),/conflicting uploaded image/i);
 site.pages[1].document.media[name]=img(1);
 assert.doesNotThrow(()=>parseSiteProject(site));
});

test('invalid trailing and repeated separators in page slugs fail validation',()=>{
  const site=createSiteProject();
  for(const slug of ['about-','about--team','a--b','-about']) {
    assert.throws(()=>addSitePage(site,slug),/slug/i);
  }
  assert.equal(addSitePage(site,'about-team').pages[1].document.title,'About Team');
});
