"""Portable release example: offline assets, real links, no client-side code."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from zipfile import ZipFile
import tempfile
import unittest

from scripts.package_release import FILES, package

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = "examples/saas.html"
CSS_FILES = (
    "dist/syntyr.core.css",
    "dist/syntyr.recipes.css",
)


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stylesheets = []
        self.assets = []
        self.anchors = []
        self.ids = []
        self.classes = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "id" in values:
            self.ids.append(values["id"])
        self.classes.extend(values.get("class", "").split())
        if tag == "link" and values.get("rel") == "stylesheet":
            self.stylesheets.append(values["href"])
            self.assets.append(values["href"])
        if tag in ("script", "iframe"):
            self.scripts.append(tag)
        if tag in ("img", "source"):
            self.assets.append(values.get("src") or values.get("srcset", ""))
        if tag == "a":
            self.anchors.append(values.get("href", ""))


class PortableReleaseExampleTests(unittest.TestCase):
    def test_offline_example_and_its_styles_are_in_release_allowlist(self):
        self.assertIn(EXAMPLE, FILES)
        for path in CSS_FILES:
            with self.subTest(path=path):
                self.assertIn(path, FILES)

    def test_actual_archive_extracts_as_self_contained_demo(self):
        with tempfile.TemporaryDirectory(prefix="syntyr-portable-zip-") as tmp:
            archive_path = Path(tmp) / "release.zip"
            package(archive_path)
            with ZipFile(archive_path) as archive:
                archive.extractall(Path(tmp) / "unpacked")
            examples = list((Path(tmp) / "unpacked").glob("*/examples/saas.html"))
            self.assertEqual(len(examples), 1)
            example = examples[0]
            for asset in CSS_FILES:
                with self.subTest(asset=asset):
                    self.assertTrue((example.parent.parent / asset).is_file())

    def test_agent_workflow_candidate_is_self_contained_in_release_archive(self):
        with tempfile.TemporaryDirectory(prefix="syntyr-agent-zip-") as tmp:
            path = Path(tmp) / "release.zip"
            package(path)
            version = (ROOT / "VERSION").read_text().strip()
            prefix = f"syntyr-css-{version}/"
            with ZipFile(path) as archive:
                for name in ("examples/agent-workflow.html",
                             "metadata/agent-workflow.v1.json",
                             "dist/syntyr.core.css"):
                    self.assertEqual(archive.read(prefix + name), (ROOT / name).read_bytes())
                tags = Tags()
                tags.feed(archive.read(prefix + "examples/agent-workflow.html").decode())
                self.assertEqual(tags.stylesheets, ["../dist/syntyr.core.css"])
                self.assertEqual(tags.scripts, [])

    def test_example_has_no_external_assets_or_broken_local_navigation(self):
        tags = Tags()
        tags.feed((ROOT / EXAMPLE).read_text(encoding="utf-8"))
        self.assertEqual(tags.scripts, [])
        self.assertEqual(tags.stylesheets, ["../dist/syntyr.core.css", "../dist/syntyr.recipes.css"])
        self.assertEqual(len(tags.ids), len(set(tags.ids)), "Duplicate HTML ids")
        self.assertIn("main", tags.ids)
        self.assertIn("#main", tags.anchors, "Keyboard skip link required")
        for ref in tags.assets + tags.anchors:
            with self.subTest(ref=ref):
                self.assertTrue(ref, "Empty link or asset")
                url = urlsplit(ref)
                self.assertFalse(url.scheme or url.netloc, "Offline demo uses a remote resource")
                if ref.startswith("#"):
                    self.assertIn(ref[1:], tags.ids, "Broken fragment link")
                elif ref.startswith("../"):
                    target = (ROOT / "examples" / ref).resolve()
                    self.assertTrue(target.is_relative_to(ROOT))
                    self.assertTrue(target.exists(), "Missing local asset")
                    self.assertIn(str(target.relative_to(ROOT)), FILES, "Missing ZIP dependency")
                else:
                    self.fail(f"Unsupported path in portable example: {ref}")

    def test_example_uses_classes_from_published_alpha4(self):
        # A source-tree demo should not depend on unreleased alpha.5 styling.
        tags = Tags()
        tags.feed((ROOT / EXAMPLE).read_text(encoding="utf-8"))
        published = "".join((ROOT / "site-releases/0.3.0-alpha.4" / Path(p).name)
                            .read_text(encoding="utf-8") for p in CSS_FILES)
        for cls in tags.classes:
            if cls.startswith("syn-"):
                with self.subTest(cls=cls):
                    self.assertIn("." + cls, published, "Not in published alpha.4 CSS")

    def test_agent_index_discovers_offline_demo_with_version_warning(self):
        index = (ROOT / "llms.txt").read_text(encoding="utf-8")
        distribution = next(line for line in index.splitlines()
                            if "[Distribution and pinned CSS]" in line)
        self.assertIn("offline", distribution.lower())
        self.assertIn("alpha.5", distribution)
        self.assertIn("unreleased", distribution.lower())

    def test_release_documentation_explains_offline_demo(self):
        docs = (ROOT / "docs/distribution.md").read_text(encoding="utf-8")
        self.assertIn("examples/saas.html", docs)
        self.assertIn("offline", docs.lower())


if __name__ == "__main__":
    unittest.main()
