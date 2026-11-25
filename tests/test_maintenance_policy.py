"""Regression tests for source ownership and low-entropy CSS distribution."""
from pathlib import Path
import tempfile
import unittest

from scripts.maintenance_policy import find_issues


class MaintenancePolicyTests(unittest.TestCase):
    def test_current_source_and_distribution_registry_have_no_drift(self):
        self.assertEqual(find_issues(), [])

    def test_root_font_role_aliases_have_one_canonical_default(self):
        tokens = (Path(__file__).resolve().parents[1] / "src/tokens.css").read_text()
        self.assertEqual(tokens.count("--syn-font-ui: var(--syn-font);"), 1)
        self.assertEqual(tokens.count("--syn-font-display: var(--syn-font);"), 1)

    def test_duplicate_bundle_sources_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory)
            (src / "tokens.css").write_text("@layer syn.tokens {}")
            issues = find_issues(src, {"syntyr.core.css": ("tokens.css", "tokens.css")})
            self.assertTrue(any("duplicate source" in issue for issue in issues), issues)

    def test_unregistered_css_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory)
            (src / "tokens.css").write_text("@layer syn.tokens {}")
            (src / "abandoned.css").write_text(".unused { color: red; }")
            issues = find_issues(src, {"syntyr.core.css": ("tokens.css",)})
            self.assertTrue(any("unregistered source: abandoned.css" in issue for issue in issues), issues)

    def test_missing_registered_css_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            issues = find_issues(Path(directory), {"syntyr.core.css": ("missing.css",)})
            self.assertTrue(any("missing source: missing.css" in issue for issue in issues), issues)

    def test_component_theme_forks_are_rejected_but_token_themes_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory)
            (src / "components").mkdir()
            (src / "tokens.css").write_text(':where(.syn-root[data-syn-theme="noir"]) { --syn-bg: black; }')
            (src / "components" / "card.css").write_text('/* [data-syn-theme="ignored"] */\n.syn-card[data-syn-theme="noir"] { color: red; }')
            bundles = {"syntyr.core.css": ("tokens.css", "components/card.css")}
            issues = find_issues(src, bundles)
            self.assertTrue(any("component theme fork" in issue for issue in issues), issues)
            (src / "components" / "card.css").write_text('/* [data-syn-theme="ignored"] */\n.syn-card { color: var(--syn-bg); }')
            self.assertEqual(find_issues(src, bundles), [])

    def test_optional_recipes_cannot_fork_presentation_by_theme(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory)
            (src / "recipes.css").write_text('.syn-card[data-syn-theme="noir"] { border: 1px solid red; }')
            issues = find_issues(src, {"syntyr.recipes.css": ("recipes.css",)})
            self.assertTrue(any("theme fork" in issue for issue in issues), issues)

    def test_core_refuses_framework_specific_css_directives_and_selectors(self):
        examples = (
            "@theme inline { --color-ui: blue; }",  # Tailwind v4
            ".syn-root { @apply flex; }",  # Tailwind-only syntax
            ".syn-shadcn { color: red; }",  # Adapter-owned surface
            ".syn-shadcn-button { color: red; }",  # Adapter-owned extension
            ".syn-radix[data-state=\"open\"] { color: red; }",  # Adapter-owned surface
            ".syn-root { color: var(--radix-popover-trigger-width); }",  # Vendor variable
            ".syn-root[data-radix-menu-content] { color: red; }",  # Vendor DOM shape
        )
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory)
            file = src / "components" / "card.css"
            file.parent.mkdir()
            registry = {"syntyr.core.css": ("components/card.css",)}
            for css in examples:
                with self.subTest(css=css):
                    file.write_text(css)
                    issues = find_issues(src, registry)
                    self.assertTrue(any("integration leak" in issue for issue in issues), issues)

    def test_comments_do_not_trigger_integration_leak_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory)
            file = src / "tokens.css"
            file.write_text("/* @apply .syn-radix --tw-color */\n.syn-root { color: var(--syn-text, CanvasText); }")
            self.assertEqual(find_issues(src, {"syntyr.core.css": ("tokens.css",)}), [])

    def test_css_imports_rejected_in_css_core(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory)
            f = src / "tokens.css"
            registry = {"syntyr.core.css": ("tokens.css",)}
            for value in ('@import "theme.css";', '@import url("https://example.org/font.css");'):
                with self.subTest(value=value):
                    f.write_text(value, encoding="utf-8")
                    self.assertTrue(any("CSS import" in e for e in find_issues(src, registry)))

    def test_import_after_same_line_layer_statement_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory)
            f = src / "tokens.css"
            registry = {"syntyr.core.css": ("tokens.css",)}
            for snippet in (
                '@layer syn.tokens; @import "https://example.org/theme.css";',
                '@layer syn.tokens; @import "theme.css";',
            ):
                with self.subTest(snippet=snippet):
                    f.write_text(snippet, encoding="utf-8")
                    self.assertTrue(any("CSS import" in e for e in find_issues(src, registry)))

    def test_url_tokens_inside_css_strings_are_not_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory)
            f = src / "tokens.css"
            registry = {"syntyr.core.css": ("tokens.css",)}
            f.write_text(
                '.syn-root::before { content: "url(/help) @import \\"fake.css\\""; }',
                encoding="utf-8",
            )
            self.assertEqual(find_issues(src, registry), [])

    def test_native_hidden_important_guard_is_only_extra_base_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory)
            f = src / "base.css"
            registry = {"syntyr.core.css": ("base.css",)}
            css = (
                '@layer syn.base {'
                ':where(.syn-root[hidden]:not([hidden="until-found" i]), '
                '.syn-root [hidden]:not([hidden="until-found" i])) {'
                'display: none !important;} }'
            )
            f.write_text(css, encoding="utf-8")
            self.assertEqual(find_issues(src, registry), [])
            f.write_text(css + '.syn-root { display: none !important; }', encoding="utf-8")
            self.assertTrue(any("!important" in e for e in find_issues(src, registry)))

    def test_unbundled_css_urls_rejected_but_embedded_sources_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory)
            f = src / "tokens.css"
            registry = {"syntyr.core.css": ("tokens.css",)}
            for value in ('url("https://example.org/logo.svg")', 'url(/images/logo.svg)',
                          'url("../icons/logo.svg")', 'url(//example.org/logo.svg)'):
                with self.subTest(value=value):
                    f.write_text(f'.syn-root {{ background: {value}; }}', encoding="utf-8")
                    self.assertTrue(any("external CSS asset" in e for e in find_issues(src, registry)))
            f.write_text('/* @import "bad.css"; url(https://bad.test/img) */'
                         '.syn-root { filter: url("#contrast");'
                         'background: url(data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=); }', encoding="utf-8")
            self.assertEqual(find_issues(src, registry), [])

    def test_css_escape_asset_paths_and_fragments_are_decoded_before_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory)
            target = src / "tokens.css"
            registry = {"syntyr.core.css": ("tokens.css",)}
            invalid = (
                r"url(icons/my\ icon.svg)",
                r"url(icons/my\20 icon.svg)",
                r'url("icons/my\20 icon.svg")',
                r"url(\2f assets/icon.svg)",
                r"url(https\3a //example.test/icon.svg)",
                r'url(" #contrast")',
                r'url(" data:image/png;base64,ABC=")',
                r'url(\20 #contrast)',
            )
            for reference in invalid:
                with self.subTest(reference=reference):
                    target.write_text(f'.syn-root {{ background: {reference}; }}', encoding='utf-8')
                    issues = find_issues(src, registry)
                    self.assertTrue(any('external CSS asset' in issue for issue in issues), issues)
            valid = (
                r"url(\#contrast)",
                r'url("\23 contrast")',
                r"url(\64 ata:image/svg+xml;base64,PHN2Zz4=)",
            )
            for reference in valid:
                with self.subTest(reference=reference):
                    target.write_text(f'.syn-root {{ filter: {reference}; }}', encoding='utf-8')
                    self.assertEqual(find_issues(src, registry), [])

    def test_import_after_charset_on_same_line_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory)
            (src / "tokens.css").write_text(
                '@charset "UTF-8";@import "https://example.test/theme.css";', encoding='utf-8')
            issues = find_issues(src, {"syntyr.core.css": ("tokens.css",)})
            self.assertTrue(any('CSS import' in issue for issue in issues), issues)

    def test_css_escaped_import_and_url_function_names_cannot_bypass_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory)
            target = src / "tokens.css"
            registry = {"syntyr.core.css": ("tokens.css",)}
            for css in (r'@\69mport "theme.css";',
                        r'@im\70ort "theme.css";',
                        r'@charset "UTF-8";@\69mport url("theme.css");'):
                with self.subTest(css=css):
                    target.write_text(css, encoding="utf-8")
                    self.assertTrue(any('CSS import' in issue for issue in find_issues(src, registry)))
            for css in (r'.syn-root { background: u\72l(/icons/asset.svg); }',
                        r'.syn-root { background: \75rl(icons/asset.svg); }'):
                with self.subTest(css=css):
                    target.write_text(css, encoding="utf-8")
                    self.assertTrue(any('external CSS asset' in issue for issue in find_issues(src, registry)))
            target.write_text(r'.syn-root { filter: u\72l(\#contrast); }', encoding="utf-8")
            self.assertEqual(find_issues(src, registry), [])

    def test_important_declarations_outside_accessibility_base_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory)
            (src / "components").mkdir()
            (src / "base.css").write_text("@media (prefers-reduced-motion: reduce) { * { animation-duration: 0s !important; } }")
            (src / "components" / "card.css").write_text(".syn-card { color: red !important; }")
            bundles = {"syntyr.core.css": ("base.css", "components/card.css")}
            issues = find_issues(src, bundles)
            self.assertTrue(any("!important outside base.css" in issue for issue in issues), issues)
            (src / "components" / "card.css").write_text("/* !important is discouraged */ .syn-card { color: red; }")
            self.assertEqual(find_issues(src, bundles), [])



class VariableResolutionPolicyTests(unittest.TestCase):
    """CSS var() without a declared token or fallback is silent runtime breakage."""

    def test_undefined_variable_without_fallback_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "buttons.css").write_text(
                ".syn-button { color: var(--syn-missing-color); }"
            )
            issues = find_issues(source, {"buttons.css": ("buttons.css",)})
            self.assertTrue(any("--syn-missing-color" in issue for issue in issues), issues)

    def test_custom_variable_with_explicit_fallback_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "buttons.css").write_text(
                ".syn-button { color: var(--syn-override, var(--syn-inner, blue)); }"
            )
            self.assertEqual(find_issues(source, {"buttons.css": ("buttons.css",)}), [])

    def test_defined_token_used_by_another_module_is_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "tokens.css").write_text(":root { --syn-accent: blue; }")
            (source / "buttons.css").write_text(".syn-button { color: var(--syn-accent); }")
            self.assertEqual(find_issues(source, {"css": ("tokens.css", "buttons.css")}), [])

    def test_comment_only_variable_reference_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "buttons.css").write_text(
                "/* var(--syn-discontinued) */ .syn-button { color: var(--syn-override, blue); }"
            )
            self.assertEqual(find_issues(source, {"buttons.css": ("buttons.css",)}), [])


    def test_quoted_variable_references_do_not_trigger_false_positives(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "label.css").write_text(
                r'.syn-label { content: "escaped \"quote\" var(--syn-not-a-variable)"; }'
            )
            self.assertEqual(find_issues(source, {"css": ("label.css",)}), [])

    def test_quoted_fake_declarations_do_not_hide_undefined_variables(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "label.css").write_text(
                '.syn-label { content: "--syn-not-declared: teal"; color: var(--syn-not-declared); }'
            )
            issues = find_issues(source, {"css": ("label.css",)})
            self.assertTrue(any("unresolved CSS variable" in issue for issue in issues), issues)


    def test_uppercase_or_mixed_case_var_function_cannot_hide_missing_tokens(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            file = source / "buttons.css"
            for spelling in ("VAR", "Var", "vAr"):
                with self.subTest(spelling=spelling):
                    file.write_text(f".syn-button {{ color: {spelling}(--syn-missing); }}")
                    issues = find_issues(source, {"css": ("buttons.css",)})
                    self.assertTrue(any("--syn-missing" in issue for issue in issues), issues)

    def test_supports_feature_query_does_not_define_custom_property(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "buttons.css").write_text(
                "@supports (--syn-missing: blue) { .syn-button { color: var(--syn-missing); } }"
            )
            issues = find_issues(source, {"css": ("buttons.css",)})
            self.assertTrue(any("unresolved CSS variable" in issue for issue in issues), issues)

    def test_real_custom_property_after_semicolon_is_still_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "buttons.css").write_text(
                ".syn-button { color: red; --syn-local: blue; background: VAR(--syn-local); }"
            )
            self.assertEqual(find_issues(source, {"css": ("buttons.css",)}), [])


    def test_unquoted_escaped_quote_does_not_hide_missing_variable(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "buttons.css").write_text(
                ".syn-icon { background: url(icon" + chr(92) + '".svg); color: var(--syn-missing); }'
            )
            issues = find_issues(source, {"css": ("buttons.css",)})
            self.assertTrue(any("--syn-missing" in issue for issue in issues), issues)

    def test_custom_property_after_nested_rule_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "buttons.css").write_text(
                ".syn-root { &:hover { color: red; } --syn-local: blue; color: var(--syn-local); }"
            )
            self.assertEqual(find_issues(source, {"css": ("buttons.css",)}), [])


class ImportantExceptionPolicyTests(unittest.TestCase):
    def test_important_outside_reduced_motion_is_rejected_in_base(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "base.css").write_text(
                ".syn-root { color: red !important; }\n"
                "@media (prefers-reduced-motion: reduce) { .syn-root * { animation-duration: 0s !important; } }"
            )
            issues = find_issues(source, {"core": ("base.css",)})
            self.assertTrue(any("!important outside reduced-motion" in issue for issue in issues), issues)

    def test_unrelated_important_within_reduced_motion_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "base.css").write_text(
                "@media (prefers-reduced-motion: reduce) { .syn-root { color: red !important; } }"
            )
            issues = find_issues(source, {"core": ("base.css",)})
            self.assertTrue(any("!important" in issue for issue in issues), issues)

    def test_supported_reduced_motion_overrides_remain_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "base.css").write_text(
                "@media (prefers-reduced-motion: reduce) { .syn-root * {"
                "scroll-behavior: auto !important;"
                "transition-duration: 0s !important;"
                "animation-duration: 0s !important;" "} }"
            )
            self.assertEqual(find_issues(source, {"core": ("base.css",)}), [])

    def test_reduced_motion_exception_rejects_negated_media(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "base.css").write_text(
                '@media not all and (prefers-reduced-motion: reduce) {'
                ' .syn-root { animation-duration: 0s !important; } }'
            )
            issues = find_issues(source, {"core": ("base.css",)})
            self.assertTrue(any("outside reduced-motion" in issue for issue in issues), issues)

    def test_reduced_motion_exception_rejects_unrestricted_media_list(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "base.css").write_text(
                '@media screen, (prefers-reduced-motion: reduce) {'
                ' .syn-root { animation-duration: 0s !important; } }'
            )
            issues = find_issues(source, {"core": ("base.css",)})
            self.assertTrue(any("outside reduced-motion" in issue for issue in issues), issues)

    def test_reduced_motion_exception_accepts_nested_media_after_declaration(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            (source / "base.css").write_text(
                '.syn-root { color: red; @media (prefers-reduced-motion: reduce) {'
                ' animation-duration: 0s !important; } }'
            )
            self.assertEqual(find_issues(source, {"core": ("base.css",)}), [])

if __name__ == "__main__":
    unittest.main()
