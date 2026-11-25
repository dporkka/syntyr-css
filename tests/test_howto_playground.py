"""The How-To directory reuses canonical block markup through the playground."""
from html import unescape
from pathlib import Path
import json
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def catalog_entries():
    source = (ROOT / "docs/playground-catalog.js").read_text(encoding="utf-8")
    return json.loads(source.removeprefix("window.SYNTYR_PLAYGROUND_CATALOG = ").removesuffix(";\n"))


class HowToPlaygroundTests(unittest.TestCase):
    def test_all_free_blocks_are_synchronized_from_canonical_gallery(self):
        run = subprocess.run([sys.executable, "scripts/build_playground_catalog.py", "--check"],
                             cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        blocks = (ROOT / "docs/blocks.html").read_text(encoding="utf-8")
        ids = re.findall(r'data-block-id="([a-z0-9-]+)"', blocks)
        snippets = re.findall(r'<pre class="blocks-source"><code>(.*?)</code></pre>', blocks, re.S)
        entries = catalog_entries()
        manifest_categories = {
            entry["category"] for entry in json.loads(
                (ROOT / "blocks/manifest.json").read_text(encoding="utf-8")
            )["blocks"]
        }
        by_id = {item["id"]: item for item in entries}
        self.assertEqual(len(ids), len(snippets))
        self.assertGreaterEqual(len(ids), 20)
        self.assertEqual(len(by_id), len(entries))
        self.assertGreaterEqual(len(entries), 36)
        for key, snippet in zip(ids, snippets):
            item = by_id["block-" + key]
            self.assertEqual(item["html"], unescape(snippet).strip())
            self.assertEqual(item["kind"], "block")
            self.assertIn(item["category"], manifest_categories)
            self.assertIn("syntyr.core.css", item["module"])
            self.assertTrue(item["description"])
            self.assertTrue(item["title"])

    def test_inspector_sources_match_canonical_snippet_classes(self):
        from scripts.build_playground_catalog import LiteralClassParser
        from scripts.export_api_metadata import collect
        sources = {item["name"]: "src/" + item["module"] for item in collect()["classes"]}
        for entry in catalog_entries():
            parser = LiteralClassParser()
            parser.feed(entry["html"])
            expected = sorted({sources[name] for name in parser.classes if name.startswith("syn-")})
            self.assertEqual(entry["source_files"], expected, entry["id"])
            for source in expected:
                self.assertTrue((ROOT / source).is_file(), source)

    def test_gallery_links_to_editor_and_editor_groups_examples(self):
        block_script = (ROOT / "docs/blocks.js").read_text()
        editor = (ROOT / "docs/playground.js").read_text()
        html = (ROOT / "docs/playground.html").read_text()
        self.assertIn('playground.html#component=', block_script)
        self.assertIn("document.createElement", block_script)
        self.assertIn('"Site & application blocks"', editor)
        self.assertIn("item.kind", editor)
        self.assertIn('id="playground-source-link"', html)

    def test_howto_directory_is_static_searchable_and_links_to_real_examples(self):
        page = (ROOT / "docs/how-to.html").read_text()
        script = (ROOT / "docs/how-to.js").read_text()
        cards = re.findall(r'<article class="syn-panel howto-card"\s+data-howto-keywords="([^"]+)"', page)
        self.assertGreaterEqual(len(cards), 8)
        self.assertIn('id="howto-search"', page)
        self.assertIn('id="howto-results"', page)
        self.assertIn('id="howto-empty"', page)
        self.assertIn("card.hidden =", script)
        self.assertIn("addEventListener", script)
        self.assertNotIn("innerHTML", script)
        ids = {entry["id"] for entry in catalog_entries()}
        links = re.findall(r'href="playground.html#component=([a-z0-9-]+)"', page)
        self.assertGreaterEqual(len(links), len(cards))
        for link in links:
            self.assertIn(link, ids, link)
        self.assertIn('href="how-to.html"', (ROOT / "docs/guides.html").read_text())
        self.assertIn('href="how-to.html"', (ROOT / "docs/index.html").read_text())

    def test_publish_fails_closed_on_stale_generated_block_gallery(self):
        from unittest.mock import patch
        from scripts.build_cloudflare_site import source_files
        with patch("scripts.build_cloudflare_site.blocks_gallery", return_value="stale HTML"):
            with self.assertRaisesRegex(ValueError, "Stale blocks gallery"):
                source_files()

    def test_publisher_allowlists_howto_assets(self):
        publisher = (ROOT / "scripts/build_cloudflare_site.py").read_text()
        for entry in ("how-to.html", "how-to.js", "how-to.css"):
            self.assertIn('"' + entry + '"', publisher)
        llms = (ROOT / "llms.txt").read_text()
        self.assertIn("docs/how-to.html", llms)


if __name__ == "__main__":
    unittest.main()
