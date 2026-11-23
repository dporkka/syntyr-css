import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {registerSectionManifest} from "../docs/page-builder-model.mjs";
import {parseSiteProject, exportSitePages} from "../docs/site-builder-model.mjs";
import {STARTER_SITE_KITS, createStarterSite} from "../docs/page-builder-site-kits.mjs";

registerSectionManifest(JSON.parse(readFileSync(new URL("../metadata/section-composer.v1.json", import.meta.url))));

test("four distinct complete website kits have editable, validated multi-page structure", () => {
  assert.deepEqual(STARTER_SITE_KITS.map(item => item.id), ["portfolio", "agency", "saas", "small-business"]);
  for (const kit of STARTER_SITE_KITS) {
    const site = createStarterSite(kit.id);
    assert.equal(site.schema, "syntyr.site.v1");
    assert.ok(site.pages.length >= 3 && site.pages.length <= 10);
    assert.equal(site.pages[0].slug, "");
    assert.equal(new Set(site.pages.map(item => item.slug)).size, site.pages.length);
    assert.deepEqual(parseSiteProject(JSON.stringify(site)), site);
    assert.equal(site.shared.header.type, "header");
    assert.equal(site.shared.footer.type, "footer");
    assert.ok(site.pages.every(item => item.document.theme === site.pages[0].document.theme));
    assert.ok(site.pages.every(item => item.document.blocks[0].type === "hero"));
    assert.ok(site.pages.every(item => !item.document.blocks.some(block => block.type === "footer" || block.type === "header")));
    assert.ok(site.pages.every(item => item.document.title.includes("Example")));
    assert.ok(new Set(site.pages.map(item => item.document.blocks[0].props.title)).size >= 3);
    const paths = new Set(site.pages.map(item => item.slug ? "/" + item.slug + "/" : "/"));
    assert.ok(paths.has(site.shared.header.props.linkHref), "Shared navigation must lead to a real page");
    const htmlFiles = exportSitePages(site);
    assert.equal(htmlFiles.length, site.pages.length);
    assert.ok(htmlFiles.every(file => file.content.includes("syntyr.all.css")));
    assert.ok(htmlFiles.every(file => (file.content.match(/<footer\b/g) || []).length === 1));
    assert.ok(htmlFiles.every(file => (file.content.match(/<header\b/g) || []).length === 1));
    assert.ok(htmlFiles.every(file => !/<script\b|<iframe\b| onerror=/i.test(file.content)));
    assert.ok(htmlFiles.every(file => !/trusted by 10,000|verified customer|award-winning/i.test(file.content)));
  }
});

test("site kits are independent copies and reject unknown identifiers", () => {
  const first = createStarterSite("saas");
  first.pages[0].document.blocks[0].props.title = "Changed locally";
  first.shared.header.props.brand = "Edited";
  const second = createStarterSite("saas");
  assert.notEqual(second.pages[0].document.blocks[0].props.title, "Changed locally");
  assert.notEqual(second.shared.header.props.brand, "Edited");
  assert.throws(() => createStarterSite("../etc"), /unknown site kit/i);
});
