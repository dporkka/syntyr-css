"""Portable static-site deployment adapters: deterministic and fail-closed."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
import unittest
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from static_deploy import (  # noqa: E402
    DeploymentError,
    CloudflareDirectoryProvider,
    NulangCloudBundleProvider,
    StaticSite,
    validate_site_url,
)


class StaticDeployTests(unittest.TestCase):
    def sample(self, root: Path) -> Path:
        site = root / "site"
        (site / "css").mkdir(parents=True)
        (site / "index.html").write_bytes(b"<h1>Syntyr</h1>")
        (site / "css/site.css").write_bytes(b"body{}")
        return site

    def test_cloudflare_adapter_stages_exact_site_without_mutating_source(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            site = self.sample(root)
            (site / "_headers").write_text("/*\n  X-Content-Type-Options: nosniff\n")
            source = StaticSite.load(site)
            target = root / "published"
            receipt = CloudflareDirectoryProvider().prepare(source, target, "https://example.com")
            self.assertEqual(receipt["provider"], "cloudflare")
            self.assertEqual((target / "css/site.css").read_bytes(), b"body{}")
            self.assertEqual((target / "_headers").read_bytes(), (site / "_headers").read_bytes())
            self.assertFalse((target / "syntyr-deploy.json").exists())

    def test_nulang_bundle_is_deterministic_and_records_content_hashes(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            site = StaticSite.load(self.sample(root))
            a, b = root / "one.zip", root / "two.zip"
            provider = NulangCloudBundleProvider()
            receipt = provider.prepare(site, a, "https://demo.example")
            provider.prepare(site, b, "https://demo.example")
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(receipt["status"], "prepared_only")
            with ZipFile(a) as archive:
                manifest = json.loads(archive.read("syntyr-deploy.json"))
                self.assertEqual(manifest["schema"], "syntyr.static-site.bundle/v1")
                self.assertEqual(manifest["origin"], "https://demo.example")
                self.assertEqual(manifest["files"][0]["path"], "css/site.css")
                for entry in manifest["files"]:
                    archived = archive.read("site/" + entry["path"])
                    self.assertEqual(entry["bytes"], len(archived))
                    self.assertEqual(entry["sha256"], hashlib.sha256(archived).hexdigest())
                self.assertEqual(archive.read("site/index.html"), b"<h1>Syntyr</h1>")

    def test_nulang_refuses_cloudflare_specific_headers(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            site = self.sample(root)
            (site / "_headers").write_text("/*\n  X-Frame-Options: DENY\n")
            with self.assertRaisesRegex(DeploymentError, "Cloudflare"):
                NulangCloudBundleProvider().prepare(StaticSite.load(site), root / "site.zip", "https://example.com")

    def test_rejects_symlinks_and_secret_files_before_staging(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            site = self.sample(root)
            (site / ".env").write_text("SECRET=example")
            with self.assertRaisesRegex(DeploymentError, "disallowed"):
                StaticSite.load(site)
            (site / ".env").unlink()
            (site / "css/leak.css").symlink_to(site / "index.html")
            with self.assertRaisesRegex(DeploymentError, "symlink"):
                StaticSite.load(site)

    def test_repository_private_directories_are_rejected_before_reading(self):
        for directory, filename in (("business", "internal-notes.md"),
                                    ("tests", "fixture.json"),
                                    ("src", "settings.ts"),
                                    ("node_modules", "index.js")):
            with self.subTest(directory=directory), TemporaryDirectory() as temp:
                site = self.sample(Path(temp))
                private = site / directory / filename
                private.parent.mkdir(parents=True, exist_ok=True)
                private.write_text("PRIVATE", encoding="utf-8")
                with self.assertRaisesRegex(DeploymentError, "disallowed"):
                    StaticSite.load(site)

    def test_secret_yml_yaml_variants_never_enter_staging(self):
        for filename in ("secrets.yaml", "secrets.yml", "credentials.yaml",
                         "credentials.yml", "config/secrets.yaml"):
            with self.subTest(filename=filename), TemporaryDirectory() as temp:
                site = self.sample(Path(temp))
                private = site / filename
                private.parent.mkdir(parents=True, exist_ok=True)
                private.write_text("token: private", encoding="utf-8")
                with self.assertRaisesRegex(DeploymentError, "disallowed"):
                    StaticSite.load(site)

    def test_zip_creation_is_atomic_when_target_appears_after_precheck(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            site = StaticSite.load(self.sample(root))
            target = root / "race.zip"
            def race_output(_source, output):
                output.write_bytes(b"EXISTING CONTENT")
                return output
            with patch("static_deploy._validate_output", side_effect=race_output):
                with self.assertRaises(FileExistsError):
                    NulangCloudBundleProvider().prepare(site, target, "https://demo.example")
            self.assertEqual(target.read_bytes(), b"EXISTING CONTENT")

    def test_refuses_repository_root_and_overwriting_targets(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(DeploymentError):
                StaticSite.load(ROOT)
            site = StaticSite.load(self.sample(root))
            target = root / "published"
            target.mkdir()
            with self.assertRaisesRegex(DeploymentError, "exists"):
                CloudflareDirectoryProvider().prepare(site, target, "https://example.com")

    def test_rejects_output_path_that_resolves_inside_source(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            site = StaticSite.load(self.sample(root))
            (root / "alternate").mkdir()
            # A lexical prefix check is insufficient when an existing directory
            # component and .. resolve back inside the source tree.
            disguised = root / "alternate" / ".." / "site" / "nested-output"
            with self.assertRaisesRegex(DeploymentError, "outside"):
                CloudflareDirectoryProvider().prepare(site, disguised, "https://example.com")
            self.assertFalse((site.source / "nested-output").exists())

    def test_url_validation_rejects_paths_and_non_https(self):
        for url in ("http://example.com", "https://example.com/path", "https://user:pass@example.com",
                    "https://example.com/?q=1", "https://example.com/#anchor", "file:///tmp/site"):
            with self.subTest(url=url), self.assertRaises(DeploymentError):
                validate_site_url(url)
        self.assertEqual(validate_site_url("https://demo.example/"), "https://demo.example")

    def test_portable_origin_rejects_markup_and_invalid_hostnames(self):
        for url in ('https://demo.example"onload="bad',
                    "https://demo.example'onclick='bad",
                    'https://demo.example<svg',
                    'https://demo.example&amp;bad',
                    'https://demo..example',
                    'https://-bad.example'):
            with self.subTest(url=url), self.assertRaises(DeploymentError):
                validate_site_url(url)
        for origin in ('https://demo.example/?', 'https://demo.example/#',
                       'https://[fe80::1%25"x]', 'https://[fe80::1%25eth0]'):
            with self.subTest(origin=origin), self.assertRaises(DeploymentError):
                validate_site_url(origin)
        self.assertEqual(validate_site_url('https://[::1]/'), 'https://[::1]')

    def test_site_origin_rejects_raw_ascii_controls_before_url_parsing(self):
        for char in (chr(0), chr(1), chr(12), chr(31), chr(127)):
            for value in (char + "https://demo.example",
                          "https://demo.example" + char):
                with self.subTest(origin=repr(value)), self.assertRaises(DeploymentError):
                    validate_site_url(value)
        self.assertEqual(validate_site_url("https://demo.example/"),
                         "https://demo.example")

    def test_scandir_failure_cannot_silently_omit_static_assets(self):
        import os
        with TemporaryDirectory() as temp:
            root = Path(temp)
            site = self.sample(root)
            scan = os.scandir
            def broken_scan(path):
                if Path(path) == site / "css":
                    raise PermissionError("cannot list assets directory")
                return scan(path)
            with patch("static_deploy.os.scandir", side_effect=broken_scan):
                with self.assertRaisesRegex(PermissionError, "cannot list"):
                    StaticSite.load(site)

    def test_failed_archive_write_does_not_leave_partial_final_zip(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            site = StaticSite.load(self.sample(root))
            target = root / "site.zip"
            with patch("static_deploy._write_zip", side_effect=OSError("simulated disk full")):
                with self.assertRaisesRegex(OSError, "disk full"):
                    NulangCloudBundleProvider().prepare(site, target, "https://demo.example")
            self.assertFalse(target.exists())
            self.assertEqual(sorted(root.glob(".syntyr-*.tmp")), [])

    def test_completed_zip_reports_temp_cleanup_failure_without_losing_receipt(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            site = StaticSite.load(self.sample(root))
            target = root / "complete.zip"
            actual_unlink = Path.unlink

            def fail_temp_cleanup(path, *args, **kwargs):
                if path.name.startswith(".syntyr-"):
                    raise PermissionError("temporary cleanup denied")
                return actual_unlink(path, *args, **kwargs)

            with patch.object(Path, "unlink", fail_temp_cleanup):
                receipt = NulangCloudBundleProvider().prepare(
                    site, target, "https://demo.example")
            self.assertEqual(receipt["status"], "prepared_only")
            self.assertIn("temporary cleanup denied", receipt.get("cleanup_warning", ""))
            with ZipFile(target) as archive:
                self.assertEqual(archive.read("site/index.html"), b"<h1>Syntyr</h1>")

    def test_link_error_stays_primary_when_temp_cleanup_also_fails(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            site = StaticSite.load(self.sample(root))
            target = root / "no.zip"
            actual_unlink = Path.unlink

            def fail_temp_cleanup(path, *args, **kwargs):
                if path.name.startswith(".syntyr-"):
                    raise PermissionError("temporary cleanup denied")
                return actual_unlink(path, *args, **kwargs)

            with patch("static_deploy.os.link", side_effect=OSError("link publication failed")), (
                 patch.object(Path, "unlink", fail_temp_cleanup)):
                with self.assertRaisesRegex(OSError, "link publication failed"):
                    NulangCloudBundleProvider().prepare(site, target, "https://demo.example")
            self.assertFalse(target.exists())

    def test_hosting_guide_documents_atomic_bundle_filesystem_constraint(self):
        guide = (ROOT / "docs/nulang-cloud-hosting.md").read_text()
        self.assertIn("hard links", guide)
        self.assertIn("exFAT", guide)

    def test_cli_is_experimental_and_refuses_live_publish(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            site = self.sample(root)
            command = [sys.executable, str(ROOT / "scripts/static_deploy.py"),
                       "--provider", "nulang-cloud", "--site-dir", str(site),
                       "--site-url", "https://demo.example",
                       "--output", str(root / "site.zip")]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("experimental", result.stderr.lower())
            result = subprocess.run(command + ["--experimental-nulang-cloud", "--publish"],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not supported", result.stderr.lower())
            self.assertFalse((root / "site.zip").exists())
            result = subprocess.run(command + ["--experimental-nulang-cloud"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "site.zip").is_file())


class PortableBuildTests(unittest.TestCase):
    def test_portable_canonical_and_sitemap_paths_are_directly_servable(self):
        from build_cloudflare_site import source_files
        from urllib.parse import urlsplit
        portable = source_files(site_url="https://demo.example", include_cloudflare_headers=False)
        html = portable["docs/reference.html"].decode("utf-8")
        self.assertIn('<link rel="canonical" href="https://demo.example/docs/reference.html">', html)
        self.assertIn(b'https://demo.example/docs/reference.html', portable["sitemap.xml"])
        self.assertIn(b'https://demo.example/docs/', portable["sitemap.xml"])
        for entry in __import__('re').findall(r'<loc>([^<]+)</loc>', portable['sitemap.xml'].decode()):
            path = urlsplit(entry).path.lstrip('/')
            if not path or path.endswith('/'):
                path += 'index.html'
            self.assertIn(path, portable)
        cloudflare = source_files()
        self.assertIn(b'https://syntyr-css.pages.dev/docs/reference<', cloudflare['sitemap.xml'])
        self.assertNotIn(b'https://syntyr-css.pages.dev/docs/reference.html<', cloudflare['sitemap.xml'])

    def test_portable_origin_rewrites_first_party_open_graph_and_structured_metadata(self):
        from build_cloudflare_site import source_files
        files = source_files(site_url="https://demo.example", include_cloudflare_headers=False)
        home = files["index.html"].decode("utf-8")
        docs = files["docs/index.html"].decode("utf-8")
        blog = files["blog/index.html"].decode("utf-8")
        self.assertIn('property="og:url" content="https://demo.example/"', home)
        self.assertNotIn('property="og:url" content="https://syntyr-css.pages.dev/"', home)
        self.assertIn('"item":"https://demo.example/docs/"', docs)
        self.assertNotIn('"item":"https://syntyr-css.pages.dev/docs/"', docs)
        # Blog structured metadata must identify the portable deployment too.
        from re import findall
        scripts = findall(r'<script type="application/ld\+json">(.*?)</script>', blog, flags=__import__('re').S)
        self.assertTrue(scripts)
        self.assertFalse(any('https://syntyr-css.pages.dev/' in script for script in scripts))

    def test_portable_existing_open_graph_url_matches_directly_servable_canonical(self):
        from build_cloudflare_site import source_files
        import re
        for origin in ("https://demo.example", "https://syntyr-css.pages.dev"):
            with self.subTest(origin=origin):
                files = source_files(site_url=origin, include_cloudflare_headers=False)
                html = files["docs/faq.html"].decode("utf-8")
                canonical = re.search(r'<link rel="canonical" href="([^"]+)"', html)
                og = re.search(r'<meta property="og:url" content="([^"]+)"', html)
                self.assertIsNotNone(canonical)
                self.assertIsNotNone(og)
                self.assertEqual(og.group(1), canonical.group(1))
                self.assertEqual(og.group(1), origin + "/docs/faq.html")

    def test_site_export_supports_custom_origin_without_cloudflare_headers(self):
        from build_cloudflare_site import source_files
        files = source_files(site_url="https://demo.example", include_cloudflare_headers=False)
        self.assertNotIn("_headers", files)
        self.assertIn(b"https://demo.example/sitemap.xml", files["robots.txt"])
        self.assertIn(b"https://demo.example", files["sitemap.xml"])
        self.assertNotIn(b"https://syntyr-css.pages.dev", files["sitemap.xml"])
        self.assertIn(b'https://demo.example/', files["index.html"])


if __name__ == "__main__":
    unittest.main()
