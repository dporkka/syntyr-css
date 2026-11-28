"""Portable multi-page site starters and their deterministic offline exports."""
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts.build_cloudflare_site import source_files
from scripts.export_site_starter import (
    CORE, STARTER_ROOT, STARTER_ROUTES, check_starter, export_starter,
    verify_offline_site,
)

ROOT = Path(__file__).resolve().parents[1]


def snapshot(directory):
    return {path.relative_to(directory).as_posix(): path.read_bytes()
            for path in directory.rglob("*") if path.is_file()}


class PortableArchetypes(unittest.TestCase):
    def test_all_four_three_page_exports_are_self_contained_and_deterministic(self):
        self.assertEqual(set(STARTER_ROUTES), {"saas-marketing", "documentation", "blog", "portfolio"})
        with TemporaryDirectory() as temp:
            for name, routes in STARTER_ROUTES.items():
                with self.subTest(starter=name):
                    self.assertEqual(len(routes), 3)
                    one = export_starter(name, Path(temp) / (name + "-one"))
                    two = export_starter(name, Path(temp) / (name + "-two"))
                    self.assertEqual(snapshot(one), snapshot(two))
                    check_starter(name, one)
                    self.assertEqual(set(snapshot(one)), set(routes) | {
                        "assets/syntyr.core.css", "assets/site.css", "LICENSE"})
                    self.assertEqual((one / "assets/syntyr.core.css").read_bytes(), CORE.read_bytes())
                    self.assertEqual((one / "LICENSE").read_bytes(), (ROOT / "LICENSE").read_bytes())
                    for route in routes:
                        markup = (one / route).read_text()
                        self.assertIn('name="robots" content="noindex,follow"', markup)
                        self.assertNotIn("/dist/", markup)
                        self.assertNotIn("/shared/site.css", markup)
                        self.assertNotIn("<script", markup.lower())

    def test_check_reports_tampering_without_replacing_any_file(self):
        with TemporaryDirectory() as temp:
            output = export_starter("documentation", Path(temp) / "site")
            page = output / "index.html"
            page.write_text(page.read_text().replace("field notes", "changed notes"))
            before = snapshot(output)
            with self.assertRaisesRegex(ValueError, "Export differs from source"):
                check_starter("documentation", output)
            self.assertEqual(snapshot(output), before)
            (output / "surprise.txt").write_text("unexpected")
            with self.assertRaisesRegex(ValueError, "Unexpected export inventory"):
                check_starter("documentation", output)

    def test_invalid_links_reject_before_atomic_publication(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            shutil.copytree(STARTER_ROOT / "documentation", source / "documentation")
            shared = source / "shared/site.css"
            shared.parent.mkdir()
            shutil.copyfile(STARTER_ROOT / "shared/site.css", shared)
            page = source / "documentation/guide/index.html"
            original = page.read_text()
            with patch("scripts.export_site_starter.STARTER_ROOT", source), patch(
                    "scripts.export_site_starter.SHARED", shared):
                for bad in ("#does-not-exist", "../missing.html", "https://example.org/",
                            "//example.org/file", "../../outside.html", "/guide/index.html"):
                    with self.subTest(link=bad):
                        page.write_text(original.replace('href="#layout"', f'href="{bad}"'))
                        output = root / "export"
                        with self.assertRaises(ValueError):
                            export_starter("documentation", output)
                        self.assertFalse(output.exists())

    def test_duplicate_ids_script_and_base_are_rejected(self):
        with TemporaryDirectory() as temp:
            output = export_starter("blog", Path(temp) / "site")
            page = output / "index.html"
            original = page.read_text()
            for bad in ('<div id="main"></div>', '<script src="example.js"></script>',
                        '<base href="./">', '<a href="#" onclick="alert(1)">Action</a>'):
                with self.subTest(markup=bad):
                    page.write_text(original.replace("</main>", bad + "</main>"))
                    with self.assertRaises(ValueError):
                        verify_offline_site(output, STARTER_ROUTES["blog"])

    def test_export_refuses_existing_destination_for_every_archetype(self):
        with TemporaryDirectory() as temp:
            destination = Path(temp) / "existing"
            destination.mkdir()
            (destination / "keep.txt").write_text("unchanged")
            for starter in STARTER_ROUTES:
                with self.subTest(starter=starter), self.assertRaises(FileExistsError):
                    export_starter(starter, destination)
            self.assertEqual(snapshot(destination), {"keep.txt": b"unchanged"})

    def test_cloudflare_preview_is_allowlisted_and_noindexed(self):
        files = source_files()
        for starter, routes in STARTER_ROUTES.items():
            for route in routes:
                path = f"examples/site-starters/{starter}/{route}"
                self.assertIn(path, files)
                self.assertIn(b'name="robots" content="noindex,follow"', files[path])
        self.assertIn("examples/site-starters/shared/site.css", files)
        sitemap = files["sitemap.xml"].decode()
        for starter in STARTER_ROUTES:
            self.assertNotIn(f"/site-starters/{starter}/", sitemap)


if __name__ == "__main__":
    unittest.main()
