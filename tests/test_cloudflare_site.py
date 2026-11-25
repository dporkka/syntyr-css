"""Cloudflare publish contract: allowlist, intact paths, and immutable releases."""
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import unquote, urlsplit
import json
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if tag in {"a", "link", "script", "img"}:
            self.urls.append(fields.get("href") or fields.get("src") or "")


class CloudflareSiteTests(unittest.TestCase):
    def build(self, output):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_cloudflare_site.py"),
             "--output", str(output)], cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_public_allowlist_and_relative_links(self):
        with TemporaryDirectory() as temp:
            out = Path(temp) / "public"
            self.build(out)
            self.assertTrue((out / "index.html").is_file())
            self.assertTrue((out / "404.html").is_file())
            self.assertTrue((out / "docs/index.html").is_file())
            self.assertTrue((out / "docs/framework-integrations.md").is_file())
            self.assertTrue((out / "docs/mobile-frameworks.md").is_file())
            self.assertTrue((out / "metadata/mobile/syntyr.tokens.json").is_file())
            self.assertTrue((out / "integrations/react-native/styles.ts").is_file())
            self.assertTrue((out / "examples/react-native/App.tsx").is_file())
            self.assertTrue((out / "docs/performance-validation.md").is_file())
            self.assertTrue((out / "docs/performance-and-polish.md").is_file())
            self.assertTrue((out / "dist/syntyr.core.css").is_file())
            self.assertTrue((out / "examples/operations-console.html").is_file())
            self.assertTrue((out / "examples/themes.html").is_file())
            self.assertTrue((out / "docs/native-browser-apis.md").is_file())
            self.assertTrue((out / "examples/native-apis.html").is_file())
            self.assertTrue((out / "examples/dropdowns.html").is_file())
            self.assertTrue((out / "docs/dropdowns.md").is_file())
            self.assertTrue((out / "docs/dropdowns.html").is_file())
            self.assertTrue((out / "dist/syntyr.utilities.css").is_file())
            contract = json.loads((out / "metadata/syntyr-contract.json").read_text())
            self.assertEqual(contract["schema_version"], 1)
            self.assertTrue(any(c["name"] == "syn-button" for c in contract["classes"]))
            self.assertTrue((out / "terminal/palettes.json").is_file())
            self.assertFalse((out / "business").exists())
            self.assertFalse((out / "tests").exists())
            self.assertFalse((out / "scripts").exists())
            self.assertFalse((out / ".git").exists())
            self.assertFalse((out / "experiments").exists())
            self.assertFalse((out / "docs/brand-migration.md").exists())
            self.assertFalse([p for p in out.rglob("*")
                              if p.name.startswith("cy" + "berline")])
            self.assertFalse(list(out.rglob("*.env")))
            for page in out.rglob("*.html"):
                parser = Links()
                parser.feed(page.read_text(encoding="utf-8"))
                for url in parser.urls:
                    parsed = urlsplit(url)
                    if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith("/"):
                        continue
                    target = (page.parent / unquote(parsed.path)).resolve()
                    self.assertTrue(target.is_relative_to(out.resolve()), (page, url))
                    resolved = target / 'index.html' if target.is_dir() else target
                    self.assertTrue(resolved.is_file(), (page, url))
            self.assertTrue((out / "docs/theme-editor.js").is_file())
            for name in ("page-builder.html", "page-builder.css", "page-builder.js", "page-builder-model.mjs", "site-builder-model.mjs", "page-builder-site-kits.mjs", "page-builder-guide.md", "page-builder-guide.html"):
                self.assertTrue((out / "docs" / name).is_file(), name)
            for name in ("form-builder.html", "form-builder.css", "form-builder.js", "form-builder-model.mjs"):
                self.assertTrue((out / "docs" / name).is_file(), name)
            for name in ("saas", "crm", "native"):
                self.assertTrue((out / "docs/demos" / (name + ".zip")).is_file())
            playground = (out / "docs/composition-playground.html").read_text()
            self.assertIn('href="demos/crm.zip"', playground)
            self.assertIn('Syntyr%20Pro%20composition%20preview', playground)
            # JSON-LD is inert data, not browser-executed JavaScript.
            self.assertFalse(any(
                "<script" in re.sub(
                    r'<script type="application/ld\+json">.*?</script>', "",
                    page.read_text(encoding="utf-8"), flags=re.I | re.S
                ).lower()
                for page in out.rglob("*.html")
                if page.relative_to(out).as_posix() not in {
                    "docs/form-builder.html", "docs/theme-editor.html", "docs/catalog.html",
                    "tools/color-contrast-checker.html", "tools/css-theme-generator.html",
                    "tools/css-clamp-generator.html", "tools/responsive-design-tester.html",
                    "tools/ascii-playground.html",  # Local-only first-party ASCII tool.
                    "docs/playground.html", "docs/page-builder.html", "docs/blocks.html",
                    "docs/composition-playground.html",  # Local-only first-party authoring.
                    "docs/htmx-playground.html",  # Explicit first-party HTMX demo with vendored JS.
                    "docs/how-to.html",  # Docs-only search, same CSP as the catalog.
                    "docs/starter-wizard.html",  # Docs-only generator, no runtime dependency.
                    "examples/animation.html", "examples/copy.html",
                    "examples/resizable-workspace.html",
                    "examples/command-launcher.html",
                    # Explicitly opted-in first-party ESM examples only.
                }
            ))

    def test_cache_contract_and_version_snapshot(self):
        with TemporaryDirectory() as temp:
            out = Path(temp) / "public"
            self.build(out)
            headers = (out / "_headers").read_text(encoding="utf-8")
            self.assertIn("immutable", headers)
            self.assertIn("must-revalidate", headers)
            version = (ROOT / "VERSION").read_text().strip()
            manifest = json.loads((ROOT / "site-releases/manifest.json").read_text())
            published = "0.3.0-alpha.4"
            self.assertIn(published, manifest, "published alpha.4 immutable snapshot must remain")
            if version != published:
                self.assertNotIn(version, manifest, "unreleased candidates must not appear as immutable releases")
            for filename in manifest[published]:
                self.assertEqual(
                    (out / "v" / published / filename).read_bytes(),
                    (ROOT / "site-releases" / published / filename).read_bytes(),
                )

    def test_reproducible_no_stale_extras_and_check_mode(self):
        with TemporaryDirectory() as temp:
            out = Path(temp) / "public"
            self.build(out)
            (out / "unexpected-secret.txt").write_text("must not ship")
            self.build(out)
            self.assertFalse((out / "unexpected-secret.txt").exists())
            result = subprocess.run(
                [sys.executable, "scripts/build_cloudflare_site.py", "--output",
                 str(out), "--check"], cwd=ROOT, capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            (out / "index.html").write_text("stale")
            result = subprocess.run(
                [sys.executable, "scripts/build_cloudflare_site.py", "--output",
                 str(out), "--check"], cwd=ROOT, capture_output=True, text=True
            )
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
