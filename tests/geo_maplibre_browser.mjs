// Developer-only live MapLibre smoke test. Not shipped with Syntyr CSS.
// SYNTYR_VENDOR_NODE_MODULES=/path/to/app/node_modules node tests/geo_maplibre_browser.mjs
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { createServer } from "node:http";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const vendor = process.env.SYNTYR_VENDOR_NODE_MODULES;
if (!vendor) throw new Error("Set SYNTYR_VENDOR_NODE_MODULES to an app node_modules path");
const files = {
  pw: path.join(vendor, "playwright", "index.mjs"),
  esbuild: path.join(vendor, "esbuild", "lib", "main.js"),
  css: path.join(vendor, "maplibre-gl", "dist", "maplibre-gl.css"),
  worker: path.join(vendor, "maplibre-gl", "dist", "maplibre-gl-worker.mjs"),
};
for (const f of Object.values(files)) if (!existsSync(f)) throw new Error("Missing dev-only file: " + f);
const { chromium } = await import(pathToFileURL(files.pw).href);
const { build } = await import(pathToFileURL(files.esbuild).href);
const compiled = await build({
  stdin: { contents: 'import * as maplibregl from "maplibre-gl"; window.maplibregl = maplibregl;', resolveDir: vendor, sourcefile:"syntyr-geo-maplibre-entry.js" },
  platform: "browser", format: "iife", bundle: true, write: false, target: "es2022",
});
const script = compiled.outputFiles[0].text;
const workerBuild = await build({
  entryPoints: [files.worker],
  platform: "browser", format: "iife", bundle: true, write: false, target: "es2022",
});
const workerScript = workerBuild.outputFiles[0].text;
const publicFiles = new Map([
  ["/tests/fixtures/geo-maplibre.html", {content: await readFile(path.join(root, "tests/fixtures/geo-maplibre.html")), type: "text/html; charset=utf-8"}],
  ["/tests/fixtures/geo-maplibre-app.js", {content: await readFile(path.join(root, "tests/fixtures/geo-maplibre-app.js")), type: "text/javascript; charset=utf-8"}],
  ["/dist/syntyr.core.css", {content: await readFile(path.join(root, "dist/syntyr.core.css")), type: "text/css; charset=utf-8"}],
  ["/dist/syntyr.geo.css", {content: await readFile(path.join(root, "dist/syntyr.geo.css")), type: "text/css; charset=utf-8"}],
  ["/maplibre-bundle.js", {content:script, type: "text/javascript; charset=utf-8"}],
  ["/maplibre-worker.js", {content:workerScript, type: "text/javascript; charset=utf-8"}],
]);
const server = createServer((req, res) => {
  const resource = publicFiles.get(req.url?.split("?")[0]);
  if (!resource) {res.writeHead(404);res.end("Not Found");return;}
  res.writeHead(200, {"Content-Type":resource.type, "Cache-Control":"no-store"});
  res.end(resource.content);
});
await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
const base = "http://127.0.0.1:" + server.address().port;
let browser;
try {
  browser = await chromium.launch({ headless:true, ...(process.env.SYNTYR_GEO_CHROMIUM_PATH ? {executablePath:process.env.SYNTYR_GEO_CHROMIUM_PATH} : {}), args:["--no-sandbox","--enable-webgl","--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"] });
  for (const width of [1280, 390, 320]) {
    const page = await browser.newPage({ viewport:{width,height:900} });
    const pageErrors = [];
    page.on("pageerror", error => pageErrors.push(error.message));
    await page.route("**/*", route => route.request().url().startsWith(base + "/") ? route.continue() : route.abort());
    await page.goto(base + "/tests/fixtures/geo-maplibre.html");
    await page.addStyleTag({path:files.css});
    // Before app enhancement, the HTML must not advertise fake interactions.
    assert.equal(await page.locator("#site-search").isDisabled(),true);
    assert.equal(await page.locator("#site-status").isDisabled(),true);
    assert.equal(await page.locator("#geo-zoom").isDisabled(),true);
    assert.equal(await page.getByRole("navigation",{name:"Site list"}).getByRole("link").count(),0,
      "Static fallback site list must not link to unrelated details before the app is ready");
    assert.equal(await page.locator("#site-list li").count(),3);
    await page.addScriptTag({url:base + "/maplibre-bundle.js"});
    // The app fixture owns all UI state, MapLibre markers, filtering and camera behavior.
    // No client code or synthetic records ship with Syntyr CSS.
    await page.addScriptTag({url:base + "/tests/fixtures/geo-maplibre-app.js"});
    await page.waitForFunction(() => window.__geoMap?.loaded(), {timeout:12000});

    const nav=page.getByRole("navigation",{name:"Site list"});
    assert.equal(await nav.count(),1);
    assert.equal(await page.getByRole("heading",{name:"Site details"}).count(),1);
    assert.equal(await page.locator(".maplibregl-marker").count(),3);
    assert.equal(await page.locator(".syn-geo-marker").count(),3);
    assert.equal(await page.locator(".syn-geo-marker[aria-current=location]").count(),1);
    assert.equal(await nav.locator("a[aria-current=location]").count(),1);
    assert.equal(await page.locator("#site-selected-name").textContent(),"Site A");

    // A real MapLibre camera owns geographic positioning. Verify its marker
    // projection after programmatic camera movement (not just CSS coordinates).
    await nav.getByRole("link",{name:"Site C — active"}).focus();
    await page.keyboard.press("Enter");
    await page.waitForFunction(() => window.__geoFixture.getSelected()==="site-c");
    assert.equal(await page.locator("#site-selected-name").textContent(),"Site C");
    assert.equal(await page.evaluate(() => document.activeElement?.id),"site-details",
      "Native list links must focus the real details target without a custom focus trap");
    const position = await page.evaluate(()=>{
      const map=window.__geoMap;
      const marker=window.__geoFixture.markers.get("site-c");
      const lngLat=marker.getLngLat();
      const projected=map.project(lngLat);
      const mapRect=map.getContainer().getBoundingClientRect();
      const rect=marker.getElement().getBoundingClientRect();
      return {lng:lngLat.lng,lat:lngLat.lat,
        center:map.getCenter().toArray(),
        error:Math.hypot((rect.left+rect.right)/2-mapRect.left-projected.x,
                         (rect.top+rect.bottom)/2-mapRect.top-projected.y)};
    });
    assert(Math.abs(position.lng-(-73.85))<.00001 && Math.abs(position.lat-40.73)<.00001,
      "Marker does not store the expected synthetic longitude/latitude");
    assert(Math.abs(position.center[0]-position.lng)<.001 && Math.abs(position.center[1]-position.lat)<.001,
      "Selecting a site in the list must recenter the real MapLibre camera");
    assert(position.error<12,"MapLibre marker is not positioned at the projected coordinates: "+JSON.stringify(position));
    assert.equal(await page.locator(".syn-geo-marker[aria-current=location]").count(),1);
    assert.equal(await nav.locator("a[aria-current=location]").count(),1);

    // Native button semantics should activate markers using Enter and Space.
    await page.getByRole("button",{name:"Inspect Site B"}).focus();
    await page.keyboard.press("Enter");
    await page.waitForFunction(() => window.__geoFixture.getSelected()==="site-b");
    assert.equal(await page.locator("#site-selected-name").textContent(),"Site B");
    assert.equal(await page.locator("#site-selected-status").textContent(),"Maintenance");
    await page.getByRole("button",{name:"Inspect Site A"}).focus();
    await page.keyboard.press("Space");
    await page.waitForFunction(() => window.__geoFixture.getSelected()==="site-a");
    assert.equal(await page.locator("#site-selected-name").textContent(),"Site A");

    // The CSS shell must not fake filter behavior: when the application hides
    // a record, its actual MapLibre marker and list row also disappear.
    await page.getByRole("combobox",{name:"Site status"}).selectOption("maintenance");
    assert.equal(await page.locator(".maplibregl-marker").count(),1);
    assert.equal(await nav.locator("li:visible").count(),1);
    assert.equal(await page.locator("#site-selected-name").textContent(),"Site B");
    assert.equal(await page.locator("#site-count").textContent(),"1 fictional site in the list");
    assert.equal(await page.locator(".syn-geo-marker[aria-current=location]").count(),1);
    assert.equal(await nav.locator("a[aria-current=location]").count(),1);

    await page.getByRole("searchbox",{name:"Find a site"}).fill("no-matching-site");
    assert.equal(await page.locator(".maplibregl-marker").count(),0);
    assert.equal(await nav.locator("li:visible").count(),0);
    assert.equal(await page.locator("#site-selected-name").textContent(),"No matching sites");
    assert.equal(await page.locator(".syn-geo-marker[aria-current=location]").count(),0);
    assert.equal(await nav.locator("a[aria-current=location]").count(),0);
    assert.equal(await page.evaluate(() => window.__geoFixture.getSelected()),null);
    assert.equal(await page.evaluate(() => [...window.__geoFixture.markers.values()]
      .filter(marker => marker.getElement().dataset.synSelected === "true").length),0,
      "No results must leave no selected marker, even off-DOM");
    assert.equal(await page.evaluate(() => window.__geoFixture.selectSite("site-a")),false,
      "Invisible records must not be available to UI selection");

    await page.getByRole("searchbox",{name:"Find a site"}).fill("");
    await page.getByRole("combobox",{name:"Site status"}).selectOption("all");
    assert.equal(await page.locator(".maplibregl-marker").count(),3);
    assert.equal(await nav.locator("li:visible").count(),3);
    // B remains selected when it is still visible after clearing filters.
    assert.equal(await page.locator("#site-selected-name").textContent(),"Site B");
    assert.equal(await page.evaluate(() => window.__geoFixture.selectSite("site-missing")),false,
      "Client UI must not select an unknown record; real authorization still belongs on the server");
    assert.equal(await page.locator("#site-selected-name").textContent(),"Site B");

    const before = await page.evaluate(()=>window.__geoMap.getZoom());
    await page.getByRole("button",{name:"Zoom in"}).click();
    const after = await page.evaluate(()=>window.__geoMap.getZoom());
    if (after <= before) throw new Error("Zoom click did not change MapLibre zoom: " + before + " -> " + after);


    const layout=await page.evaluate(()=>{
      const box=e=>{const r=e.getBoundingClientRect();return [r.left,r.top,r.width,r.height]};
      return {
        overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth,
        columns:getComputedStyle(document.querySelector(".syn-geo-workspace")).gridTemplateColumns.trim().split(/\s+/).length,
        map:box(document.querySelector(".syn-geo-map")),
        markers:[...document.querySelectorAll(".syn-geo-marker")].map(box),
        overlay:getComputedStyle(document.querySelector(".syn-geo-overlay")).pointerEvents,
        controls:getComputedStyle(document.querySelector(".syn-geo-controls")).pointerEvents
      };
    });
    if (layout.overflow>1) throw new Error(width + "px horizontal overflow: " + layout.overflow);
    if (width === 390) {
      await page.emulateMedia({forcedColors:"active", reducedMotion:"reduce"});
      await page.keyboard.press("Tab"); // establish keyboard modality for :focus-visible
      await page.getByRole("button",{name:"Inspect Site B"}).focus();
      const outline=await page.getByRole("button",{name:"Inspect Site B"}).evaluate(el=>getComputedStyle(el).outlineStyle);
      if (outline === "none") throw new Error("No visible keyboard focus outline in forced colors");
      await page.keyboard.press("Enter");
      assert.equal(await page.locator("#site-selected-name").textContent(),"Site B");
    }
    if (layout.map[2]<=0 || layout.map[3]<=0) throw new Error(width+"px MapLibre mount collapsed");
    if (layout.markers.some(marker=>marker[2]<44 || marker[3]<44))
      throw new Error(width+"px marker target too small: "+JSON.stringify(layout.markers));
    if (layout.overlay!=="none" || layout.controls!=="auto") throw new Error("Overlay pointer events incorrect");
    if (width<=390 && layout.columns!==1) throw new Error(width+"px workspace did not stack: "+layout.columns);
    if (process.env.SYNTYR_GEO_SCREENSHOT_DIR) await page.screenshot({path:path.join(process.env.SYNTYR_GEO_SCREENSHOT_DIR,"syntyr-maplibre-"+width+".png"),fullPage:true});
    if (width === 1280) {
      for (const scale of [2, 4]) {
        await page.evaluate(s => { document.documentElement.style.fontSize = (16 * s) + "px"; }, scale);
        const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
        if (overflow > 1) throw new Error("Text reflow at " + scale + "x caused " + overflow + "px horizontal overflow");
      }
    }
    if (pageErrors.length) throw new Error("Uncaught browser errors: " + pageErrors.join("; "));
    await page.evaluate(()=>window.__geoMap.remove());
    await page.close();
    console.log("PASS MapLibre real marker/list/inspector/filter/keyboard/responsive at "+width+"px");
  }
} finally {
  try {
    await browser?.close();
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
}
