"""HTMX recipe catalog and the removable, CSS-only state adapter."""
from pathlib import Path
import json
import re
import unittest

from scripts.build_cloudflare_site import PUBLIC_DOCS, source_files

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = "integrations/htmx/syntyr.htmx.css"
PATTERNS = (
    "Live search", "Pagination", "Sortable table", "Inline edit",
    "Dependent select", "Validated form", "Lazy-loaded navigation", "Popover details",
    "Infinite scroll", "Bulk actions", "Polled status", "Request feedback",
)


class HtmxComponentCatalogTests(unittest.TestCase):
    def test_adapter_is_optional_and_isolated_from_all_core_distributions(self):
        adapter = (ROOT / ADAPTER).read_text()
        pkg = json.loads((ROOT / "package.json").read_text())
        self.assertEqual(pkg["exports"]["./htmx.css"], "./" + ADAPTER)
        self.assertIn("integrations/htmx/", pkg["files"])
        self.assertIn(ADAPTER, source_files())
        self.assertIn(".syn-root", adapter)
        self.assertIn("htmx-request", adapter)
        self.assertIn("htmx-swapping", adapter)
        self.assertIn("prefers-reduced-motion", adapter)
        self.assertNotIn("!important", adapter)
        self.assertNotIn("@import", adapter)
        self.assertNotIn("url(", adapter)
        self.assertNotIn("<script", adapter.lower())
        self.assertNotIn("syntyr.htmx.css", (ROOT / "scripts/build.py").read_text())
        from scripts.package_release import FILES
        self.assertIn(ADAPTER, FILES)
        self.assertIn("docs/htmx-components.md", FILES)

    def test_markdown_catalog_has_twelve_distinct_copyable_recipes(self):
        guide = (ROOT / "docs/htmx-components.md").read_text()
        self.assertIn("htmx-components.md", PUBLIC_DOCS)
        for index, title in enumerate(PATTERNS, start=1):
            self.assertEqual(guide.count(f"### {index}. {title}"), 1, title)
        self.assertGreaterEqual(guide.count(chr(96) * 3 + "html"), len(PATTERNS))
        self.assertIn("action=", guide)
        self.assertIn('method="get"', guide)
        self.assertIn("HX-History-Restore-Request", guide)
        self.assertIn("CSRF", guide)
        self.assertIn("aria-live", guide)
        self.assertIn("HTMX 2", guide)
        self.assertIn("HTMX 4", guide)

    def test_catalog_is_discoverable_in_static_site_and_agent_index(self):
        self.assertIn("htmx-components", (ROOT / "llms.txt").read_text())
        self.assertIn("htmx-components.html", (ROOT / "docs/guides.html").read_text())
        self.assertIn("htmx-components.html", (ROOT / "docs/reference.html").read_text())
        self.assertIn("htmx-components.html", (ROOT / "docs/framework-integrations.md").read_text())
        site_files = source_files()
        self.assertIn("docs/htmx-components.md", site_files)
        self.assertIn("docs/htmx-components.html", site_files)


if __name__ == "__main__":
    unittest.main()
