// Maintainer-only smoke: external Playwright for this test, not a Syntyr runtime dependency.
'use strict';
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const net = require('node:net');
const path = require('node:path');
const { setTimeout: delay } = require('node:timers/promises');
const { chromium, firefox } = require('playwright');

const ROOT = path.resolve(__dirname, '..');
async function getPort() {
  const s = net.createServer();
  await new Promise(resolve => s.listen(0, '127.0.0.1', resolve));
  const port = s.address().port;
  await new Promise(resolve => s.close(resolve));
  return port;
}
async function waitForServer(url) {
  for (let i = 0; i < 60; i++) {
    try { const r = await fetch(url); if (r.ok) return; } catch {}
    await delay(100);
  }
  throw new Error('Python Geo demo did not start');
}

async function verify(engine, name, base) {
  const env = process.env['SYNTYR_TEST_' + name.toUpperCase() + '_EXECUTABLE'];
  const browser = await engine.launch({ headless: true, ...(env ? { executablePath: env } : {}) });
  try {
    for (const width of [320, 390, 1280]) {
      const page = await browser.newPage({ viewport: { width, height: 820 }, javaScriptEnabled: false });
      const errors = [];
      page.on('pageerror', e => errors.push(e.message));
      await page.goto(base + '/');
      assert.equal(await page.getByRole('heading', {name: 'Asset availability workspace'}).count(), 1);
      assert.equal(await page.locator('.syn-geo-marker').count(), 6);
      const m = await page.evaluate(() => ({
        width: document.documentElement.scrollWidth,
        viewport: document.documentElement.clientWidth
      }));
      assert(m.width <= m.viewport + 1, `${name} ${width}px horizontal overflow: ${JSON.stringify(m)}`);
      assert.deepEqual(errors, []);
      await page.close();
    }

    const page = await browser.newPage({ viewport: { width: 390, height: 820 }, javaScriptEnabled: false });
    await page.goto(base + '/');
    await page.getByRole('searchbox').fill('east');
    await page.getByLabel('Availability').selectOption('available');
    await page.getByLabel('Format').selectOption('static');
    await page.getByRole('button', {name: 'Apply filters'}).click();
    assert(page.url().includes('query=east'));
    assert(page.url().includes('status=available'));
    assert.equal(await page.locator('.syn-geo-marker').count(), 2);
    assert.equal(await page.locator('#selection').getByRole('heading', {name:'East Junction'}).count(),1);
    await page.getByRole('link', {name:'Select East Vista'}).click();
    assert(page.url().includes('selected=EV-035'));
    await page.locator('#selection').getByRole('heading', {name:'East Vista'}).waitFor();
    assert.equal(await page.locator('#selection').getByRole('heading', {name:'East Vista'}).count(),1);
    assert.equal(await page.locator('.syn-geo-marker[aria-current="location"]').count(),1);

    // District navigation is a server-filtered facet, not a cosmetic map layer.
    await page.goto(base + '/?status=available&type=static');
    const districts = page.getByRole('navigation', {name: 'Browse districts'});
    await districts.getByRole('link', {name: 'East district (2)'}).click();
    assert(page.url().includes('district=East+district'), 'district GET navigation must preserve active status/type');
    assert(page.url().includes('status=available') && page.url().includes('type=static'));
    assert.equal(await page.locator('.syn-geo-marker').count(), 2);
    assert.equal(await page.locator('#selection').getByRole('heading', {name:'East Junction'}).count(), 1);
    await page.getByRole('link', {name:'Find East Vista on the schematic map'}).focus();
    await page.keyboard.press('Enter');
    assert(page.url().endsWith('#map-marker-EV-035'), 'record keyboard activation must navigate to the marker');
    assert.equal(await page.evaluate(() => document.activeElement?.id), 'map-marker-EV-035', 'fragment navigation must focus the named marker');
    await page.getByRole('link', {name:'Select East Vista'}).focus();
    await Promise.all([
      page.waitForURL(url => url.searchParams.get('selected') === 'EV-035'),
      page.keyboard.press('Enter'),
    ]);
    assert(page.url().includes('district=East+district') && page.url().includes('selected=EV-035'));
    await page.locator('#selection').getByRole('heading', {name:'East Vista'}).waitFor();
    assert.equal(await page.locator('#selection').getByRole('heading', {name:'East Vista'}).count(), 1);
    await page.getByRole('combobox', {name:'District'}).selectOption('North district');
    await page.getByRole('button', {name: 'Apply filters'}).click();
    assert(page.url().includes('district=North+district'));
    assert.equal(await page.locator('.syn-geo-marker').count(), 1);
    assert.equal(await page.locator('#selection').getByRole('heading', {name:'North Ridge'}).count(), 1);

    await page.goto(base + '/?query=no-such-asset');
    assert.equal(await page.locator('.syn-geo-marker').count(), 0);
    assert.equal(await page.locator('#selection').count(), 0);
    assert.equal(await page.getByRole('status').filter({hasText:'No assets match'}).count(),1);

    await page.goto(base + '/');
    await page.evaluate(() => document.documentElement.style.fontSize = '64px');
    const zoom = await page.evaluate(() => ({
      width: document.documentElement.scrollWidth,
      viewport: document.documentElement.clientWidth
    }));
    if (zoom.width > zoom.viewport + 1) {
      const offenders = await page.evaluate(() => [...document.body.querySelectorAll('*')]
        .map(e => ({ tag: e.tagName.toLowerCase(), classes: String(e.className).slice(0,75),
          rect: e.getBoundingClientRect().toJSON(), scroll: e.scrollWidth,
          text: e.textContent.trim().slice(0,38) }))
        .filter(e => e.rect.right > document.documentElement.clientWidth + 2 && e.rect.width > 2)
        .sort((a,b) => b.rect.right-a.rect.right).slice(0,18));
      console.error('OVERFLOW_OFFENDERS', JSON.stringify(offenders));
    }
    assert(zoom.width <= zoom.viewport + 1, `${name} high-text zoom overflow: ${JSON.stringify(zoom)}`);
    await page.evaluate(() => {
      document.documentElement.style.fontSize = '';
      document.body.dir = 'rtl';
    });
    const rtl = await page.locator('.syn-geo-marker').first().evaluate(marker => {
      const viewport = marker.closest('.syn-geo-viewport').getBoundingClientRect();
      const rect = marker.getBoundingClientRect();
      return ((rect.left + rect.right)/2 - viewport.left) / viewport.width;
    });
    assert(Math.abs(rtl - 0.20) < 0.04, `${name} RTL marker shifted: ${rtl}`);
    await page.close();

    const forced = await browser.newPage({ viewport: {width: 390, height: 820}, forcedColors: 'active' });
    await forced.goto(base + '/');
    assert.equal(await forced.locator('.syn-geo-marker[aria-current="location"]').count(),1);
    await forced.close();
    console.log('PASS', name, 'server filters, district drill-down, selection, RTL, 320/390/1280, enlarged text, forced colors, no JS');
  } finally {
    await browser.close();
  }
}

async function main() {
  const port = await getPort();
  const base = 'http://127.0.0.1:' + port;
  const proc = spawn('python3', ['examples/geo_operations_server.py', '--port', String(port)], {
    cwd: ROOT, stdio: 'ignore'
  });
  try {
    await waitForServer(base + '/');
    for (const name of (process.env.SYNTYR_TEST_BROWSERS || 'chromium,firefox').split(',')) {
      const engine = { chromium, firefox }[name];
      if (!engine) throw Error('Unknown browser ' + name);
      await verify(engine, name, base);
    }
  } finally {
    const exited = new Promise(resolve => proc.once('exit', resolve));
    proc.kill('SIGTERM');
    await Promise.race([exited, delay(1500)]);
    if (proc.exitCode === null && proc.signalCode === null) proc.kill('SIGKILL');
  }
}
main().catch(e => { console.error(e); process.exitCode=1; });
