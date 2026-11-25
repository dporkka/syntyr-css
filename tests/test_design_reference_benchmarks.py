"""Contracts for three Syntyr design benchmark applications and reproducible asset reporting."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("marketing", "crm", "documentation")
BASE = ROOT / "examples" / "design-benchmarks"


class ContentProbe(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.links = []
        self.ids = set()
        self.fragment_links = []
        self.inputs = []
        self.labels = []
        self.mains = 0
        self.headings = 0

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        self.tags.append(tag)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "main":
            self.mains += 1
        if tag == "h1":
            self.headings += 1
        if tag == "a" and attrs.get("href", "").startswith("#"):
            self.fragment_links.append(attrs["href"][1:])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.links.append(attrs.get("href", ""))
        if tag in {"input", "select", "textarea"} and attrs.get("type") != "hidden":
            self.inputs.append(attrs)
        if tag == "label":
            self.labels.append(attrs)


class DesignReferenceBenchmarkTest(unittest.TestCase):
    def test_three_independent_real_world_benchmark_pages(self):
        for kind in PAGES:
            with self.subTest(kind=kind):
                page = BASE / f"{kind}.html"
                probe = ContentProbe()
                markup = page.read_text(encoding="utf-8")
                probe.feed(markup)
                self.assertEqual(probe.mains, 1)
                self.assertEqual(probe.headings, 1)
                self.assertIn("syn-root", markup)
                self.assertIn('href="#main"', markup)
                self.assertIn("main", probe.ids)
                self.assertNotIn("script", probe.tags)
                self.assertFalse(any(link.startswith(("https:", "http:", "//")) for link in probe.links))
                self.assertIn("../../dist/syntyr.core.css", probe.links)
                self.assertTrue(all((page.parent / link).resolve().is_file() for link in probe.links))
                self.assertTrue(all(ref in probe.ids for ref in probe.fragment_links if ref))
                self.assertGreaterEqual(len(probe.tags), 30)
                for field in probe.inputs:
                    self.assertTrue(field.get("id"))
                    self.assertTrue(any(l.get("for") == field["id"] for l in probe.labels))

    def test_benchmarks_and_human_guide_are_published_explicitly(self):
        from scripts.build_cloudflare_site import source_files
        files = source_files()
        for name in PAGES:
            self.assertIn(f"examples/design-benchmarks/{name}.html", files)
        self.assertIn("examples/design-benchmarks/benchmark.css", files)
        self.assertIn("docs/design-reference-matrix.md", files)
        self.assertIn("docs/design-reference-matrix.html", files)
        self.assertIn(b"design-reference-matrix.html", files["docs/reference.html"])

    def test_research_matrix_contains_actionable_evidence_and_boundaries(self):
        document = (ROOT / "docs/design-reference-matrix.md").read_text(encoding="utf-8")
        self.assertIn("Open Props", document)
        self.assertIn("W3C", document)
        self.assertIn("PatternFly", document)
        self.assertIn("Commercial", document)
        self.assertIn("Do not copy", document)
        self.assertGreaterEqual(document.count("https://"), 10)
        self.assertIn("design_reference_audit.py", document)
        self.assertIn("documentation.html", document)

    def test_offline_audit_reports_separate_asset_classes_for_each_page(self):
        completed = subprocess.run(
            [sys.executable, "scripts/design_reference_audit.py", "--json"],
            cwd=ROOT, capture_output=True, text=True, check=True
        )
        audit = json.loads(completed.stdout)
        self.assertEqual(set(audit["pages"]), set(PAGES))
        for name, report in audit["pages"].items():
            with self.subTest(name=name):
                self.assertEqual(report["runtime_js_bytes"], 0)
                self.assertEqual(report["external_stylesheets"], 0)
                self.assertEqual(report["missing_stylesheets"], 0)
                self.assertGreater(report["syntyr_css_gzip_bytes"], 0)
                self.assertGreater(report["markup_bytes"], 500)
                self.assertGreaterEqual(report["custom_css_gzip_bytes"], 0)
                self.assertEqual(report["script_tags"], 0)

    def test_audit_counts_inline_event_handler_javascript(self):
        from scripts.design_reference_audit import audit_page
        markup = '<button onclick="alert(1)" onkeydown="return false">Run</button>'
        report = audit_page(markup, BASE)
        self.assertEqual(report["runtime_js_bytes"], len("alert(1)return false"))
        self.assertEqual(report["script_tags"], 0)

        image = audit_page('<img src="fixture.png" onerror="recover()" />', BASE)
        self.assertEqual(image["runtime_js_bytes"], len("recover()"))

        unrelated = audit_page('<p one="note" only="metadata">Text</p>', BASE)
        self.assertEqual(unrelated["runtime_js_bytes"], 0)

    def test_audit_counts_unique_tokens_in_style_elements_and_attributes(self):
        from scripts.design_reference_audit import audit_page
        markup = (
            '<style>.card { --syn-accent: red; --syn-space: 1rem; }</style>'
            '<div style="--syn-accent : blue; --syn-radius: 4px">Card</div>'
        )
        report = audit_page(markup, BASE)
        self.assertEqual(report["custom_token_overrides"], 3)

    def test_audit_excludes_comments_and_strings_from_custom_token_declarations(self):
        from scripts.design_reference_audit import audit_page
        markup = (
            '<style>/* --syn-fake: red */ .card { content: "--syn-string: blue"; '
            '--syn-real: purple; /* --syn-fake: yellow; */ --syn-other: 3px; }</style>'
            '<div style="/* --syn-fake: black */ --syn-real: green">Card</div>'
        )
        self.assertEqual(audit_page(markup, BASE)["custom_token_overrides"], 2)

    def test_audit_accounts_for_inline_css_without_changing_linked_css_totals(self):
        from scripts.design_reference_audit import audit_page
        import gzip
        styles = [".card { --syn-accent: red }", "--syn-radius: 4px"]
        markup = f"<style>{styles[0]}</style><div style='{styles[1]}'>Card</div>"
        report = audit_page(markup, BASE)
        inline = "\n".join(styles).encode("utf-8")
        self.assertEqual(report["custom_css_bytes"], 0)
        self.assertEqual(report["custom_css_gzip_bytes"], 0)
        self.assertEqual(report["inline_css_bytes"], sum(len(s.encode("utf-8")) for s in styles))
        self.assertEqual(report["inline_css_gzip_bytes"], len(gzip.compress(inline, mtime=0)))
        self.assertEqual(report["custom_css_total_bytes"], report["inline_css_bytes"])
        self.assertEqual(report["custom_css_total_gzip_bytes"], report["inline_css_gzip_bytes"])

        linked = audit_page('<link rel="stylesheet" href="benchmark.css">' + markup, BASE)
        self.assertGreater(linked["custom_css_bytes"], 0)
        self.assertGreater(linked["custom_css_gzip_bytes"], 0)
        self.assertEqual(linked["custom_css_total_bytes"], linked["custom_css_bytes"] + linked["inline_css_bytes"])
        self.assertEqual(linked["custom_css_total_gzip_bytes"], linked["custom_css_gzip_bytes"] + linked["inline_css_gzip_bytes"])

    def test_mixed_case_stylesheet_rel_is_counted(self):
        from scripts.design_reference_audit import audit_page
        lower = audit_page('<link rel="stylesheet" href="benchmark.css">', BASE)
        mixed = audit_page('<link rel="preload StyleSheet" href="benchmark.css">', BASE)
        for field in ("custom_css_bytes", "custom_css_gzip_bytes",
                      "custom_token_overrides", "external_stylesheets", "missing_stylesheets"):
            self.assertEqual(lower[field], mixed[field], field)
        self.assertGreater(mixed["custom_css_bytes"], 0)

    def test_imported_stylesheets_are_rejected_not_silently_unmeasured(self):
        from scripts.design_reference_audit import audit_page
        import tempfile
        # External AND local imports change the measured transfer graph.
        for css in ('@import url("https://example.org/theme.css");',
                    '@IMPORT "extra.css";', '@import url(extra.css) screen;'):
            with self.subTest(css=css):
                with self.assertRaisesRegex(ValueError, "CSS @import"):
                    audit_page(f'<style>{css}</style>', BASE)
                with tempfile.TemporaryDirectory(dir=BASE) as tmp:
                    path = Path(tmp) / "import.css"
                    path.write_text(css, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "CSS @import"):
                        audit_page(f'<link rel="stylesheet" href="{path.relative_to(BASE)}">', BASE)

        # Tokens in comments/quoted content are not functional at-rules.
        harmless = '<style>/* @import url("ignore.css"); */ .x { content:"@import"; }</style>'
        self.assertEqual(audit_page(harmless, BASE)["external_stylesheets"], 0)

    def test_audit_deduplicates_stylesheet_path_aliases(self):
        from scripts.design_reference_audit import audit_page
        single = audit_page('<link rel="stylesheet" href="benchmark.css">', BASE)
        aliased = audit_page(
            '<link rel="stylesheet" href="benchmark.css">'
            '<link rel="stylesheet" href="./benchmark.css">',
            BASE
        )
        for field in ("custom_css_bytes", "custom_css_gzip_bytes",
                      "custom_css_total_bytes", "custom_css_total_gzip_bytes",
                      "custom_token_overrides"):
            self.assertEqual(aliased[field], single[field], field)

    def test_audit_rejects_remote_stylesheet_or_missing_stylesheet(self):
        from scripts.design_reference_audit import audit_page
        with self.assertRaisesRegex(ValueError, "external stylesheet"):
            audit_page("<link rel='stylesheet' href='https://example.com/ui.css'>", BASE)
        with self.assertRaisesRegex(FileNotFoundError, "missing.css"):
            audit_page("<link rel='stylesheet' href='missing.css'>", BASE)


if __name__ == "__main__":
    unittest.main()
