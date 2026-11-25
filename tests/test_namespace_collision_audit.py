"""Namespace collision audit is deterministic, with no third-party parser."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.audit_class_collisions import extract_css_classes, audit_stylesheet

ROOT = Path(__file__).resolve().parents[1]


class NamespaceCollisionAuditTests(unittest.TestCase):
    def test_css_parser_collects_selectors_in_nested_at_rules(self):
        css = r'''
        /* .syn-comment { } */
        @layer components {
          @media (min-width: 600px) {
            .syn-button:hover, :where(.syn-root) .syn-panel {
              content: ".syn-string";
              background-image: url("icon.syn-url.svg");
              color: red;
            }
          }
          .tw\:flex { display: flex; }
        }'''
        self.assertEqual(extract_css_classes(css),
                         {"syn-button", "syn-root", "syn-panel", "tw:flex"})

    def test_css_escapes_unicode_and_full_selector_names_are_preserved(self):
        css = r"""
        .syn-\70 anel { color: red; }
        .syn-panelé { color: blue; }
        .syn-\62 utton, .tw\:flex { opacity: 1; }
        .syn-\000070 anel { margin: 0; }
        """
        result = audit_stylesheet(css, {"syn-panel", "syn-button"},
                                  public_tokens={"--syn-accent"})
        self.assertEqual(result["exact_overlap"], ["syn-button", "syn-panel"])
        self.assertIn("syn-panelé", result["other_syn_classes"])
        self.assertIn("tw:flex", extract_css_classes(css))

    def test_feature_query_does_not_define_a_custom_property(self):
        css = """
        @supports (--syn-accent: red) {
            .host { color: red; }
        }
        :root { --syn-bg: white; }
        """
        result = audit_stylesheet(css, set(),
                                  public_tokens={"--syn-accent", "--syn-bg"})
        self.assertEqual(result["exact_token_overlap"], ["--syn-bg"])

    def test_reports_exact_collisions_and_prefixed_names_only(self):
        public = {"syn-button", "syn-panel", "syn-root"}
        result = audit_stylesheet(
            r".btn{} .syn-button:hover{} .syn-random{} .tw\:flex{}",
            public,
        )
        self.assertEqual(result["exact_overlap"], ["syn-button"])
        self.assertEqual(result["other_syn_classes"], ["syn-button", "syn-random"])
        self.assertEqual(result["other_class_count"], 4)

    def test_detects_exact_custom_property_collisions_without_matching_var_references(self):
        external = """
        :root { --syn-accent: red; --syn-other: var(--syn-bg);
                --other: var(--syn-root); }
        """
        result = audit_stylesheet(
            external, {"syn-root"},
            public_tokens={"--syn-accent", "--syn-bg"},
        )
        self.assertEqual(result["exact_token_overlap"], ["--syn-accent"])
        self.assertEqual(result["other_syn_tokens"], ["--syn-accent", "--syn-other"])

    def test_css_whitespace_only_pads_custom_property_names(self):
        # U+00A0 is not CSS whitespace; it belongs to the property name, so
        # `--syn-accent<NBSP>:` is a different (non-matching) declaration.
        css = ":root { --syn-accent\u00a0: red; --syn-bg : white; }"
        result = audit_stylesheet(css, set(),
                                  public_tokens={"--syn-accent", "--syn-bg"})
        self.assertEqual(result["exact_token_overlap"], ["--syn-bg"])

    def test_escaped_quote_outside_string_keeps_later_selectors(self):
        # `\"` is an escaped identifier character, not a string opener, so the
        # following `.syn-panel` selector must still be discovered.
        css = r'.host\"name .syn-panel{}'
        self.assertEqual(extract_css_classes(css), {'host"name', "syn-panel"})

    def test_quoted_strings_are_still_masked(self):
        css = '.syn-panel{ content: ".syn-hidden{}"; }'
        self.assertEqual(extract_css_classes(css), {"syn-panel"})

    def test_escaped_dot_is_not_a_class_selector_boundary(self):
        self.assertEqual(extract_css_classes(r".host\.syn-panel{}"),
                         {"host.syn-panel"})
        self.assertEqual(extract_css_classes(".host.syn-panel{}"),
                         {"host", "syn-panel"})

    def test_cli_json_fails_only_when_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            vendor = Path(tmp) / "host.css"
            vendor.write_text(".syn-panel{} .btn{}", encoding="utf-8")
            cmd = [sys.executable, "scripts/audit_class_collisions.py",
                   "--css", str(vendor), "--json"]
            result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["comparisons"][0]["exact_overlap"],
                             ["syn-panel"])
            strict = subprocess.run(cmd + ["--fail-on-overlap"], cwd=ROOT,
                                    capture_output=True, text=True)
            self.assertEqual(strict.returncode, 1)
            vendor.write_text(".btn{} .card{}", encoding="utf-8")
            clear = subprocess.run(cmd + ["--fail-on-overlap"], cwd=ROOT,
                                   capture_output=True, text=True)
            self.assertEqual(clear.returncode, 0, clear.stderr)


if __name__ == "__main__":
    unittest.main()
