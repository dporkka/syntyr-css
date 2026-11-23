import test from 'node:test';
import assert from 'node:assert/strict';
import {createBlock,createDefaultDocument} from '../docs/page-builder-model.mjs';
import {
 createSiteProject,addSitePage,parseSiteProject,exportSitePages,
 saveSyncedComponent,insertSyncedComponent,updateSyncedComponent,
 setSyncedOverride,detachSyncedInstance,removeSitePage
} from '../docs/site-builder-model.mjs';

function linkedSite() {
 let site=addSitePage(createSiteProject(),'about');
 site=saveSyncedComponent(site,{id:'primary-cta',name:'Primary call to action',slug:'',blockId:'cta-1'});
 site=insertSyncedComponent(site,'about','primary-cta','cta-reused');
 return site;
}

test('master changes update every linked block on all pages',()=>{
 let site=linkedSite();
 assert.equal(site.components.length,1);
 assert.equal(site.instances.length,2);
 assert.equal(site.pages[1].document.blocks.at(-1).props.heading,'Ready to build?');
 const master={...site.components[0].block.props,heading:'Shared service headline'};
 site=updateSyncedComponent(site,'primary-cta',master);
 assert.equal(site.pages[0].document.blocks.find(b=>b.id==='cta-1').props.heading,'Shared service headline');
 assert.equal(site.pages[1].document.blocks.find(b=>b.id==='cta-reused').props.heading,'Shared service headline');
 const html=exportSitePages(site).map(item=>item.content);
 assert.ok(html.every(markup=>markup.includes('Shared service headline')));
 assert.deepEqual(parseSiteProject(JSON.stringify(site)),site);
});

test('per-instance field override persists while other master fields update',()=>{
 let site=linkedSite();
 site=setSyncedOverride(site,'about','cta-reused','heading','About-specific heading');
 site=updateSyncedComponent(site,'primary-cta',{...site.components[0].block.props,heading:'New shared title',description:'New shared description'});
 const home=site.pages[0].document.blocks.find(b=>b.id==='cta-1');
 const about=site.pages[1].document.blocks.find(b=>b.id==='cta-reused');
 assert.equal(home.props.heading,'New shared title');
 assert.equal(about.props.heading,'About-specific heading');
 assert.equal(about.props.description,'New shared description');
 site=setSyncedOverride(site,'about','cta-reused','heading',null);
 assert.equal(site.pages[1].document.blocks.find(b=>b.id==='cta-reused').props.heading,'New shared title');
});

test('detaching preserves last resolved content and removes only one link',()=>{
 let site=linkedSite();
 site=setSyncedOverride(site,'about','cta-reused','heading','Customized content');
 site=detachSyncedInstance(site,'about','cta-reused');
 assert.equal(site.instances.length,1);
 site=updateSyncedComponent(site,'primary-cta',{...site.components[0].block.props,heading:'Changed globally'});
 assert.equal(site.pages[0].document.blocks.find(b=>b.id==='cta-1').props.heading,'Changed globally');
 assert.equal(site.pages[1].document.blocks.find(b=>b.id==='cta-reused').props.heading,'Customized content');
});

test('invalid links, wrong block types, duplicate instances and unsupported overrides fail closed',()=>{
 const site=linkedSite();
 assert.throws(()=>insertSyncedComponent(site,'about','primary-cta','cta-reused'),/duplicate/i);
 assert.throws(()=>insertSyncedComponent(site,'about','unknown','new-one'),/unknown/i);
 assert.throws(()=>saveSyncedComponent(site,{id:'primary-cta',name:'Duplicate',slug:'',blockId:'features-1'}),/duplicate/i);
 assert.throws(()=>saveSyncedComponent(site,{id:'bad/name',name:'Bad',slug:'',blockId:'features-1'}),/id/i);
 assert.throws(()=>setSyncedOverride(site,'about','cta-reused','unknown','x'),/field|override/i);
 assert.throws(()=>setSyncedOverride(site,'about','cta-reused','heading',{}),/string/i);
 const bad=structuredClone(site);bad.instances[1].componentId='unknown';
 assert.throws(()=>parseSiteProject(bad),/unknown/i);
 bad.instances[1].componentId='primary-cta';bad.instances.push({...bad.instances[1]});
 assert.throws(()=>parseSiteProject(bad),/duplicate/i);
 const mismatched=structuredClone(site);mismatched.pages[1].document.blocks.at(-1).type='hero';
 mismatched.pages[1].document.blocks.at(-1).props=createBlock('hero','valid-hero').props;
 assert.throws(()=>parseSiteProject(mismatched),/type/i);
});

test('deleting a site page prunes references, escaping malicious master content on export',()=>{
 let site=linkedSite();
 site=updateSyncedComponent(site,'primary-cta',{...site.components[0].block.props,heading:'<img src=x onerror=alert(1)>'});
 for(const page of exportSitePages(site)) {
  assert.match(page.content,/&lt;img src=x onerror=alert\(1\)&gt;/);
  assert.doesNotMatch(page.content,/<img src=x onerror/);
 }
 site=removeSitePage(site,'about');
 assert.equal(site.pages.length,1);
 assert.equal(site.instances.length,1);
});
