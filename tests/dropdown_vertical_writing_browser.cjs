/* Optional real-browser containment regression for vertical writing modes.
   NODE_PATH points at a local Playwright developer install; Syntyr runtime stays CSS-only. */
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const {pathToFileURL} = require('node:url');
const path = require('node:path');

(async () => {
  const root = path.resolve(__dirname, '..');
  const executablePath = process.env.SYNTYR_CHROMIUM;
  const browser = await chromium.launch({headless:true, executablePath, args:['--no-sandbox']});
  try {
    for (const viewport of [{width:1280,height:400},{width:320,height:200}]) {
      for (const mode of ['horizontal-tb','vertical-rl']) {
        const context = await browser.newContext({viewport, reducedMotion:'reduce'});
        const page = await context.newPage();
        const errors=[];
        page.on('pageerror', error=>errors.push(String(error)));
        await page.goto(pathToFileURL(path.join(root,'examples/dropdowns.html')).href);
        await page.evaluate(({mode})=>{
          const popover=document.querySelector('#actions-panel');
          popover.style.writingMode=mode;
          const close=popover.querySelector('[popovertargetaction="hide"]');
          for(let i=0;i<42;i++){
            const link=document.createElement('a');
            link.className='syn-dropdown__item';
            link.href='#';
            link.textContent='Action '+i+' — some deliberately long content for viewport containment';
            close.before(link);
          }
        },{mode});
        await page.locator('#actions-trigger').click();
        await page.waitForFunction(()=>document.querySelector('#actions-panel').matches(':popover-open'));
        const bounds=await page.locator('#actions-panel').boundingBox();
        const metrics=await page.locator('#actions-panel').evaluate(el=>({
          width:el.getBoundingClientRect().width,
          height:el.getBoundingClientRect().height,
          clientWidth:el.clientWidth,
          clientHeight:el.clientHeight,
          scrollHeight:el.scrollHeight,
          scrollWidth:el.scrollWidth,
          writingMode:getComputedStyle(el).writingMode,
          maxHeight:getComputedStyle(el).maxHeight,
          maxWidth:getComputedStyle(el).maxWidth,
        }));
        console.log(JSON.stringify({viewport,mode,bounds,metrics}));
        assert.ok(bounds.x>=-1 && bounds.y>=-1 &&
          bounds.x+bounds.width<=viewport.width+1 &&
          bounds.y+bounds.height<=viewport.height+1,
          'dropdown exceeds viewport: '+JSON.stringify({viewport,mode,bounds,metrics}));
        assert.deepEqual(errors,[]);
        await page.keyboard.press('Escape');
        assert.equal(await page.locator('#actions-panel').evaluate(el=>el.matches(':popover-open')),false);
        await context.close();
      }
    }
    console.log('PASS: actual Chromium dropdown viewport containment for normal and vertical writing');
  } finally {await browser.close()}
})().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
