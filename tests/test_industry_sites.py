"""Contract tests for dependency-free, distributable industry site starters."""
from html.parser import HTMLParser
from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory
from urllib.parse import unquote, urlsplit
import unittest
from unittest.mock import patch
import zipfile

from scripts.package_industry_sites import SITE_NAMES, package_sites

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "examples" / "industry-sites"


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.links = []
        self.ids = set()
        self.title = False
        self.description = False
        self.skip = False
        self.heading_count = 0
        self.forms = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag in {"a", "link"} and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "meta" and attrs.get("name") == "description" and attrs.get("content"):
            self.description = True
        if tag == "title":
            self.title = True
        if tag == "a" and attrs.get("href") == "#main":
            self.skip = True
        if tag == "h1":
            self.heading_count += 1
        if tag == "form":
            self.forms.append(attrs)


class IndustrySitesTests(unittest.TestCase):
    def test_three_multpage_sites_have_navigation_and_semantics(self):
        self.assertEqual(set(SITE_NAMES), {"field-service", "professional-practice", "saas-developer"})
        for name in SITE_NAMES:
            pages = sorted((BASE / name).glob("*.html"))
            self.assertGreaterEqual(len(pages), 2, name)
            for path in pages:
                with self.subTest(path=path):
                    html = path.read_text(encoding="utf-8")
                    page = Page()
                    page.feed(html)
                    tags = [tag for tag, _ in page.tags]
                    self.assertTrue(page.title and page.description)
                    self.assertTrue(page.skip)
                    self.assertIn("main", page.ids)
                    self.assertEqual(page.heading_count, 1)
                    self.assertIn("header", tags)
                    self.assertIn("main", tags)
                    self.assertIn("footer", tags)
                    self.assertNotIn("script", tags)
                    self.assertFalse(page.forms, "No unconnected lead capture forms")
                    self.assertTrue(any(tag == "body" and "syn-root" in attrs.get("class", "")
                                        and attrs.get("data-syn-theme") for tag, attrs in page.tags))
                    self.assertIn("../../../dist/syntyr.core.css", page.links)
                    self.assertIn("../site.css", page.links)
                    self.assertIn("Fictional", html)

    def test_every_relative_page_and_fragment_link_resolves(self):
        for name in SITE_NAMES:
            for path in (BASE / name).glob("*.html"):
                page = Page()
                page.feed(path.read_text(encoding="utf-8"))
                for href in page.links:
                    parsed = urlsplit(href)
                    if parsed.scheme or href.startswith("//"):
                        self.assertNotIn(parsed.scheme, {"http", "https"}, path.name)
                        continue
                    if not parsed.path and not parsed.fragment:
                        self.fail(f"Empty link: {path}")
                    if parsed.path.startswith("/"):
                        self.fail(f"Unportable root link: {path}: {href}")
                    target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
                    self.assertTrue(target.is_file(), f"{path}: {href}")
                    if parsed.fragment and target.suffix == ".html":
                        destination = Page()
                        destination.feed(target.read_text(encoding="utf-8"))
                        self.assertIn(unquote(parsed.fragment), destination.ids, f"{path}: {href}")

    def test_packager_produces_self_contained_html_and_css(self):
        with TemporaryDirectory() as tmp:
            outputs = package_sites(Path(tmp))
            self.assertEqual(set(outputs), set(SITE_NAMES))
            for site, path in outputs.items():
                with self.subTest(site=site):
                    with zipfile.ZipFile(path) as archive:
                        files = set(archive.namelist())
                        self.assertIn("assets/syntyr.core.css", files)
                        self.assertIn("assets/site.css", files)
                        self.assertIn("README.md", files)
                        self.assertIn("LICENSE", files)
                        self.assertIn("index.html", files)
                        self.assertGreaterEqual(len([x for x in files if x.endswith(".html")]), 2)
                        for filename in files:
                            if filename.endswith(".html"):
                                html = archive.read(filename).decode("utf-8")
                                self.assertIn('href="assets/syntyr.core.css"', html)
                                self.assertIn('href="assets/site.css"', html)
                                self.assertNotIn("../../dist/", html)
                                self.assertNotIn("../site.css", html)

    def test_export_does_not_include_unreviewed_html_pages(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            copytree(BASE, source)
            draft = source / "field-service" / "draft.html"
            draft.write_text((source / "field-service" / "index.html").read_text(encoding="utf-8"),
                             encoding="utf-8")
            with patch("scripts.package_industry_sites.SOURCE", source):
                outputs = package_sites(root / "output")
            with zipfile.ZipFile(outputs["field-service"]) as archive:
                self.assertNotIn("draft.html", archive.namelist())
                self.assertEqual(
                    {name for name in archive.namelist() if name.endswith(".html")},
                    {"index.html", "services.html"},
                )

    def test_export_rejects_symlinked_reviewed_page(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            copytree(BASE, source)
            target = source / "professional-practice" / "services.html"
            outside = root / "outside.html"
            outside.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
            target.unlink()
            target.symlink_to(outside)
            with patch("scripts.package_industry_sites.SOURCE", source):
                with self.assertRaisesRegex(ValueError, "Not a reviewed regular page"):
                    package_sites(root / "output")

    def test_code_examples_that_may_scroll_are_keyboard_focusable(self):
        for path in (BASE / "saas-developer").glob("*.html"):
            with self.subTest(path=path):
                page = Page()
                page.feed(path.read_text(encoding="utf-8"))
                for tag, attrs in page.tags:
                    if tag == "pre" and "site-code" in attrs.get("class", "").split():
                        self.assertEqual(attrs.get("tabindex"), "0", "Code needs Tab access")
                        self.assertTrue(attrs.get("aria-label"), "Code needs a descriptive label")

    def test_failed_export_preserves_existing_archives(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            copytree(BASE, source)
            output = root / "output"
            first_page = source / SITE_NAMES[0] / "index.html"
            last_page = source / SITE_NAMES[-1] / "index.html"
            with patch("scripts.package_industry_sites.SOURCE", source):
                paths = package_sites(output)
                before = {path: path.read_bytes() for path in paths.values()}

                # Make the first replacement detectably different, then make
                # the last starter fail after earlier ZIPs have been built.
                with first_page.open("a", encoding="utf-8") as page:
                    page.write("\n<!-- changed on rerun -->\n")
                last_page.write_text("<html></html>", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Unexpected stylesheet references"):
                    package_sites(output)

            self.assertEqual(set(output.iterdir()), set(before))
            self.assertEqual({path: path.read_bytes() for path in paths.values()}, before)

    def test_public_site_only_includes_reviewed_starters_and_noindexes_demos(self):
        from scripts.build_cloudflare_site import NOINDEX_HTML, source_files

        expected = {"examples/industry-sites/index.html", "examples/industry-sites/site.css"}
        for name in SITE_NAMES:
            for page in (BASE / name).glob("*.html"):
                expected.add(f"examples/industry-sites/{name}/{page.name}")
        files = source_files()
        self.assertTrue(expected.issubset(files.keys()))
        for name in expected:
            if name.endswith(".html"):
                self.assertIn(name, NOINDEX_HTML)
                self.assertIn(b'content="noindex,follow"', files[name])


if __name__ == "__main__":
    unittest.main()
