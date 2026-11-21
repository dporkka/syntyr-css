"""Real browser stress test for text resize and 320px reflow.

Run in a developer-only Playwright environment:
    PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/chromium-browser python3 tests/reflow_test.py

This changes the document's root font size and is a *text-size stress test*,
not proof of real browser 200%/400% zoom or WCAG certification.
Horizontal scrolling *inside* the tabular-data widget remains allowed.
"""
import argparse
import os
from pathlib import Path
import shutil
import sys

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "index.html", "docs/index.html", "docs/catalog.html", "docs/blocks.html", "docs/guides.html", "docs/reference.html",
    "examples/landing.html", "examples/viz.html", "examples/console.html",
    "examples/resources.html", "examples/pricing.html",
    "docs/console-kit.html", "examples/saas.html", "examples/settings-billing.html",
         "examples/app-onboarding.html", "examples/app-team.html", "examples/app-notifications.html",
         "examples/app-integrations.html", "examples/app-security.html",
         "examples/app-account.html", "examples/app-audit.html", "examples/app-support.html", "examples/app-states.html",
    "examples/business.html", "examples/terminal.html",
         "examples/geometry-terminal.html",
         "examples/operations-console.html", "examples/themes.html",
    "examples/vertigo-admin.html", "examples/vertigo-resource-workflow.html", "examples/saas-workflows.html", "examples/crm.html", "examples/minimalist-patterns.html",
    "examples/design-states.html", "examples/symbols.html", "examples/native-elements.html",
    "examples/native-apis.html", "examples/flagship-studio.html", "examples/flagship-noir.html", "examples/flagship-grid.html",
    "examples/semantic-starter.html", "examples/workflow-steps.html", "examples/enterprise-compositions.html", "examples/premium-compositions.html", "examples/operation-revisions.html",
)


def check_page(browser, path: str, width: int, scale: float) -> None:
    context = browser.new_context(viewport={"width": width, "height": 850})
    page = context.new_page()
    try:
        page.goto((ROOT / path).as_uri())
        page.evaluate("(scale) => { document.documentElement.style.fontSize = (16 * scale) + 'px'; }", scale)
        inspect_overflow = """() => {
            const root=document.documentElement;
            const clipped = Array.from(document.querySelectorAll('a, button, input, select, textarea, summary'))
              .filter(e => {
                const r=e.getBoundingClientRect(), s=getComputedStyle(e);
                if(s.display==='none'||s.visibility==='hidden'||r.width===0||r.height===0) return false;
                // Closed native details conceal their content even if a child computes a display value.
                if(e.closest('details:not([open])') && !e.closest('summary')) return false;
                // Keep naturally horizontal data regions scrollable while
                // rejecting links clipped by regular containers.
                if(e.closest('.syn-table-wrap')) return false;
                const pipeline = e.closest('.syn-pipeline');
                if(pipeline && pipeline.matches('[tabindex="0"][aria-label]') &&
                   getComputedStyle(pipeline).overflowX === 'auto' &&
                   pipeline.scrollWidth > pipeline.clientWidth) {
                  // Horizontal pipeline scrolling can reveal distant controls,
                  // but cannot reveal content clipped by a nested fixed card.
                  let obscured = false;
                  for(let ancestor=e.parentElement; ancestor && ancestor!==pipeline;
                      ancestor=ancestor.parentElement) {
                    const overflowX=getComputedStyle(ancestor).overflowX;
                    if(overflowX!=='hidden' && overflowX!=='clip') continue;
                    const bounds=ancestor.getBoundingClientRect();
                    if(r.left < bounds.left - 1 || r.right > bounds.right + 1) {
                      obscured = true;
                      break;
                    }
                  }
                  // This is a genuine clipped control even if its bounding
                  // box happens to remain within the document viewport.
                  if(obscured) return true;
                  return false;
                }
                return r.left < -1 || r.right > innerWidth + 1;
              }).slice(0,5).map(e=>[e.tagName, e.textContent.trim().slice(0,35),
                 Math.round(e.getBoundingClientRect().left),Math.round(e.getBoundingClientRect().right)]);
            return {scrollWidth:root.scrollWidth, clientWidth:root.clientWidth, clipped};
        }"""
        if path == 'examples/native-elements.html' and width == 320:
            # Native file-picker shadow content must not stretch the grid,
            # including WebKit at 2x/200% enlarged text.
            fieldset = page.get_by_role('group', name='Native inputs')
            dims = fieldset.evaluate('e => ({client: e.clientWidth, scroll: e.scrollWidth})')
            assert dims['scroll'] <= dims['client'] + 1, (path, width, scale, dims)
        data = page.evaluate(inspect_overflow)
        assert data["scrollWidth"] <= data["clientWidth"] + 1 and not data["clipped"], (
            f"{path}: viewport={width}px, font scale={scale}x: {data}"
        )
        if path == 'examples/crm.html':
            # The pipeline is intentionally scrollable horizontally and must
            # remain keyboard-focusable and named for assistive technology.
            pipeline = page.locator('.syn-pipeline')
            assert pipeline.count() == 1
            assert pipeline.get_attribute('tabindex') == '0'
            assert pipeline.get_attribute('aria-label')
            assert pipeline.evaluate("e => getComputedStyle(e).overflowX") == 'auto'
            assert pipeline.evaluate('e => e.scrollWidth > e.clientWidth')
            if width == 320 and scale == 2:
                # A scrollable pipeline must not exempt a control clipped by
                # an intermediate, non-scrollable card. This catches a false
                # negative in the root-overflow inspection logic.
                pipeline.evaluate("""e => {
                    const card = document.createElement('div');
                    card.id = 'syn-clipped-card-fixture';
                    card.style.cssText = 'position:fixed;left:10px;top:10px;inline-size:40px;overflow-x:hidden;';
                    const control = document.createElement('button');
                    control.textContent = 'INTENTIONAL CLIPPED FIXTURE';
                    // Keep the button wholly inside the viewport. The only
                    // accessibility defect should be the ancestor's clipping.
                    control.style.cssText = 'inline-size:120px;min-inline-size:120px;display:block;';
                    card.append(control);
                    e.append(card);
                }""")
                try:
                    clipped = page.evaluate(inspect_overflow)['clipped']
                    assert any('INTENTIONAL CLIPPED FIXTURE' in c[1] for c in clipped), clipped
                finally:
                    page.locator('#syn-clipped-card-fixture').evaluate('e => e.remove()')
                # A named, horizontally scrolling board must also be operable
                # from the keyboard, not merely discoverable by screen readers.
                pipeline.evaluate('e => e.scrollLeft = 0')
                pipeline.focus()
                page.keyboard.press('ArrowRight')
                page.wait_for_function(
                    "document.querySelector('.syn-pipeline').scrollLeft > 0",
                    timeout=3000,
                )

        mobile_menu = page.locator('details.site-mobile-menu')
        if mobile_menu.count() and mobile_menu.is_visible():
            mobile_menu.evaluate('e => e.open = true')
            bounds = mobile_menu.locator('nav').evaluate("""e => {
                const r = e.getBoundingClientRect();
                return {left: r.left, right: r.right};
            }""")
            assert bounds['left'] >= -1 and bounds['right'] <= width + 1, (
                f"{path}: expanded menu clipped at {width}px and {scale}x: {bounds}"
            )
    finally:
        context.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browsers", nargs="+", default=["chromium"],
                        choices=["chromium", "firefox", "webkit"])
    args = parser.parse_args()
    failed = 0
    with sync_playwright() as p:
        for engine in args.browsers:
            opts = {"headless": True}
            if engine == "chromium":
                binary = os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE") or shutil.which("chromium") or shutil.which("chromium-browser")
                if binary:
                    opts.update(executable_path=binary, args=["--no-sandbox"])
            if engine == "webkit":
                custom_webkit = os.getenv("SYNTYR_WEBKIT_EXECUTABLE")
                if custom_webkit:
                    opts["executable_path"] = custom_webkit
            try:
                browser = getattr(p, engine).launch(**opts)
            except Exception as e:
                failed += 1
                print(f"BLOCKED {engine}: {e}")
                continue
            for path in PAGES:
                for width, scale in ((320, 1), (320, 1.5), (320, 2), (390, 2)):
                    try:
                        check_page(browser, path, width, scale)
                    except Exception as e:
                        print(f"FAIL {engine}: {e}", flush=True)
                        failed += 1
            browser.close()
            print(f"FINISHED {engine}: {len(PAGES)*4} reflow cases", flush=True)
    return int(bool(failed))


if __name__ == "__main__":
    sys.exit(main())
