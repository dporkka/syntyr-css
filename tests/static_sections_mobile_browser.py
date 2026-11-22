"""Optional Chromium regression: all static section exports fit 390px phones.

Run: SYNTYR_CHROMIUM_EXECUTABLE=/usr/bin/chromium-browser uv run --no-project --with playwright python3 tests/static_sections_mobile_browser.py
No network access, JavaScript runtime, or backend is required in the pages.
"""
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


def build_pages(destination):
    script = r"""
import fs from 'node:fs';
import path from 'node:path';
import {registerSectionManifest,createDefaultDocument,createBlock,exportHtml}
  from './docs/page-builder-model.mjs';
const manifest=JSON.parse(fs.readFileSync('./metadata/section-composer.v1.json','utf8'));
registerSectionManifest(manifest);
for(const item of manifest.sections){
  const doc=createDefaultDocument();
  doc.blocks=[createBlock('section:'+item.id, 'example-1')];
  fs.writeFileSync(path.join(process.argv[1],item.id+'.html'),exportHtml(doc));
}
fs.writeFileSync(path.join(process.argv[1],'ids.json'),
  JSON.stringify(manifest.sections.map(s=>s.id)));
"""
    subprocess.run(["node", "--input-type=module", "-e", script, str(destination)],
                   cwd=ROOT, check=True)
    (destination / "syntyr.all.css").write_bytes((ROOT / "dist/syntyr.all.css").read_bytes())
    (destination / "assets").mkdir()
    for asset in (ROOT / "assets").glob("*.svg"):
        (destination / "assets" / asset.name).write_bytes(asset.read_bytes())


def main():
    with TemporaryDirectory(prefix="syntyr-mobile-static-") as folder:
        folder = Path(folder)
        build_pages(folder)
        ids = json.loads((folder / "ids.json").read_text())
        failures = []
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                executable_path=os.environ.get("SYNTYR_CHROMIUM_EXECUTABLE"),
            )
            context = browser.new_context(viewport={"width": 390, "height": 844})
            page = context.new_page()
            for ident in ids:
                page.goto((folder / (ident + ".html")).as_uri(), wait_until="load")
                # Native loading="lazy" intentionally defers below-fold images.
                # Scroll them into view before evaluating broken-asset status.
                for img in page.locator("img").all():
                    img.scroll_into_view_if_needed()
                    expect(img).to_have_js_property("complete", True)
                data = page.evaluate("""() => ({
                  vw: innerWidth,
                  doc: document.documentElement.scrollWidth,
                  invalidIDs: [...document.querySelectorAll('[id]')].map(n=>n.id)
                    .filter((n,i,a)=>a.indexOf(n)!==i),
                  images: [...document.images].filter(i=>!i.complete||i.naturalWidth===0)
                    .map(i=>i.getAttribute('src')),
                })""")
                if data["doc"] > data["vw"] + 2 or data["invalidIDs"] or data["images"]:
                    failures.append((ident, data))
                if ident == "api-endpoint-reference":
                    code = page.locator("pre.syn-code-scroll")
                    assert code.count() == 2
                    assert all(code.nth(i).get_attribute("tabindex") == "0" for i in range(2))
                    assert code.nth(1).evaluate("(n)=>n.scrollWidth > n.clientWidth")
            browser.close()
        assert not failures, f"Invalid static mobile exports: {failures}"
        print(f"PASS {len(ids)} script-free exports at 390px, without horizontal document overflow")


if __name__ == "__main__":
    main()
