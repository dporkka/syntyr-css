"""SEO regression checks for the deployable Cloudflare Pages output."""
from __future__ import annotations

import json
import re
import unittest
from xml.etree import ElementTree

from scripts.build_cloudflare_site import SITE_URL, add_seo_metadata, source_files


def meta(html: str, name: str) -> str:
    found = re.search(r'<meta\s+name="' + re.escape(name) + r'"\s+content="([^"]*)"', html)
    return found.group(1) if found else ""


def canonical(html: str) -> list[str]:
    return re.findall(r'<link\s+rel="canonical"\s+href="([^"]+)"', html)


class SEOOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.site = source_files()

    def test_sitemap_uses_200_status_urls_and_excludes_nonindexable_pages(self):
        xml = ElementTree.fromstring(self.site["sitemap.xml"])
        locs = [node.text for node in xml.findall("{*}url/{*}loc")]
        self.assertTrue(locs)
        self.assertEqual(len(locs), len(set(locs)))
        self.assertIn(SITE_URL + "/", locs)
        self.assertIn(SITE_URL + "/docs/catalog", locs)
        self.assertIn(SITE_URL + "/docs/", locs)
        self.assertNotIn(SITE_URL + "/404", locs)
        self.assertFalse(any(url.endswith(".html") or url.endswith(".md") for url in locs))
        self.assertEqual(self.site["robots.txt"].decode().count(SITE_URL + "/sitemap.xml"), 1)

    def test_every_indexable_html_has_exactly_one_clean_self_canonical(self):
        sitemap = ElementTree.fromstring(self.site["sitemap.xml"])
        listed = {node.text for node in sitemap.findall("{*}url/{*}loc")}
        for path, contents in self.site.items():
            if not path.endswith(".html"):
                continue
            html = contents.decode()
            urls = canonical(html)
            clean = ("/" if path == "index.html" else "/" + path[:-10]
                     if path.endswith("/index.html") else "/" + path[:-5])
            target = SITE_URL + clean
            if target in listed:
                self.assertEqual(urls, [target], path)
                self.assertNotIn("noindex", meta(html, "robots").lower(), path)
            else:
                self.assertIn("noindex", meta(html, "robots").lower(), path)
                self.assertNotIn(target, listed)

    def test_structured_data_identifies_software_and_docs_breadcrumbs(self):
        homepage = self.site["index.html"].decode()
        self.assertEqual(len(re.findall(r'application/ld\+json', homepage)), 1)
        home_data = json.loads(re.search(
            r'<script type="application/ld\+json">(.*?)</script>', homepage, re.S
        ).group(1))
        self.assertEqual(home_data["@type"], "SoftwareSourceCode")
        self.assertEqual(home_data["license"], "https://opensource.org/licenses/MIT")
        doc = self.site["docs/catalog.html"].decode()
        data = json.loads(re.search(
            r'<script type="application/ld\+json">(.*?)</script>', doc, re.S
        ).group(1))
        self.assertEqual(data["@type"], "BreadcrumbList")
        self.assertEqual(data["itemListElement"][-1]["item"], SITE_URL + "/docs/catalog")

    def test_human_navigation_points_to_html_and_robots_excludes_markdown(self):
        self.assertIn('href="components.html"', self.site["docs/catalog.html"].decode())
        self.assertIn('href="blocks-guide.html"', self.site["docs/blocks.html"].decode())
        headers = self.site["_headers"].decode()
        self.assertIn("/llms-full.txt\n  X-Robots-Tag: noindex", headers)
        self.assertIn("/docs/*.md\n  X-Robots-Tag: noindex", headers)

    def test_json_ld_escapes_script_terminators(self):
        html = ('<!doctype html><html><head>'
                '<title>Guide &lt;/script&gt;&lt;script&gt;alert(1)&lt;/script&gt;</title>'
                '<meta name="description" content="Sample guide for safe structured data.">'
                '</head><body><main><h1>Test guide</h1></main></body></html>')
        files = {"docs/injected.html": html.encode("utf-8")}
        add_seo_metadata(files)
        result = files["docs/injected.html"].decode("utf-8")
        self.assertEqual(result.count("</script>"), 1, result)
        self.assertIn(r"\u003c/script>", result)
        self.assertNotIn("</script><script>", result)

    def test_search_description_overrides_are_complete_sentences(self):
        stems = (
            "component-authoring", "design-research-linear-resend", "recipes",
            "saas-cli-business", "tailwind-research", "visual-composition",
            "visual-intensity", "viz",
        )
        for stem in stems:
            content = self.site[f"docs/{stem}.html"].decode()
            description = meta(content, "description")
            self.assertGreaterEqual(len(description), 75, stem)
            self.assertLessEqual(len(description), 165, stem)
            self.assertTrue(description.endswith("."), (stem, description))
            self.assertFalse(description.endswith(" and."), (stem, description))
            self.assertFalse(description.endswith(" their."), (stem, description))
            self.assertFalse(description.endswith(" an."), (stem, description))
            self.assertFalse(description.endswith(" a."), (stem, description))
            self.assertNotIn(" .", description, stem)

    def test_generated_guide_metadata_is_descriptive(self):
        for name in ("ai-quickstart", "components", "framework-integrations", "from-pico"):
            page = self.site[f"docs/{name}.html"].decode()
            description = meta(page, "description")
            self.assertGreaterEqual(len(description), 70, name)
            self.assertNotIn("complete illustrated HTML reference", description)
            self.assertLessEqual(len(description), 175)


    def test_homepage_explains_css_framework_and_links_to_offers(self):
        home = self.site["index.html"].decode()
        self.assertIn("Lightweight CSS Framework for Semantic HTML", home)
        self.assertIn("Lightweight CSS. <em>Less machinery.</em>", home)
        self.assertIn('href="docs/catalog.html"', home)
        self.assertIn('href="docs/pro.html"', home)
        self.assertIn('href="docs/studio.html"', home)
        self.assertIn('href="tools/"', home)

    def test_indexable_examples_have_search_descriptions(self):
        for stem in ("data-grid", "native-choice-filter-list", "native-workflows", "platform-embed"):
            page = self.site[f"examples/{stem}.html"].decode()
            description = meta(page, "description")
            self.assertGreaterEqual(len(description), 95, stem)
            self.assertLessEqual(len(description), 165, stem)

    def test_commercial_concept_pages_are_discoverable_and_truthful(self):
        sitemap = ElementTree.fromstring(self.site["sitemap.xml"])
        urls = {node.text for node in sitemap.findall("{*}url/{*}loc")}
        products = self.site["docs/products.html"].decode()
        for name in ("pro", "studio"):
            self.assertIn(SITE_URL + f"/docs/{name}", urls)
            page = self.site[f"docs/{name}.html"].decode()
            self.assertEqual(canonical(page), [SITE_URL + f"/docs/{name}"])
            self.assertIn("NOT FOR SALE", page)
            self.assertIn("mailto:", page)
            self.assertIn('href="distribution.html"', page)
            self.assertIn(f'href="{name}.html"', products)
            self.assertNotIn('name="robots" content="noindex', page)
        self.assertIn('href="../examples/data-grid.html"', self.site["docs/catalog.html"].decode())
        self.assertIn('href="pro.html"', self.site["docs/blocks.html"].decode())
        self.assertIn('href="../docs/studio.html"', self.site["tools/index.html"].decode())


if __name__ == "__main__":
    unittest.main()
