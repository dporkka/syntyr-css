"""Focused optional browser checks for the progressive documentation search."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / "docs/reference.html").as_uri()

with sync_playwright() as p:
    for engine in ("chromium", "firefox"):
        with getattr(p, engine).launch(headless=True) as browser:
            for width in (320, 1280):
                page = browser.new_page(viewport={"width": width, "height": 820})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(URL)
                search = page.get_by_role("searchbox", name="Search guides")
                search.wait_for(timeout=2000)
                links = page.locator(".docs-reference-group li")
                total = links.count()
                assert total >= 80
                assert links.filter(visible=True).count() == total
                assert (ROOT / "VERSION").read_text().strip() in page.locator("#docs-search-scope").inner_text()
                search.fill("sveltekit")
                assert 0 < links.filter(visible=True).count() < total
                assert page.locator('a[href="framework-integrations.html"]').is_visible()
                search.fill("no-such-guide-zzzz-936")
                assert links.filter(visible=True).count() == 0
                assert "No matching guides" in page.get_by_role("status").inner_text()
                search.fill("")
                assert links.filter(visible=True).count() == total
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
                assert not errors, errors
                page.close()
            page = browser.new_page(java_script_enabled=False)
            page.goto(URL)
            assert page.locator(".docs-reference-group li:visible").count() == total
            assert not page.get_by_role("searchbox", name="Search guides").is_visible()
            page.close()
            print(f"PASS {engine} {browser.version}: search 320/1280 and no-JS fallback")
