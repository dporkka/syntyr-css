"""Regression contracts for optional semantic HTML authoring support."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from syntyr_check import validate_html


class SemanticHTMLContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((ROOT / "metadata/syntyr-contract.json").read_text())

    def check(self, markup, *, semantic=True):
        return validate_html(markup, self.contract, semantic=semantic)

    def test_opt_in_never_changes_default_contract_validation(self):
        markup = '<main class="syn-root"><input id="q"><input id="q"></main>'
        self.assertEqual(self.check(markup, semantic=False), [])

    def test_duplicate_ids_are_reported_and_located(self):
        findings = self.check('<div id="same"></div>\n<div id="same"></div>')
        self.assertEqual([f["code"] for f in findings], ["duplicate-id"])
        self.assertEqual((findings[0]["line"], findings[0]["severity"]), (2, "error"))

    def test_labels_accept_implicit_and_explicit_associations(self):
        html = '''<form>
        <label>Search <input name="query"></label>
        <label for="region">Region</label><select id="region"><option>All</option></select>
        <textarea aria-label="Notes"></textarea>
        <button type="submit">Submit</button></form>'''
        self.assertEqual(self.check(html), [])

    def test_explicit_for_takes_precedence_over_wrapping_label(self):
        html = '<label for="other">Other <input id="self" name="self"></label><input id="other" name="other">'
        result = self.check(html)
        self.assertEqual([f["code"] for f in result], ["missing-form-label"])

    def test_unlabeled_controls_and_broken_associations(self):
        html = '<html><body><label for="absent">Region</label><input id="q" name="q"><textarea aria-describedby="missing"></textarea></body></html>'
        codes = [f["code"] for f in self.check(html)]
        self.assertEqual(codes.count("missing-form-label"), 2)
        self.assertIn("missing-label-target", codes)
        self.assertIn("missing-aria-reference", codes)

    def test_dynamic_templates_and_inert_templates_are_not_assumed_static(self):
        html = '''<html><body><label for="{{ field_id }}">Dynamic</label>
        <input id="{{ field_id }}" name="v">
        <template><input id="template-only"></template>
        <label><input type="checkbox" name="ok"> Confirm</label>
        <input type="hidden" name="csrf"></body></html>'''
        self.assertEqual(self.check(html), [])

    def test_image_submit_input_needs_accessible_name(self):
        missing = self.check('<input type="image" src="/submit.png">')
        self.assertEqual([f["code"] for f in missing], ["missing-form-label"])
        self.assertEqual(self.check('<input type="image" src="/submit.png" alt="Send request">'), [])
        self.assertEqual(self.check('<input type="image" src="/submit.png" aria-label="Send">'), [])
        self.assertEqual(self.check('<label>Send <input type="image" src="/submit.png"></label>'), [])

    def test_input_button_requires_value_or_accessible_label(self):
        self.assertEqual([f["code"] for f in self.check('<input type="button">')],
                         ["missing-form-label"])
        self.assertEqual(self.check('<input type="button" value="Add another">'), [])
        self.assertEqual(self.check('<input type="button" aria-label="Add another">'), [])
        self.assertEqual(self.check('<input type="submit"><input type="reset">'), [])

    def test_hidden_controls_skip_name_checks_but_not_target_integrity(self):
        html = ('<html><body><section hidden><input type="button" popovertarget="missing">'
                '<div><input type="image" src="/send.png"></div></section></body></html>')
        self.assertEqual([f["code"] for f in self.check(html)], ["missing-native-target"])
        self.assertEqual([f["code"] for f in self.check('<input type="button">')],
                         ["missing-form-label"])

    def test_title_supplies_native_accessible_name_fallback(self):
        self.assertEqual(self.check('<input type="button" title="Add item">'), [])
        self.assertEqual(self.check('<input type="image" src="/send.png" title="Submit image">'), [])
        self.assertEqual([f["code"] for f in self.check('<input type="button" title="   ">')],
                         ["missing-form-label"])

    def test_native_invoker_targets_checked_even_when_input_name_exempt(self):
        html = ('<html><body>'
                '<input type="button" aria-label="{{ label }}" popovertarget="missing">'
                '<input type="submit" commandfor="absent">'
                '<input type="reset" popovertarget="missing">'
                '<input type="hidden" commandfor="absent">'
                '</body></html>')
        self.assertEqual([f["code"] for f in self.check(html)],
                         ["missing-native-target"] * 4)

    def test_native_invoker_targets_must_exist_in_complete_html(self):
        html = ('<html><body><button popovertarget="missing">Open</button>'
                '<button commandfor="absent" command="show-modal">Dialog</button></body></html>')
        self.assertEqual([f["code"] for f in self.check(html)],
                         ["missing-native-target", "missing-native-target"])

    def test_popover_invoker_requires_actual_popover_target(self):
        html = ('<html><body><button popovertarget="panel">Open</button>'
                '<section id="panel">Ordinary section</section></body></html>')
        self.assertEqual([f["code"] for f in self.check(html)], ["invalid-popover-target"])
        valid = ('<html><body><button popovertarget="panel">Open</button>'
                 '<section id="panel" popover>Details</section>'
                 '<button commandfor="modal" command="show-modal">Dialog</button>'
                 '<dialog id="modal"><p>Details</p></dialog></body></html>')
        self.assertEqual(self.check(valid), [])

    def test_native_invoker_lint_does_not_guess_template_or_fragment_targets(self):
        self.assertEqual(self.check('<button popovertarget="outside">Open</button>'), [])
        self.assertEqual(self.check('<html><body><button popovertarget="{{ target_id }}">Open</button></body></html>'), [])

    def test_static_table_selection_uses_data_state_not_aria(self):
        html = '''<table><caption>Invoices</caption><thead><tr><th scope="col">Account</th></tr></thead>
          <tbody><tr aria-selected="true"><td>Acme</td></tr>
          <tr data-syn-state="selected"><td>Beta</td></tr></tbody></table>'''
        self.assertEqual([f["code"] for f in self.check(html)], ["aria-selected-static-table"])

    def test_interactive_grid_aria_selected_is_not_flagged(self):
        html = '<table role="grid" aria-label="Invoices"><tr aria-selected="true"><td>Acme</td></tr></table>'
        self.assertEqual(self.check(html), [])

    def test_unlabeled_data_table_is_advisory_not_a_parse_error(self):
        html = '<table><thead><tr><th scope="col">A</th></tr></thead><tbody><tr><td>One</td></tr></tbody></table>'
        result = self.check(html)
        self.assertEqual([(f["code"], f["severity"]) for f in result], [("table-missing-name", "warning")])

    def test_semantic_starter_is_classless_and_lint_clean(self):
        html = (ROOT / "examples/semantic-starter.html").read_text()
        self.assertIn("<form action=", html)
        self.assertNotIn('class="syn-form"', html)
        self.assertIn("<nav ", html)
        self.assertIn("<caption>", html)
        self.assertIn("<fieldset>", html)
        self.assertIn("<legend>", html)
        self.assertEqual(self.check(html), [])

    def test_semantic_css_respects_native_disclosure_and_forms(self):
        css = (ROOT / "src/semantic.css").read_text()
        self.assertIn("form:not([class])", css)
        self.assertIn("summary:not([class])", css)
        self.assertIn("min-block-size: 2.75rem", css)
        self.assertIn("label[data-syn-semantic]", css)

    def test_table_styles_confine_aria_selection_to_grids(self):
        css = (ROOT / "src/components/data.css").read_text()
        self.assertIn('data-syn-state="selected"', css)
        self.assertIn('[role="grid"]', css)
        self.assertIn('aria-selected="true"', css)
        self.assertNotIn('.syn-table tr[aria-selected="true"] {', css)

    def test_cli_semantic_flag_reports_errors_and_warning_only_exits_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "sample.html"
            path.write_text('<input id="x"><input id="x">')
            command = [sys.executable, "scripts/syntyr_check.py", "--semantic", "--format", "json", str(path)]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("duplicate-id", [f["code"] for f in json.loads(result.stdout)])
            path.write_text('<table><tr><th>Name</th></tr></table>')
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)[0]["severity"], "warning")


    def test_explicit_labels_must_target_labelable_elements(self):
        markup = ("<html><body>"
                  '<label for="card">Card</label><div id="card"></div>'
                  '<label for="token">Token</label><input id="token" type="hidden">'
                  '<label for="query">Query</label><input id="query" name="query">'
                  "</body></html>")
        issues = self.check(markup)
        self.assertEqual([f["code"] for f in issues],
                         ["invalid-label-target", "invalid-label-target"])

    def test_image_submit_control_requires_accessible_name(self):
        markup = ('<html><body><form><input type="image" src="submit.svg">'
                  '<input type="image" src="save.svg" alt="Save changes">'
                  '</form></body></html>')
        self.assertEqual([f["code"] for f in self.check(markup)],
                         ["missing-form-label"])

    def test_native_invokers_require_matching_popover_and_dialog_targets(self):
        markup = ("<html><body>"
                  '<button type="button" popovertarget="missing">Missing</button>'
                  '<button type="button" popovertarget="plain">Plain</button>'
                  '<div id="plain"></div>'
                  '<button type="button" commandfor="plain" command="show-modal">Wrong</button>'
                  '<button type="button" commandfor="missing-dialog" command="show-modal">Missing dialog</button>'
                  '<button type="button" popovertarget="menu">Menu</button>'
                  '<div popover id="menu"></div>'
                  '<button type="button" commandfor="modal" command="show-modal">Modal</button>'
                  '<dialog id="modal" aria-label="Review"></dialog>'
                  '</body></html>')
        self.assertEqual([f["code"] for f in self.check(markup)], [
            "missing-native-target", "invalid-popover-target",
            "invalid-dialog-target", "missing-native-target",
        ])

    def test_builtin_commands_match_ascii_case_insensitively(self):
        html = ('<html><body>'
                '<button commandfor="ordinary" command="SHOW-MODAL">Wrong dialog</button>'
                '<button commandfor="ordinary" command="REQUEST-CLOSE">Wrong close</button>'
                '<button commandfor="ordinary" command="TOGGLE-POPOVER">Popover event</button>'
                '<div id="ordinary"></div>'
                '<button commandfor="real-dialog" command="ShOw-MoDaL">Open</button>'
                '<dialog id="real-dialog"></dialog>'
                '</body></html>')
        self.assertEqual([f["code"] for f in self.check(html)],
                         ["invalid-dialog-target", "invalid-dialog-target"])

    def test_popover_commands_on_non_popover_html_targets_dispatch_command_event(self):
        html = ('<html><body>'
                '<button commandfor="panel" command="show-popover">Show</button>'
                '<button commandfor="panel" command="HIDE-POPOVER">Hide</button>'
                '<button commandfor="panel" command="toggle-popover">Toggle</button>'
                '<div id="panel"></div>'
                '<button popovertarget="panel">Invalid real popovertarget</button>'
                '</body></html>')
        self.assertEqual([f["code"] for f in self.check(html)], ["invalid-popover-target"])

    def test_custom_commands_and_dynamic_targets_are_not_false_positives(self):
        markup = ("<html><body>"
                  '<button type="button" commandfor="panel" command="--refresh">Refresh</button>'
                  '<div id="panel"></div>'
                  '<button type="button" popovertarget="{{ menu_id }}">Menu</button>'
                  '<button type="button" commandfor="{{ dialog_id }}" command="show-modal">Open</button>'
                  '</body></html>')
        self.assertEqual(self.check(markup), [])

    def test_native_reference_examples_remain_semantically_valid(self):
        for filename in ("native-apis.html", "native-elements.html", "native-recipes.html",
                         "semantic-starter.html"):
            with self.subTest(filename=filename):
                self.assertEqual(self.check((ROOT / "examples" / filename).read_text()), [])


    def test_datalist_references_must_target_real_datalist(self):
        markup = ('<html><body><form>'
                  '<label>Wrong <input list="ordinary"></label><div id="ordinary"></div>'
                  '<label>Missing <input list="missing"></label>'
                  '<label>Correct <input list="suggestions"></label>'
                  '<datalist id="suggestions"><option value="A"></datalist>'
                  '</form></body></html>')
        self.assertEqual([f["code"] for f in self.check(markup)],
                         ["invalid-datalist-target", "missing-native-target"])

    def test_summary_must_be_direct_child_of_details(self):
        markup = ('<html><body><summary>Not a disclosure</summary>'
                  '<details><div><summary>Nested</summary></div></details>'
                  '<details><summary>Correct</summary><p>Content</p></details>'
                  '</body></html>')
        self.assertEqual([f["code"] for f in self.check(markup)],
                         ["summary-outside-details", "summary-outside-details"])

    def test_fragment_native_references_are_left_to_host_document(self):
        self.assertEqual(self.check('<button popovertarget="host-popover">Open</button>'
                                    '<label>Suggestion <input list="host-list"></label>'), [])


    def test_all_first_party_examples_keep_valid_native_relationships(self):
        pages = sorted((ROOT / "examples").rglob("*.html"))
        self.assertGreater(len(pages), 40)
        for page in pages:
            with self.subTest(page=page.relative_to(ROOT)):
                findings = self.check(page.read_text())
                semantic_errors = [item for item in findings if item["severity"] == "error" and
                                   item["code"] not in ("missing-stylesheet", "unknown-class",
                                                        "unscoped-class")]
                self.assertEqual(semantic_errors, [])


if __name__ == "__main__":
    unittest.main()
