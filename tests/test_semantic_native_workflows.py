"""Script-free semantic workflow recipes, gallery and optional CSS contracts."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "examples/semantic-compositions.html"


class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.ids = set()
        self.errors = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if "id" in attrs:
            if attrs["id"] in self.ids:
                self.errors.append(f"duplicate id: {attrs['id']}")
            self.ids.add(attrs["id"])
        if tag == "script" or any(key.startswith("on") for key in attrs):
            self.errors.append(f"unexpected script: {tag}")
        if attrs.get("href", "").startswith("#"):
            self.tags.append(("fragment", {"target": attrs["href"][1:]}))


class NativeWorkflows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = GALLERY.read_text()
        cls.dom = Scan()
        cls.dom.feed(cls.html)

    def test_native_accordion_is_real_disclosure_without_script(self):
        items = [attrs for tag, attrs in self.dom.tags if tag == "details" and attrs.get("name") == "syn-semantic-faq"]
        self.assertGreaterEqual(len(items), 2)
        self.assertEqual(sum("open" in attrs for attrs in items), 1)
        self.assertIn("<summary>", self.html)
        self.assertFalse(self.dom.errors, self.dom.errors)

    def test_search_and_topic_forms_have_real_get_targets(self):
        forms = [attrs for tag, attrs in self.dom.tags if tag == "form" and attrs.get("action") == "https://github.com/dporkka/syntyr-css/issues"]
        self.assertEqual(len(forms), 2)
        self.assertTrue(all(f.get("method", "").lower() == "get" for f in forms))
        self.assertIn("search", [t for t, _ in self.dom.tags])
        names = [attrs.get("name") for tag, attrs in self.dom.tags if tag in ("input", "select")]
        self.assertGreaterEqual(names.count("q"), 2)
        for tag in ("fieldset", "legend", "optgroup", "option", "label", "button"):
            self.assertIn(tag, [t for t, _ in self.dom.tags])

    def test_published_csp_explicitly_allows_only_issues_form_target(self):
        from scripts.build_cloudflare_site import source_files
        headers = source_files()["_headers"].decode("utf-8")
        policy = next(line.strip() for line in headers.splitlines()
                      if line.strip().startswith("Content-Security-Policy:"))
        self.assertIn(
            "form-action 'self' https://github.com/dporkka/syntyr-css/issues;",
            policy,
        )

    def test_semantic_guide_is_in_agent_index_and_consolidated_reference(self):
        from scripts.build_agent_docs import SOURCES
        path = "docs/semantic-components.md"
        self.assertIn(path, SOURCES)
        self.assertIn(path, (ROOT / "llms.txt").read_text(encoding="utf-8"))
        self.assertIn(path, (ROOT / "llms-full.txt").read_text(encoding="utf-8"))

    def test_progress_and_meter_are_distinct_accessible_measures(self):
        vals = [attrs for tag, attrs in self.dom.tags if tag == "progress"]
        measures = [attrs for tag, attrs in self.dom.tags if tag == "meter"]
        self.assertGreaterEqual(len(vals), 1)
        self.assertGreaterEqual(len(measures), 1)
        self.assertTrue(all("value" in v and "max" in v for v in vals))
        self.assertTrue(all(all(key in v for key in ("value", "min", "max", "low", "high", "optimum")) for v in measures))
        self.assertIn("output", [t for t, _ in self.dom.tags])
        self.assertIn("Illustrative status", self.html)

    def test_responsive_media_uses_local_assets_and_real_caption(self):
        for tag in ("figure", "picture", "source", "img", "figcaption"):
            self.assertIn(tag, [t for t, _ in self.dom.tags])
        sources = [a for t, a in self.dom.tags if t == "source" and "srcset" in a]
        self.assertTrue(any("studio-settings.webp" in a["srcset"] and a.get("media") for a in sources))
        images = [a for t, a in self.dom.tags if t == "img" and "studio-editor.webp" in a.get("src", "")]
        self.assertEqual(len(images), 1)
        self.assertTrue(images[0].get("alt"))
        self.assertEqual((images[0]["width"], images[0]["height"]), ("1120", "700"))
        self.assertEqual(images[0].get("loading"), "lazy")
        for name in ("studio-editor.webp", "studio-settings.webp"):
            self.assertTrue((ROOT / "docs/previews" / name).is_file())

    def test_navigation_and_documentation_are_complete(self):
        anchors = [a["target"] for t, a in self.dom.tags if t == "fragment"]
        self.assertTrue(all(a in self.dom.ids for a in anchors), "broken gallery fragment link")
        docs = (ROOT / "docs/semantic-components.md").read_text()
        for section in ("## Native FAQ disclosure", "## Semantic issue search",
                        "## Grouped choice form", "## Progress and measurement",
                        "## Responsive captioned media"):
            with self.subTest(section=section):
                self.assertIn(section, docs)
        self.assertIn("no JavaScript", docs)
        self.assertIn("name=\"syn-semantic-faq\"", docs)
        self.assertIn('aria-label="On this page"', self.html)
        self.assertIn('href="examples/semantic-compositions.html"', (ROOT / "index.html").read_text())

    def test_open_disclosures_get_only_scoped_optional_styling(self):
        css = (ROOT / "src/semantic.css").read_text()
        self.assertIn("details[open]:not([class])", css)
        self.assertIn("details[open][data-syn-semantic]", css)
        self.assertNotIn("appearance: none", css)
        self.assertNotIn("display: none", css)


if __name__ == "__main__":
    unittest.main()
