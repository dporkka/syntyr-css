import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
import {
  registerSectionManifest, createDefaultDocument, createBlock, parseDocument,
  replaceBlockImage, restoreBlockImage, requiredAssets, exportHtml, getImageAssetBytes, verifyDocumentMedia
} from "../docs/page-builder-model.mjs";
import {createStoredZip} from "../docs/page-builder-zip.mjs";

const manifest=JSON.parse(readFileSync(new URL("../metadata/section-composer.v1.json",import.meta.url)));
registerSectionManifest(manifest);
// 1x1 opaque PNG. No SVG/HTML/user scripts.
const base64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WlJnE8AAAAASUVORK5CYII=";
const raw=Buffer.from(base64,"base64");
const filename="custom-"+createHash("sha256").update(raw).digest("hex")+".png";
const dataURL="data:image/png;base64,"+base64;
const gallery=()=>({...createDefaultDocument(),blocks:[createBlock("section:image-gallery","gallery-1")]});

test("image and alt attributes become editable text fields without breaking existing canonical sections",()=>{
  const block=createBlock("section:image-gallery","gallery-1");
  assert.equal(typeof block.props.src1,"string");
  assert.equal(typeof block.props.alt1,"string");
  assert.match(block.props.src1,/gallery-horizon/);
  assert.match(block.props.alt1,/coastal|sunset|hill/i);
  const page=gallery();
  assert.deepEqual(parseDocument(page),page);
  assert.match(exportHtml(page),/src="assets\/gallery-horizon.svg"/);
});

test("image replacement follows matching full-image link and works in preview, static export, and project JSON",()=>{
  const original=gallery();
  const updated=replaceBlockImage(original,"gallery-1","src1",{filename,dataURL});
  assert.equal(original.media[filename],undefined);
  assert.equal(updated.media[filename],dataURL);
  const block=updated.blocks[0];
  assert.equal(block.props.src1,"assets/"+filename);
  assert.equal(block.props.href1,"assets/"+filename);
  assert.deepEqual(parseDocument(JSON.stringify(updated)),updated);
  assert.match(exportHtml(updated),new RegExp('src="assets/'+filename.replace(".","\\.")+'"'));
  assert.match(exportHtml(updated,{previewAssets:true}),new RegExp('src="data:image/png;base64,'));
  assert.doesNotMatch(exportHtml(updated),/<script\b|data:image\/png/);
  assert.deepEqual(requiredAssets(updated),[
    filename,"gallery-architecture.svg","gallery-botanical.svg","gallery-signal.svg"
  ].sort());
  assert.deepEqual(Buffer.from(getImageAssetBytes(updated,filename)),raw);
  const restored=restoreBlockImage(updated,"gallery-1","src1");
  assert.match(restored.blocks[0].props.src1,/gallery-horizon.svg/);
  assert.match(restored.blocks[0].props.href1,/gallery-horizon.svg/);
  assert.deepEqual(requiredAssets(restored),[
    "gallery-architecture.svg","gallery-botanical.svg","gallery-horizon.svg","gallery-signal.svg"
  ]);
});

test("imports refuse injected image URLs, unsafe SVG uploads, inconsistent MIME and spoofed assets",()=>{
  const page=gallery();
  for(const payload of ["javascript:alert(1)","data:text/html;base64,PHNjcmlwdD4=","https://tracking.example/img","assets/../../bad.png"]){
    const bad=structuredClone(page);
    bad.blocks[0].props.src1=payload;
    assert.throws(()=>parseDocument(bad),/image|asset|source/i);
  }
  for (const invalid of [
    ["custom-"+'a'.repeat(64)+".svg",dataURL],
    [filename,"data:image/svg+xml;base64,PHN2Zz48L3N2Zz4="],
    [filename,"data:image/png;base64,PHNjcmlwdD4="],
    [filename,"data:image/jpeg;base64,"+base64],
    [filename,"data:image/png;base64,***INVALID***"],
    ["../../steal.png",dataURL]
  ]){
    const bad=structuredClone(page);
    bad.media={[invalid[0]]:invalid[1]};
    assert.throws(()=>parseDocument(bad),/asset|image|mime|binary|invalid/i);
  }
  assert.throws(()=>replaceBlockImage(page,"gallery-1","alt1",{filename,dataURL}),/image|src/i);
  assert.throws(()=>replaceBlockImage(page,"missing","src1",{filename,dataURL}),/block/i);
});

test("embedded image assets are bounded and ZIP files only permit safe raster destinations",()=>{
  const page=gallery();
  const result=replaceBlockImage(page,"gallery-1","src1",{filename,dataURL});
  assert.doesNotThrow(()=>createStoredZip([
    {name:"index.html",content:exportHtml(result)},
    {name:"assets/"+filename,content:getImageAssetBytes(result,filename)}
  ]));
  assert.throws(()=>createStoredZip([{name:"assets/custom-evil.svg",content:"<svg/>"}]),/path/i);
  assert.throws(()=>createStoredZip([{name:"assets/../steal.png",content:"x"}]),/path/i);
  assert.throws(()=>replaceBlockImage(page,"gallery-1","src1",{
    filename,dataURL:"data:image/png;base64,"+"A".repeat(4*1024*1024)
  }),/too large|size|image/i);
});

test("old editable gallery projects migrate missing image fields without losing text and links",()=>{
  const legacy = gallery();
  delete legacy.media;
  const block = legacy.blocks[0];
  block.props.text1 = "Retained editorial heading";
  block.props.href1 = "/portfolio";
  for (const name of Object.keys(block.props))
    if (/^(?:src|alt)\d+$/.test(name)) delete block.props[name];
  const imported = parseDocument(JSON.stringify(legacy));
  assert.equal(imported.blocks[0].props.text1, "Retained editorial heading");
  assert.equal(imported.blocks[0].props.href1, "/portfolio");
  assert.equal(imported.blocks[0].props.src1, createBlock("section:image-gallery").props.src1);
  assert.equal(imported.blocks[0].props.alt1, createBlock("section:image-gallery").props.alt1);
  assert.deepEqual(imported.media,{});
  assert.deepEqual(parseDocument(JSON.stringify(imported)), imported);
  const broken=structuredClone(legacy);
  delete broken.blocks[0].props.text1;
  assert.throws(()=>parseDocument(broken),/field.*string/i);
});

test("verifies actual imported and exported image bytes, not only the filename and MIME", async () => {
  const original = gallery();
  const valid = replaceBlockImage(original, "gallery-1", "src1", {filename, dataURL});
  assert.deepEqual(await verifyDocumentMedia(JSON.stringify(valid)), valid);
  const forged = structuredClone(valid);
  const fakeName = "custom-" + "0".repeat(64) + ".png";
  delete forged.media[filename];
  forged.media[fakeName] = dataURL;
  forged.blocks[0].props.src1 = "assets/" + fakeName;
  forged.blocks[0].props.href1 = "assets/" + fakeName;
  await assert.rejects(verifyDocumentMedia(JSON.stringify(forged)), /content hash mismatch/i);
  const changed = structuredClone(valid);
  changed.media[filename] = "data:image/png;base64," + Buffer.concat([raw, Buffer.from([1])]).toString("base64");
  await assert.rejects(verifyDocumentMedia(changed), /content hash mismatch/i);
  assert.deepEqual(await verifyDocumentMedia(original), original);
});
