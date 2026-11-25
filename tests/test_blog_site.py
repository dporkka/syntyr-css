"""Static Syntyr blog publish, semantics, and SEO contract."""
from __future__ import annotations

from html.parser import HTMLParser
import json
import re
import unittest
from xml.etree import ElementTree

from scripts.build_cloudflare_site import SITE_URL, source_files


POSTS = (
    "css-first-design-systems",
    "accessible-native-html",
    "landing-page-ui-blocks",
)


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.headings = []
        self.landmarks = []
        self.links = []
        self.times = []
        self.classes = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.classes.update(attrs.get("class", "").split())
        if tag in ("main", "article", "nav"):
            self.landmarks.append(tag)
        if tag == "h1":
            self.headings.append(tag)
        if tag == "a":
            self.links.append(attrs.get("href", ""))
        if tag == "time":
            self.times.append(attrs.get("datetime"))


class BlogSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = source_files()

    def test_index_and_three_articles_are_allowlisted(self):
        self.assertIn("blog/index.html", self.site)
        self.assertIn("blog/blog.css", self.site)
        for slug in POSTS:
            self.assertIn(f"blog/{slug}.html", self.site)

    def test_every_page_is_semantic_and_uses_real_syntyr_blocks(self):
        for name in ("index", *POSTS):
            html = self.site[f"blog/{name}.html"].decode()
            doc = Document()
            doc.feed(html)
            self.assertEqual(len(doc.headings), 1, name)
            self.assertIn("main", doc.landmarks, name)
            self.assertIn("syn-root", doc.classes, name)
            self.assertIn("syn-button", doc.classes, name)
            self.assertIn("syn-breadcrumbs", doc.classes, name)
            self.assertEqual(html.count('rel="stylesheet" href="/_assets/css/'), 3, name)
            self.assertNotIn("<script src=", html, name)
            self.assertIn("../docs/blocks.html", doc.links, name)
            self.assertIn('href="rss.xml"', html, name)
        index = self.site["blog/index.html"].decode()
        self.assertIn("syn-feature-grid", index)
        self.assertIn("syn-feature-card", index)
        for slug in POSTS:
            self.assertIn(f"{slug}.html", index)
        for slug in POSTS:
            article = self.site[f"blog/{slug}.html"].decode()
            self.assertIn("syn-prose", article)
            self.assertIn("syn-cta-band", article)
            self.assertIn('datetime="2026-11-16"', article)

    def test_structured_data_canonicals_and_rss(self):
        for slug in POSTS:
            html = self.site[f"blog/{slug}.html"].decode()
            match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
            self.assertIsNotNone(match, slug)
            data = json.loads(match.group(1))
            self.assertEqual(data["@type"], "BlogPosting", slug)
            self.assertEqual(data["mainEntityOfPage"], SITE_URL + f"/blog/{slug}")
            self.assertEqual(data["datePublished"], "2026-11-16")
            self.assertIn(f'href="{SITE_URL}/blog/{slug}"', html)
        self.assertIn(f'href="{SITE_URL}/blog/"', self.site["blog/index.html"].decode())
        rss = ElementTree.fromstring(self.site["blog/rss.xml"])
        self.assertEqual(rss.findtext("channel/link"), SITE_URL + "/blog/")
        self.assertEqual(len(rss.findall("channel/item")), len(POSTS))
        for item in rss.findall("channel/item"):
            self.assertTrue(item.findtext("guid", "").startswith(SITE_URL + "/blog/"))
            self.assertTrue(item.findtext("description"))

    def test_blog_in_sitemap_and_primary_navigation(self):
        sitemap = ElementTree.fromstring(self.site["sitemap.xml"])
        urls = {tag.text for tag in sitemap.findall("{*}url/{*}loc")}
        self.assertIn(SITE_URL + "/blog/", urls)
        for slug in POSTS:
            self.assertIn(SITE_URL + f"/blog/{slug}", urls)
        self.assertIn('href="blog/"', self.site["index.html"].decode())
        self.assertIn('href="../blog/"', self.site["docs/index.html"].decode())


if __name__ == "__main__":
    unittest.main()
