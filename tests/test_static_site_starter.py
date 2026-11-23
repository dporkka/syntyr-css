"""Executable contract for the portable, CSS-first SaaS marketing site starter."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
STARTER = ROOT / "examples/site-starters/saas-marketing"
ROUTES = ("index.html", "pricing/index.html", "about/index.html")
EXPORTER = ROOT / "scripts/export_site_starter.py"


class SiteDocument(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.scripts = 0

    def handle_starttag(self, tag: str, attrs):
        attributes = dict(attrs)
        self.tags.append((tag, attributes))
        if attributes.get("id"):
            self.ids.add(attributes["id"])
        if tag == "script":
            self.scripts += 1
        if tag in {"a", "link", "img", "script"}:
            link = attributes.get("href") or attributes.get("src")
            if link:
                self.links.append(link)


def inspect_site(source: Path) -> None:
    for route in ROUTES:
        page = source / route
        assert page.is_file(), f"missing route {route}"
        html = page.read_text(encoding="utf-8")
        dom = SiteDocument()
        dom.feed(html)
        tags = [tag for tag, _ in dom.tags]
        assert tags.count("h1") == 1, f"{route}: expected one h1"
        assert tags.count("main") == 1, f"{route}: expected one main landmark"
        assert tags.count("header") >= 1 and tags.count("footer") >= 1
        assert tags.count("nav") >= 1, f"{route}: expected primary navigation"
        assert "Skip to content" in html, f"{route}: missing skip link"
        assert dom.scripts == 0, f"{route}: template must be script-free"
        assert "data-syn-theme=" in html, f"{route}: missing Syntyr theme"
        assert any("syntyr.core.css" in link for link in dom.links)
        assert any("site.css" in link for link in dom.links)
        assert "Fictional product" in html, f"{route}: demo content disclosure"
        for link in dom.links:
            parsed = urlsplit(link)
            assert not parsed.scheme and not parsed.netloc, f"{route}: remote asset {link}"
            if not parsed.path or parsed.path.startswith("#"):
                continue
            if parsed.path.startswith(("mailto:", "tel:")):
                continue
            destination = (page.parent / parsed.path).resolve()
            assert destination.is_relative_to(ROOT.resolve()) or destination.is_relative_to(source.resolve())
            assert destination.is_file(), f"{route}: missing target {link}"
            if parsed.fragment:
                linked = SiteDocument()
                linked.feed(destination.read_text(encoding="utf-8"))
                assert parsed.fragment in linked.ids, f"{route}: broken fragment {link}"


class StaticSiteStarterTests(unittest.TestCase):
    def test_source_is_a_connected_accessible_three_page_site(self):
        inspect_site(STARTER)
        home = (STARTER / "index.html").read_text(encoding="utf-8")
        self.assertIn("id=\"features\"", home)
        self.assertIn("id=\"workflow\"", home)
        self.assertIn("id=\"faq\"", home)
        self.assertIn("<details", home)
        self.assertIn("pricing/index.html", home)
        self.assertIn("about/index.html", home)

    def test_export_is_standalone_and_script_free(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "site"
            result = subprocess.run(
                [sys.executable, str(EXPORTER), "--output", str(output)],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "assets/syntyr.core.css").is_file())
            self.assertTrue((output / "assets/site.css").is_file())
            inspect_site(output)
            for route in ROUTES:
                self.assertNotIn("/dist/", (output / route).read_text(encoding="utf-8"))

    def test_export_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "existing"
            output.mkdir()
            (output / "keep.txt").write_text("do not overwrite", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(EXPORTER), "--output", str(output)],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((output / "keep.txt").read_text(), "do not overwrite")

    def test_cloudflare_preview_is_explicitly_allowlisted_and_noindexed(self):
        from scripts.build_cloudflare_site import source_files
        files = source_files()
        for route in ROUTES:
            name = f"examples/site-starters/saas-marketing/{route}"
            self.assertIn(name, files)
            self.assertIn('name="robots" content="noindex,follow"', files[name].decode())
        self.assertIn("examples/site-starters/saas-marketing/assets/site.css", files)


if __name__ == "__main__":
    unittest.main()
