"""CSS-only file lifecycle recipes: native picker, truthful queue snapshots, no transport."""
from html.parser import HTMLParser
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.ids = set()
        self.label_targets = set()
        self.scripts = 0
        self.action_buttons = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "label" and a.get("for"):
            self.label_targets.add(a["for"])
        if tag == "script":
            self.scripts += 1
        if tag == "button":
            self.action_buttons += 1


class FileLifecycleRecipesTest(unittest.TestCase):
    def test_optional_css_queue_and_states_share_core_file_control(self):
        css = read("src/recipes.css")
        self.assertIn("&.syn-file-queue", css)
        self.assertIn("&.syn-file-item", css)
        self.assertIn("&.syn-file-item-header", css)
        for state in ("queued", "uploading", "complete", "failed"):
            with self.subTest(state=state):
                self.assertIn(f'&.syn-file-item[data-syn-state="{state}"]', css)
        self.assertIn("@media (forced-colors: active)", css)
        self.assertIn("overflow-wrap: anywhere;", css)
        self.assertIn("progress", css)
        self.assertNotIn(".syn-file-queue", read("dist/syntyr.core.css"))
        self.assertIn("&.syn-file-queue", read("dist/syntyr.recipes.css"))

    def test_static_example_is_semantic_and_never_claims_to_upload(self):
        html = read("examples/file-lifecycle.html")
        p = Tags()
        p.feed(html)
        input_files = [a for t, a in p.tags if t == "input" and a.get("type") == "file"]
        self.assertEqual(len(input_files), 1)
        self.assertIn("multiple", input_files[0])
        self.assertTrue(p.label_targets <= p.ids)
        self.assertIn(input_files[0]["id"], p.label_targets)
        self.assertGreaterEqual(sum(t == "progress" for t, _ in p.tags), 2)
        self.assertGreaterEqual(sum(t == "li" for t, _ in p.tags), 4)
        queue_roles = [a.get("role") for tag, a in p.tags
                       if tag == "ol" and "syn-file-queue" in a.get("class", "").split()]
        self.assertEqual(queue_roles, ["list"],
                         "Marker-free file queues must keep list semantics in Safari/VoiceOver")
        states = {a.get("data-syn-state") for _, a in p.tags}
        self.assertTrue({"queued", "uploading", "complete", "failed"} <= states)
        self.assertEqual(p.scripts, 0)
        self.assertEqual(p.action_buttons, 0)
        self.assertIn("does not upload", html.lower())
        self.assertIn("illustrative", html.lower())
        self.assertIn("../dist/syntyr.core.css", html)
        self.assertIn("../dist/syntyr.recipes.css", html)

    def test_docs_and_machine_readable_exports(self):
        docs = read("docs/recipes.md")
        self.assertIn("file-lifecycle.html", docs)
        self.assertIn("syn-file-queue", docs)
        self.assertIn('<ol class="syn-file-queue" role="list">', docs,
                      "Copyable queue must explicitly retain list semantics")
        self.assertIn("Safari", docs, "Explain role=list when list markers are removed")
        self.assertIn("host application", docs.lower())
        self.assertIn("file-lifecycle.html", read("README.md"))
        self.assertIn("file-lifecycle.html", read("docs/index.html"))
        self.assertIn("file-lifecycle.html", read("scripts/build_cloudflare_site.py"))
        api = json.loads(read("metadata/syntyr-api.json"))
        classes = {item["name"] for item in api["classes"]}
        self.assertTrue({"syn-file-queue", "syn-file-item", "syn-file-item-header"} <= classes)
        manifest = json.loads(read("metadata/components.json"))
        self.assertTrue(any(c["name"] == "File lifecycle" for c in manifest["components"]))


if __name__ == "__main__":
    unittest.main()
