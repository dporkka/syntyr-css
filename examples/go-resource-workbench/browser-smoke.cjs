// Maintainer-only browser checks. Requires a separately installed Playwright;
// neither Playwright nor JavaScript ships as a Syntyr runtime dependency.
const { chromium, firefox } = require("playwright");
const assert = require("node:assert/strict");
const { spawn, spawnSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { setTimeout: delay } = require("node:timers/promises");
const net = require("node:net");

async function port() {
  const server = net.createServer();
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const assigned = server.address().port;
  await new Promise(resolve => server.close(resolve));
  return assigned;
}
async function available(url) {
  for (let i=0; i<70; i++) {
    try { const r=await fetch(url); if (r.ok) return; } catch {}
    await delay(100);
  }
  throw new Error("Go demo did not start");
}
async function run(browserType, name, base) {
  const bin = process.env["SYNTYR_TEST_" + name.toUpperCase() + "_EXECUTABLE"];
  const browser = await browserType.launch({
    headless: true,
    ...(bin ? { executablePath: bin } : {}),
  });
  try {
    for (const width of [320,390,1280]) {
      const page = await browser.newPage({viewport:{width,height:844},javaScriptEnabled:false});
      const errors = [];
      page.on("pageerror", e => errors.push(e.message));
      await page.goto(base+"/resources?theme=studio");
      assert.equal(await page.getByRole("heading",{name:"Resource workbench"}).count(),1);
      assert.equal(await page.getByRole("table").count(),1);
      const metrics = await page.evaluate(() => ({
        scroll:document.documentElement.scrollWidth,
        view:document.documentElement.clientWidth,
        searchbox:document.querySelector('input[type="search"]')?.getAttribute("id"),
      }));
      assert(metrics.scroll <= metrics.view+1, `${name} at ${width}px overflows horizontally: ${JSON.stringify(metrics)}`);
      assert(metrics.searchbox, "Search must use a native labeled input");
      await page.close();
    }

    const page=await browser.newPage({viewport:{width:390,height:844},javaScriptEnabled:false});
    await page.goto(base+"/resources?theme=grid");
    assert.equal(await page.locator("[data-syn-theme=grid]").count(),1);
    await page.getByRole("searchbox").fill("harbor");
    await page.getByLabel("Status").selectOption("review");
    await page.getByRole("button",{name:"Apply view"}).click();
    await page.getByRole("heading",{name:"Resources",exact:true}).waitFor();
    assert(page.url().includes("q=harbor"),"GET search should persist query in URL");
    assert(page.url().includes("status=review"),"GET search should persist status in URL");
    assert.equal(await page.getByRole("row").count(),2,"one matching row and header");
    await page.getByRole("link",{name:/Harbor East/}).click();
    assert.equal(await page.getByRole("heading",{name:"Record details"}).count(),1);
    assert.equal(await page.locator("aside").getByText("Harbor East").count(),1);
    const preview=page.getByRole("link",{name:/Preview all 1 matching/});
    await preview.click();
    assert(await page.getByText("Preview only").count()>0);
    assert(await page.getByText("1 selected.").count()>0);
    await page.close();

    // A real native POST must work with browser JavaScript disabled, then PRG
    // must expose the updated record. Restore seeded values for the next engine.
    const editor=await browser.newPage({viewport:{width:390,height:844},javaScriptEnabled:false});
    await editor.goto(base+"/resources?id=RS-204&theme=grid");
    await editor.locator("#edit-owner").fill("Local Workshop");
    await editor.locator("#edit-status").selectOption("done");
    await editor.getByRole("button",{name:"Save local change"}).click();
    assert(editor.url().includes("id=RS-204"),"POST must redirect to saved inspector");
    assert(await editor.locator("aside").getByText("Local Workshop").count()>0,"edit must update server state");
    assert.equal(await editor.locator("aside").locator("dd").filter({hasText:"done"}).count(),1);
    await editor.locator("#edit-owner").fill("Operations");
    await editor.locator("#edit-status").selectOption("review");
    await editor.getByRole("button",{name:"Save local change"}).click();
    assert(await editor.locator("aside").getByText("Operations").count()>0,"seeded owner restored");
    await editor.close();

    const paged=await browser.newPage({viewport:{width:390,height:844},javaScriptEnabled:false});
    await paged.goto(base+"/resources?theme=grid&sort=name&columns_present=1&columns=owner");
    await paged.getByRole("link",{name:"Next"}).click();
    assert(paged.url().includes("page=2"),"server must navigate to the actual second page");
    assert(paged.url().includes("theme=grid") && paged.url().includes("columns=owner"),"page links must preserve view preferences");
    assert.equal(await paged.getByRole("row").count(),4,"pagination must render only three rows plus header");
    assert.equal(await paged.getByRole("link",{name:/Transit Hub/}).count(),1);
    assert.equal(await paged.getByRole("link",{name:/Airport Loop/}).count(),0);
    await paged.getByRole("checkbox",{name:/Select RS-442/}).check();
    await paged.getByRole("button",{name:"Preview checked"}).click();
    assert(paged.url().includes("page=2") && paged.url().includes("ids=RS-442"),"checked preview must retain visible-page context");
    assert(await paged.getByText("1 selected.").count()>0);
    await paged.close();

    const zoom=await browser.newPage({viewport:{width:320,height:740},javaScriptEnabled:false});
    await zoom.goto(base+"/resources?theme=studio");
    await zoom.evaluate(()=>document.documentElement.style.fontSize="64px");
    const zoomMetrics=await zoom.evaluate(()=>({
      scroll:document.documentElement.scrollWidth,
      view:document.documentElement.clientWidth,
    }));
    assert(zoomMetrics.scroll<=zoomMetrics.view+1,`${name} at 400% text zoom overflows: ${JSON.stringify(zoomMetrics)}`);
    await zoom.close();

    const forced=await browser.newPage({viewport:{width:390,height:844},javaScriptEnabled:false,forcedColors:"active"});
    await forced.goto(base+"/resources?theme=studio");
    const visible=await forced.getByRole("searchbox").evaluate(el=>{
      el.focus();
      return {outline:getComputedStyle(el).outlineStyle,display:getComputedStyle(el).display};
    });
    assert.notEqual(visible.display,"none");
    await forced.close();
    console.log("PASS",name,"320/390/1280, native GET filtering, pagination, inspector, bulk preview, 400% text, forced-colors, no-JS");
  } finally { await browser.close(); }
}
async function main(){
  const p=await port(), base="http://127.0.0.1:"+p;
  const buildDir=fs.mkdtempSync(path.join(process.env.TMPDIR||os.tmpdir(),"syntyr-workbench-"));
  const binary=path.join(buildDir,"demo");
  const build=spawnSync("go",["build","-o",binary,"."],{encoding:"utf8",env:process.env});
  if (build.status!==0) {
    fs.rmSync(buildDir,{recursive:true,force:true});
    throw Error("Go build failed: "+(build.stderr||build.error));
  }
  const proc=spawn(binary,["-addr","127.0.0.1:"+p],{stdio:"ignore"});
  try {
    await available(base+"/resources");
    const engines={chromium,firefox};
    for(const name of (process.env.SYNTYR_TEST_BROWSERS||"chromium,firefox").split(",")){
      if (!engines[name]) throw Error("Unsupported browser "+name);
      await run(engines[name],name,base);
    }
  } finally {
    const exited=new Promise(resolve=>proc.once("exit",resolve));
    proc.kill("SIGTERM");
    await Promise.race([exited,delay(1800)]);
    if (proc.exitCode===null && proc.signalCode===null) proc.kill("SIGKILL");
    fs.rmSync(buildDir,{recursive:true,force:true});
  }
}
main().catch(err=>{console.error(err);process.exitCode=1});
