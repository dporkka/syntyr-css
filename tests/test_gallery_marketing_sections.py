"""New copyable website sections: real media, semantics, CSS-only interactions."""
from html.parser import HTMLParser
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
NEW = {
    "image-gallery": "Portfolio",
    "image-story": "Marketing",
    "testimonials-grid": "Marketing",
    "milestone-timeline": "Services",
    "event-agenda": "Services",
}


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.nodes = []

    def handle_starttag(self, tag, attrs):
        self.nodes.append((tag, dict(attrs)))


class NewWebsiteSectionsTests(unittest.TestCase):
    def test_all_five_sections_are_copyable_and_script_free(self):
        blocks = json.loads((ROOT / "blocks/manifest.json").read_text())["blocks"]
        by_id = {block["id"]: block for block in blocks}
        for ident, category in NEW.items():
            with self.subTest(ident=ident):
                self.assertIn(ident, by_id)
                self.assertEqual(by_id[ident]["category"], category)
                self.assertIn("core", by_id[ident]["modules"])
                source = (ROOT / "blocks/snippets" / f"{ident}.html").read_text()
                parsed = Elements()
                parsed.feed(source)
                self.assertIn("h2", [tag for tag, _ in parsed.nodes])
                self.assertNotIn("script", [tag for tag, _ in parsed.nodes])
                self.assertNotIn("javascript:", source)
                self.assertNotIn('href="#"', source)

    def test_image_gallery_is_accessible_and_uses_own_hosted_art(self):
        source = (ROOT / "blocks/snippets/image-gallery.html").read_text()
        parsed = Elements()
        parsed.feed(source)
        photos = [attrs for tag, attrs in parsed.nodes if tag == "img"]
        self.assertGreaterEqual(len(photos), 4)
        self.assertEqual(len(photos), len([1 for tag, _ in parsed.nodes if tag == "figcaption"]))
        for attrs in photos:
            self.assertTrue(attrs.get("alt"))
            self.assertEqual(attrs.get("loading"), "lazy")
            self.assertGreater(int(attrs.get("width", 0)), 0)
            self.assertGreater(int(attrs.get("height", 0)), 0)
            self.assertTrue((ROOT / "docs" / attrs["src"]).is_file())
        links = [attrs.get("href") for tag, attrs in parsed.nodes if tag == "a"]
        for attrs in photos:
            self.assertIn(attrs["src"], links)
        css = (ROOT / "src/components/patterns.css").read_text()
        self.assertIn(".syn-image-gallery", css)
        self.assertIn("object-fit: cover", css)

    def test_other_sections_have_semantic_content(self):
        for ident, expected in {
            "image-story": {"figure", "img", "figcaption"},
            "testimonials-grid": {"blockquote", "cite"},
            "milestone-timeline": {"ol", "time"},
            "event-agenda": {"ol", "time"},
        }.items():
            with self.subTest(ident=ident):
                parsed = Elements()
                parsed.feed((ROOT / "blocks/snippets" / f"{ident}.html").read_text())
                self.assertTrue(expected.issubset({tag for tag, _ in parsed.nodes}))

    def test_portable_registry_bundles_all_image_assets(self):
        import tempfile
        from scripts.build_shadcn_registry import generate
        from scripts.registry_install import plan_install, apply_install
        registry = generate()
        for ident, count in (("image-gallery", 4), ("image-story", 1)):
            payload = json.loads(registry[f"r/{ident}.json"])
            targets = [file["target"] for file in payload["files"] if "/assets/" in file["target"]]
            self.assertEqual(len(targets), count)
            self.assertTrue(all(target.endswith(".svg") for target in targets))
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            # Checked-in registry contains the same dependencies as the generated one.
            plan = plan_install("image-gallery", project)
            self.assertEqual(len([p for p in plan["files"] if "/assets/" in p["path"]]), 4)
            apply_install(plan, project)
            self.assertTrue((project / "syntyr/assets/gallery-horizon.svg").is_file())

    def test_generated_gallery_includes_copyable_previews(self):
        gallery = (ROOT / "docs/blocks.html").read_text()
        for ident in NEW:
            self.assertIn(f'data-block-id="{ident}"', gallery)
            self.assertIn(f'id="block-title-{ident}"', gallery)


if __name__ == "__main__":
    unittest.main()
