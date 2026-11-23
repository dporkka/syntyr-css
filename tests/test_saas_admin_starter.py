"""Contracts for the standalone, dependency-free SaaS admin HTML starter."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import unittest

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "examples" / "saas-admin-starter"
PAGES = ("index.html", "pipeline.html", "customers.html", "billing.html")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.local_assets = []
        self.nav_current = []
        self.labels = set()
        self.controls = set()
        self.headings = []
        self.tables = 0
        self.captions = 0
        self.scripts = 0
        self.mains = 0
        self.forms = []
        self.landmarks = []

    def handle_starttag(self, tag, attr_list):
        attrs = dict(attr_list)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "a":
            self.links.append(attrs.get("href", ""))
            if attrs.get("aria-current") == "page":
                self.nav_current.append(attrs.get("href", ""))
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.local_assets.append(attrs.get("href", ""))
        if tag == "script":
            self.scripts += 1
        if tag == "main":
            self.mains += 1
        if tag == "nav":
            self.landmarks.append(attrs.get("aria-label"))
        if tag == "table":
            self.tables += 1
        if tag == "caption":
            self.captions += 1
        if tag == "form":
            self.forms.append((attrs.get("method"), attrs.get("action")))
        if tag == "label" and attrs.get("for"):
            self.labels.add(attrs["for"])
        if tag in {"input", "select", "textarea"} and attrs.get("id"):
            self.controls.add(attrs["id"])
        if tag in {"h1", "h2", "h3"}:
            self.headings.append(tag)


def parse(name):
    page = PageParser()
    page.feed((TEMPLATE / name).read_text(encoding="utf-8"))
    return page


class SaaSAdminStarter(unittest.TestCase):
    def test_four_navigable_complete_pages(self):
        for filename in PAGES:
            with self.subTest(filename=filename):
                page = parse(filename)
                self.assertEqual(page.mains, 1)
                self.assertIn("main", page.ids)
                self.assertIn("h1", page.headings)
                self.assertEqual(page.scripts, 0)
                self.assertEqual(page.nav_current, [filename])
                self.assertIn("Primary navigation", page.landmarks)
                self.assertEqual(len(page.ids), len(set(page.ids)), "duplicate id")
                self.assertIn("#main", page.links, "missing keyboard skip link")
                for route in PAGES:
                    self.assertIn(route, page.links)
                self.assertEqual(page.local_assets, ["../../dist/syntyr.core.css", "../../dist/syntyr.recipes.css", "styles.css"])
                for url in page.local_assets + page.links:
                    parsed = urlsplit(url)
                    self.assertFalse(parsed.scheme or parsed.netloc, "remote dependency not allowed")
                    if not parsed.path:
                        target = TEMPLATE / filename
                    else:
                        target = TEMPLATE / parsed.path
                    self.assertTrue(target.is_file(), f"broken link: {filename}: {url}")
                    if parsed.fragment and target.suffix == ".html":
                        self.assertIn(parsed.fragment, parse(target.name).ids, f"broken fragment: {url}")

    def test_dashboard_metrics_and_activity(self):
        page = parse("index.html")
        text = (TEMPLATE / "index.html").read_text()
        self.assertGreaterEqual(text.count("syn-stat-value"), 3)
        self.assertIn("Recent activity", text)
        self.assertIn("Illustrative", text)
        self.assertGreaterEqual(page.tables, 1)
        self.assertEqual(page.tables, page.captions)

    def test_pipeline_has_explicit_stages_without_fake_controls(self):
        text = (TEMPLATE / "pipeline.html").read_text()
        for heading in ("New", "Qualified", "Proposal", "Won"):
            self.assertIn(heading, text)
        self.assertIn('class="syn-pipeline starter-pipeline"', text)
        self.assertIn("customers.html#", text)
        self.assertNotIn("draggable=", text)
        self.assertIn("read-only", text.lower())

    def test_customers_provides_server_ready_get_search(self):
        page = parse("customers.html")
        text = (TEMPLATE / "customers.html").read_text()
        self.assertIn(("get", "customers.html"), page.forms)
        self.assertTrue({"query", "status"} <= page.labels)
        self.assertTrue({"query", "status"} <= page.controls)
        self.assertEqual(page.tables, page.captions)
        self.assertGreaterEqual(page.tables, 1)
        self.assertIn("server", text.lower())
        self.assertIn("aria-describedby", text)

    def test_billing_is_not_a_fake_checkout(self):
        text = (TEMPLATE / "billing.html").read_text()
        page = parse("billing.html")
        self.assertIn("Current plan", text)
        self.assertIn("Invoices", text)
        self.assertIn('disabled', text)
        self.assertIn("illustrative", text.lower())
        self.assertEqual(page.tables, page.captions)

    def test_scoped_responsive_css_and_public_discovery(self):
        css = (TEMPLATE / "styles.css").read_text()
        self.assertIn(".starter-", css)
        self.assertIn("@media", css)
        self.assertIn("forced-colors", css)
        self.assertNotIn("@import", css)
        self.assertNotIn("url(http", css)
        self.assertIn("saas-admin-starter/index.html", (ROOT / "docs/index.html").read_text())
        self.assertIn("saas-admin-starter/index.html", (ROOT / "README.md").read_text())
        publish = (ROOT / "scripts/build_cloudflare_site.py").read_text()
        for file in (*PAGES, "styles.css"):
            self.assertIn(f"saas-admin-starter/{file}", publish)


if __name__ == "__main__":
    unittest.main()
