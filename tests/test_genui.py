import json
import unittest

from integrations.genui import render_json, GenUIError


def spec(node):
    return json.dumps({"version": 1, "root": node})


def node(kind, **props):
    return {"type": kind, "props": props}


class GenUITests(unittest.TestCase):
    def test_escapes_all_model_text(self):
        payload = '<img src=x onerror="alert(1)"> &'
        html = render_json(spec(node("Text", text=payload)))
        self.assertIn('&lt;img', html)
        self.assertIn('&quot;', html)
        self.assertNotIn('<img', html)

    def test_composes_semantic_html(self):
        tree = {"type": "Panel", "children": [
            node("Heading", text="Revenue", level=2),
            node("Metric", label="MRR", value="$1000"),
            node("Table", caption="Sales", columns=["Name", "Total"],
                 rows=[["A", "$20"]]),
            node("Progress", label="Done", value=2, max=3),
        ]}
        html = render_json(spec(tree))
        self.assertEqual(html, render_json(spec(tree)))
        for part in ['class="syn-root"', '<h2 class="syn-heading">Revenue</h2>',
                     '<caption>Sales</caption>', '<th scope="col">Name</th>',
                     '<progress value="2" max="3">']:
            self.assertIn(part, html)

    def test_rejects_unknown_types_properties_and_children(self):
        for bad in [
            node("Script", text="alert(1)"),
            node("Text", text="hi", onclick="alert(1)"),
            node("Text", text="hi", html="<b>hi</b>"),
            {"type": "Text", "props": {"text": "hi"}, "children": [node("Divider")]},
            node("Heading", text="hi", level=True),
            node("Heading", text="hi", level=7),
            node("Table", caption="A", columns=["A"], rows=[["1", "2"]]),
            node("Progress", label="A", value=2, max=1),
            node("Details", summary=""),
        ]:
            with self.subTest(bad=bad), self.assertRaises(GenUIError):
                render_json(spec(bad))

    def test_rejects_duplicate_keys_invalid_version_and_nonfinite(self):
        for bad in [
            '{"version":1,"version":1,"root":{"type":"Divider"}}',
            '{"version":true,"root":{"type":"Divider"}}',
            '{"version":1,"root":{"type":"Progress","props":{"label":"A","value":NaN,"max":1}}}',
            '{"version":1,"root":{"type":"Text","props":{"text":"\\ud800"}}}',
            'null', '{"version":1,"root":{}}',
        ]:
            with self.subTest(bad=bad), self.assertRaises(GenUIError):
                render_json(bad)

    def test_resource_limits(self):
        deep = node("Divider")
        for _ in range(20):
            deep = {"type": "Stack", "children": [deep]}
        for bad in [deep, {"type": "Stack", "children": [node("Divider")] * 257},
                    node("Text", text="x" * 4001)]:
            with self.assertRaises(GenUIError):
                render_json(spec(bad))
        with self.assertRaises(GenUIError):
            render_json(" " * 262145)

    def test_no_model_controlled_attributes_or_urls(self):
        for prop in ["class", "style", "href", "src", "id", "action"]:
            with self.assertRaises(GenUIError):
                render_json(spec(node("Badge", text="A", **{prop: "x"})))

    def test_all_primitives_have_semantics(self):
        tree = {"type": "Grid", "children": [
            {"type": "Stack", "children": [node("Text", text="Intro"),
              node("Badge", text="Beta"), node("List", items=["A", "B"]),
              {"type": "Details", "props": {"summary": "More"},
               "children": [node("Divider")]}]},
        ]}
        html = render_json(spec(tree))
        for part in ['class="syn-grid"', 'class="syn-stack"', '<ul class="syn-list">',
                     '<details><summary>More</summary>', '<hr>']:
            self.assertIn(part, html)
