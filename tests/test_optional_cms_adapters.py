"""Portable Syntyr data must survive optional CMS adapters without code execution."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from scripts import export_cms_adapter
from scripts.render_cms_starter import render_document

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "examples/cms-starter/content/pages/home.json"
KEYSTATIC = ROOT / "examples/cms-keystatic/content/pages/home.json"
PAYLOAD = ROOT / "examples/cms-payload/fixtures/home-document.json"


class OptionalCmsAdaptersTests(unittest.TestCase):
    def canonical(self) -> dict:
        return json.loads(SOURCE.read_text(encoding="utf-8"))

    def fixture(self, filename: Path) -> dict:
        return json.loads(filename.read_text(encoding="utf-8"))

    def test_keystatic_roundtrip_is_lossless(self):
        converted = export_cms_adapter.convert("keystatic", self.fixture(KEYSTATIC))
        self.assertEqual(converted, self.canonical())

    def test_payload_roundtrip_strips_only_known_database_metadata(self):
        converted = export_cms_adapter.convert("payload", self.fixture(PAYLOAD))
        self.assertEqual(converted, self.canonical())

    def test_unsafe_urls_duplicate_anchors_and_unknown_types_fail_closed(self):
        for provider, path in (("keystatic", KEYSTATIC), ("payload", PAYLOAD)):
            source = self.fixture(path)
            for mutation in ("script", "duplicate", "unsupported", "unexpected"):
                data = deepcopy(source)
                blocks = data["sections"]
                props = blocks[0]["value"] if provider == "keystatic" else blocks[0]
                if mutation == "script":
                    props["button"]["url"] = "javascript:alert(1)"
                elif mutation == "duplicate":
                    if provider == "keystatic":
                        blocks[1]["value"]["id"] = props["id"]
                    else:
                        blocks[1]["sectionId"] = props["sectionId"]
                elif mutation == "unsupported":
                    blocks[0]["discriminant" if provider == "keystatic" else "blockType"] = "rawHtml"
                else:
                    props["unsafeHtml"] = "<script>alert(1)</script>"
                with self.subTest(provider=provider, mutation=mutation):
                    with self.assertRaises(ValueError):
                        export_cms_adapter.convert(provider, data)

    def test_untrusted_text_is_escaped_by_portable_html_renderer(self):
        source = self.fixture(KEYSTATIC)
        source["sections"][0]["value"]["heading"] = '<img src=x onerror="alert(1)">'
        page = export_cms_adapter.convert("keystatic", source)
        html = render_document(page)
        self.assertIn("&lt;img", html)
        self.assertNotIn("<img src=x", html)

    def test_cli_never_overwrites_output_when_input_invalid(self):
        with TemporaryDirectory() as td:
            out = Path(td) / "site.json"
            out.write_text('{"known":"good"}', encoding="utf-8")
            bad = Path(td) / "bad.json"
            data = self.fixture(PAYLOAD)
            data["sections"][0]["button"]["url"] = "//untrusted.example"
            bad.write_text(json.dumps(data), encoding="utf-8")
            call = subprocess.run(
                [sys.executable, str(ROOT / "scripts/export_cms_adapter.py"),
                 "payload", "--input", str(bad), "--output", str(out)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(call.returncode, 0)
            self.assertEqual(out.read_text(), '{"known":"good"}')

    def test_cli_writes_static_renderer_compatible_json(self):
        with TemporaryDirectory() as td:
            out = Path(td) / "site.json"
            call = subprocess.run(
                [sys.executable, str(ROOT / "scripts/export_cms_adapter.py"),
                 "payload", "--input", str(PAYLOAD), "--output", str(out)],
                capture_output=True, text=True,
            )
            self.assertEqual(call.returncode, 0, call.stderr)
            self.assertEqual(json.loads(out.read_text()), self.canonical())

    def test_keystatic_config_uses_separate_editor_storage_and_no_cms_runtime(self):
        config = (ROOT / "examples/cms-keystatic/keystatic.config.ts").read_text()
        self.assertIn("fields.blocks(", config)
        self.assertIn("format: { data: 'json' }", config)
        self.assertIn("path: 'content/pages/home'", config)
        self.assertIn("kind: 'local'", config)
        self.assertNotIn("rawHtml", config)
        self.assertEqual(
            {part for part in ("hero", "features", "pricing", "faq", "cta")
             if f"{part}: {{" in config},
            {"hero", "features", "pricing", "faq", "cta"},
        )

    def test_payload_config_has_block_types_and_requires_explicit_access(self):
        config = (ROOT / "examples/cms-payload/SyntyrHomepage.ts").read_text()
        for kind in ("hero", "features", "pricing", "faq", "cta"):
            self.assertIn(f"slug: '{kind}'", config)
        self.assertIn("createSyntyrHomepageGlobal", config)
        self.assertIn("access:", config)
        self.assertIn("type: 'blocks'", config)
        self.assertIn("name: 'sectionId'", config)
        self.assertNotIn("access: { read: () => true", config)


if __name__ == "__main__":
    unittest.main()
