import {createComposer} from "./composition-model.mjs";
import {exportHtml} from "./page-builder-model.mjs";
import {createStoredZip} from "./page-builder-zip.mjs";

const RELEASE = "0.3.0-alpha.5";
const byId = id => document.getElementById("composition-" + id);
const presets = {
  saas: {title:"SaaS landing page",theme:"studio",requirements:["product-intro","features","pricing","faq","call-to-action"]},
  crm: {title:"CRM dashboard",theme:"noir",requirements:["pipeline","metrics","inventory-search","account-management"]}
};
let composer, current = null, order = [];
const status = message => { byId("status").textContent = message; };
function invalidate() {
  current = null;
  byId("preview").srcdoc = "";
  byId("obligations").replaceChildren();
  byId("json").disabled = byId("zip").disabled = true;
}
function preview(project) {
  const doc = new DOMParser().parseFromString(exportHtml(project,{previewAssets:true}),"text/html");
  doc.querySelector('link[rel="stylesheet"]').setAttribute("href","../dist/syntyr.all.css");
  for (const a of doc.querySelectorAll("a[href]")) a.removeAttribute("href");
  const csp = doc.createElement("meta");
  csp.httpEquiv = "Content-Security-Policy";
  const origin = /^https?:$/.test(location.protocol) ? location.origin : "'self'";
  csp.content = "default-src 'none'; style-src 'self' " + origin + "; img-src 'self' data: " + origin + "; base-uri 'none'; form-action 'none'";
  doc.head.prepend(csp);
  return "<!doctype html>" + doc.documentElement.outerHTML;
}
function render() {
  invalidate();
  try {
    const request = {release:RELEASE,title:byId("title").value,theme:byId("theme").value,requirements:[...order]};
    const plan = composer.planIntent(request);
    if (!plan.ready) throw new Error("Unsupported requirements: " + plan.unresolved.join(", "));
    const output = composer.compose(plan.composition);
    byId("preview").srcdoc = preview(output.project);
    for (const item of plan.coverage) {
      const li = document.createElement("li");
      li.textContent = item.id + ": " + (item.host_requirements.join("; ") || "Review sample content and links.");
      byId("obligations").append(li);
    }
    current = output;
    byId("json").disabled = byId("zip").disabled = false;
    status(output.project.blocks.length + " canonical sections generated. Offline validation not run.");
  } catch (error) { status("Cannot generate: " + error.message); }
}
function applyPreset(preset) {
  byId("title").value = preset.title;
  byId("theme").value = preset.theme;
  order = [...preset.requirements];
  for (const input of byId("intents").querySelectorAll("input")) input.checked = order.includes(input.value);
  render();
}
async function read(path) {
  const response = await fetch(new URL(path,import.meta.url),{credentials:"same-origin"});
  if (!response.ok) throw new Error("Required local file unavailable");
  return response;
}
function download(filename, data, type) {
  const url = URL.createObjectURL(new Blob([data],{type}));
  const a = document.createElement("a");
  a.href=url; a.download=filename; document.body.append(a); a.click(); a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),30000);
}
byId("generate").addEventListener("click",render);
for (const field of ["title","theme"]) byId(field).addEventListener("input",()=>{invalidate();status("Requirements changed. Generate again.");});
byId("json").addEventListener("click",()=>{if(current) download("syntyr-page.json",JSON.stringify(current.project,null,2),"application/json");});
byId("zip").addEventListener("click",async()=>{
  const output=current;
  if(!output) return;
  byId("zip").disabled=true;
  try {
    const entries=[{name:"index.html",content:output.html},
      {name:"syntyr.all.css",content:await (await read("../dist/syntyr.all.css")).text()},
      {name:"LICENSE",content:await (await read("../LICENSE")).text()},
      {name:"README.txt",content:"Syntyr candidate presentation scaffold. Review sample content and routes. Host data and form handling are not implemented. Offline validation has not run.\n"}];
    for(const asset of output.assets) {
      if(!/^(?:gallery-[a-z0-9-]+|syntyr-mark)\.svg$/.test(asset)) throw new Error("Unsupported asset");
      entries.push({name:"assets/"+asset,content:new Uint8Array(await (await read("../assets/"+asset)).arrayBuffer())});
    }
    if(current!==output) return;
    download("syntyr-composition.zip",createStoredZip(entries),"application/zip");
    status("Portable HTML/CSS ZIP downloaded. Review before publishing.");
  } catch(error) { if(current===output) status("Export failed: "+error.message); }
  finally { byId("zip").disabled=!current; }
});
try {
  composer=createComposer(await (await read("../metadata/section-composer.v1.json")).json(),RELEASE);
  for(const intent of composer.listIntents(RELEASE).intents) {
    const label=document.createElement("label"), input=document.createElement("input");
    input.type="checkbox"; input.value=intent.id;
    label.append(input,document.createTextNode(intent.id.replaceAll("-"," ")));
    input.addEventListener("change",()=>{
      order=input.checked?[...order,input.value]:order.filter(id=>id!==input.value);
      invalidate();status("Requirements changed. Generate again.");
    });
    byId("intents").append(label);
  }
  byId("intents").disabled=byId("generate").disabled=false;
  for(const button of document.querySelectorAll("[data-preset]")) {
    button.disabled=false;
    button.addEventListener("click",()=>applyPreset(presets[button.dataset.preset]));
  }
  applyPreset(presets.saas);
} catch(error) { status("Cannot load composer: "+error.message); }
