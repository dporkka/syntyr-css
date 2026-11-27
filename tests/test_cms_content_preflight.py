"""Reject ambiguous JSON at every Python CMS/editor input boundary."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import render_cms_starter as cms
from scripts.build_hugo_cms_starter import stage_site
from scripts.export_cms_adapter import export

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "examples/cms-starter/content/pages/home.json"


class StrictContentPreflightTests(unittest.TestCase):
    def test_schema_requires_nonblank_free_text(self):
        schema = json.loads((SOURCE.parents[2] / "blocks.schema.json").read_text())
        pending = [schema]
        count = 0
        while pending:
            item = pending.pop()
            if isinstance(item, dict):
                if item.get("type") == "string" and "minLength" in item:
                    self.assertIn("pattern", item)
                    self.assertNotRegex("   ", item["pattern"])
                    count += 1
                pending.extend(item.values())
            elif isinstance(item, list):
                pending.extend(item)
        self.assertGreater(count, 10)

    def test_valid_utf8_and_escaped_emoji_are_portable(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "home.json"
            page = json.loads(SOURCE.read_text())
            page["title"] = "Olá 🌐"
            path.write_text(json.dumps(page), encoding="utf-8")
            self.assertEqual(cms.load_validated_document(path), page)
            self.assertIn("Olá 🌐", cms.render_document(page))

    def test_ambiguous_or_invalid_json_rejected(self):
        cases = (
            (b'{"title":"first","title":"last"}', "Duplicate"),
            (b'{"nested":{"id":"first","id":"last"}}', "Duplicate"),
            (b'{"x":NaN}', "Non-JSON"),
            (b'{"x":Infinity}', "Non-JSON"),
            (b'{"x":1e999}', "finite"),
            (b'{"x":"\\ud800"}', "Unicode"),
            (b'{"x":"\\udfff"}', "Unicode"),
            (b'{"x":"\xff"}', "Unicode"),
            (b'[' * 2000 + b']' * 2000, "nesting"),
        )
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "home.json"
            for payload, diagnostic in cases:
                with self.subTest(payload=payload[:80]):
                    path.write_bytes(payload)
                    with self.assertRaisesRegex(ValueError, diagnostic):
                        cms.load_content_json(path)
            with patch("scripts.render_cms_starter.MAX_CONTENT_BYTES", 12):
                path.write_bytes(b" " * 13)
                with self.assertRaisesRegex(ValueError, "input limit"):
                    cms.load_content_json(path)

    def test_invalid_content_never_reaches_render_or_adapters(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "content/pages/home.json"
            source.parent.mkdir(parents=True)
            source.write_bytes(b'{"title":"first","title":"last"}')
            for function in (
                lambda: cms.build(root, root / "python"),
                lambda: stage_site(root / "hugo", content_path=source),
                lambda: export("keystatic", source, root / "keystatic.json"),
                lambda: export("payload", source, root / "payload.json"),
            ):
                with self.assertRaisesRegex(ValueError, "Duplicate"):
                    function()
            self.assertEqual(set(root.iterdir()), {root / "content"})

    def test_read_only_cli_succeeds_or_fails_without_build(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "content/pages/home.json"
            source.parent.mkdir(parents=True)
            output = root / "never-build"
            command = [sys.executable, str(ROOT / "scripts/render_cms_starter.py"),
                       "--source", str(root), "--output", str(output), "--validate-only"]
            source.write_bytes(SOURCE.read_bytes())
            good = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(good.returncode, 0, good.stderr)
            source.write_bytes(b'{"title":"a","title":"b"}')
            bad = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)
            self.assertIn("Duplicate", bad.stderr)
            self.assertFalse(output.exists())

    def test_rejects_dot_segments_before_rendering_deployment_local_links(self):
        for bad in ("/../signup", "/./signup", "/a/../signup", "/%2e/signup",
                    "/%2E%2e/signup", "/.%2e/signup", "/%2e./signup"):
            with self.subTest(url=bad):
                page = json.loads(SOURCE.read_text())
                page["sections"][0]["button"]["url"] = bad
                with self.assertRaisesRegex(ValueError, "traversal"):
                    cms.validate_document(page)
        for good in ("/signup", "/signup?next=../account", "/a%2Fb", "/.well-known",
                     "https://example.org/signup"):
            with self.subTest(url=good):
                page = json.loads(SOURCE.read_text())
                page["sections"][0]["button"]["url"] = good
                self.assertEqual(cms.validate_document(page), page)

    def test_url_and_text_validation_fails_on_malformed_unicode_and_authority(self):
        for bad in ("https://:443/path", "https://example.org:99999/", "https://@example.org/",
                    "https://example.org:bad/", "/\ud800"):
            with self.subTest(url=repr(bad)):
                page = json.loads(SOURCE.read_text())
                page["sections"][0]["button"]["url"] = bad
                with self.assertRaises(ValueError):
                    cms.validate_document(page)
        page = json.loads(SOURCE.read_text())
        page["title"] = "\ud800"
        with self.assertRaises(ValueError):
            cms.validate_document(page)


if __name__ == "__main__":
    unittest.main()
