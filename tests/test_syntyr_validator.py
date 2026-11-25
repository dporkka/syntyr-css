"""Source contract and optional static HTML validator behavior."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from export_api_metadata import outputs  # noqa: E402
from syntyr_check import validate_html  # noqa: E402


class ContractTests(unittest.TestCase):
    def test_contract_is_generated_and_complete(self):
        output = outputs()[ROOT / "metadata/syntyr-contract.json"]
        contract = json.loads(output)
        index = json.loads((ROOT / "metadata/syntyr-api.json").read_text())
        self.assertEqual(contract["schema_version"], 1)
        self.assertEqual(contract["source_version"], (ROOT / "VERSION").read_text().strip())
        self.assertEqual({c["name"] for c in contract["classes"]},
                         {c["name"] for c in index["classes"]})
        self.assertEqual({c["name"] for c in contract["tokens"]},
                         {c["name"] for c in index["tokens"]})
        self.assertIn("syn-button", {c["name"] for c in contract["classes"]})
        self.assertIn("syntyr.core.css", next(
            c["stylesheets"] for c in contract["classes"] if c["name"] == "syn-button"))
        self.assertIn("components/buttons.css", next(
            c["stylesheets"] for c in contract["classes"] if c["name"] == "syn-button"))
        self.assertIn("data-syn-theme", contract["attributes"])
        self.assertIn("studio", contract["attributes"]["data-syn-theme"])
        self.assertTrue(any(c["name"] == "Button" for c in contract["components"]))
        self.assertEqual(output, (ROOT / "metadata/syntyr-contract.json").read_text())


class ValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((ROOT / "metadata/syntyr-contract.json").read_text())

    def test_valid_document_and_local_classes(self):
        html = """<link rel="stylesheet" href="/assets/syntyr.core.css">
        <main class="syn-root app">
          <button class="syn-button syn-button--primary custom" type="button">Go</button>
        </main>"""
        self.assertEqual(validate_html(html, self.contract), [])

    def test_unknown_class_and_invalid_theme_have_source_positions(self):
        html = '<main class="syn-root syn-buttn" data-syn-theme="purple"></main>'
        diagnostics = validate_html(html, self.contract)
        self.assertEqual([x["code"] for x in diagnostics],
                         ["unknown-class", "invalid-attribute-value"])
        self.assertEqual(diagnostics[0]["line"], 1)
        self.assertEqual(diagnostics[0]["column"], 1)
        self.assertIn("syn-buttn", diagnostics[0]["message"])

    def test_missing_optional_stylesheet(self):
        html = """<link rel="stylesheet" href="syntyr.core.css">
        <main class="syn-root syn-pipeline"></main>"""
        diagnostics = validate_html(html, self.contract)
        self.assertEqual([x["code"] for x in diagnostics], ["missing-stylesheet"])
        self.assertIn("syntyr.recipes.css", diagnostics[0]["message"])

    def test_inline_fragments_without_stylesheet_are_valid(self):
        self.assertEqual(validate_html('<div class="syn-root syn-panel"></div>', self.contract), [])

    def test_explicit_stylesheet_list_and_submodules(self):
        html = '<main class="syn-root syn-button"></main>'
        self.assertEqual(validate_html(html, self.contract,
                                       stylesheets={"syntyr.core.css"}), [])
        diagnostics = validate_html(html, self.contract,
                                    stylesheets={"components/buttons.css"})
        self.assertEqual([x["code"] for x in diagnostics], ["missing-stylesheet"])
        self.assertIn("syn-root", diagnostics[0]["message"])

    def test_dynamic_class_fragment_is_not_treated_as_static_class(self):
        html = '<div class="syn-root {{ syn-unknown }}" data-syn-theme="{{ theme }}"></div>'
        self.assertEqual(validate_html(html, self.contract), [])

    def test_url_version_query_still_recognizes_stylesheet(self):
        html = ('<link rel="stylesheet" href="/v/0.3/syntyr.core.css?v=2">'
                '<main class="syn-root syn-panel"></main>')
        self.assertEqual(validate_html(html, self.contract), [])

    def test_density_values_are_validated(self):
        html = '<main data-syn-density="tiny" class="syn-root"></main>'
        self.assertEqual([d["code"] for d in validate_html(html, self.contract)],
                         ["invalid-attribute-value"])

    def test_full_document_reports_known_classes_outside_root(self):
        html = """<html><head><link rel="stylesheet" href="syntyr.core.css"></head>
        <body>
          <button class="syn-button">Outside</button>
          <main class="syn-root"><button class="syn-button">Inside</button></main>
          <div class="syn-panel">After root</div>
        </body></html>"""
        errors = [d for d in validate_html(html, self.contract)
                  if d["code"] == "unscoped-class"]
        self.assertEqual([d["class_name"] for d in errors],
                         ["syn-button", "syn-panel"])
        self.assertTrue(all("syn-root" in d["message"] for d in errors))

    def test_full_document_accepts_root_on_element_and_void_tags(self):
        html = """<html><head><link rel="stylesheet" href="syntyr.core.css"></head>
        <body><main class="syn-root syn-panel">
          <img src="icon.svg" alt="Icon">
          <button class="syn-button">In scope after a void tag</button>
          <section class="syn-panel"><button class="syn-button">Nested</button></section>
        </main></body></html>"""
        self.assertEqual(validate_html(html, self.contract), [])

    def test_fragments_and_dynamic_ancestor_scopes_are_not_flagged(self):
        fragment = '<button class="syn-button">Injected inside a host root</button>'
        self.assertEqual(validate_html(fragment, self.contract,
                                       stylesheets={"syntyr.core.css"}), [])
        dynamic_page = """<html><head><link rel="stylesheet" href="syntyr.core.css"></head>
        <body class="{{ root_class }}">
          <button class="syn-button">Scope established by the template</button>
        </body></html>"""
        self.assertEqual(validate_html(dynamic_page, self.contract), [])

    def test_inert_template_markup_may_be_inserted_into_a_different_root(self):
        html = """<html><head><link rel="stylesheet" href="syntyr.core.css"></head>
        <body><template id="new-panel"><button class="syn-button">Copy me</button></template>
        <main class="syn-root"><button class="syn-button">Current</button></main>
        </body></html>"""
        self.assertEqual(validate_html(html, self.contract), [])

    def test_cli_reports_json_and_nonzero_status_for_errors(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.html"
            path.write_text('<section class="syn-not-a-real-class"></section>')
            p = subprocess.run([sys.executable, "scripts/syntyr_check.py", "--format",
                                "json", str(path)], cwd=ROOT, text=True,
                               capture_output=True)
            self.assertEqual(p.returncode, 1, p.stderr)
            data = json.loads(p.stdout)
            self.assertEqual(data[0]["code"], "unknown-class")
            self.assertEqual(data[0]["file"], str(path))


if __name__ == "__main__":
    unittest.main()
