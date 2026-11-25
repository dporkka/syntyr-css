"""Native shadcn/daisyUI-inspired patterns stay accessible without a JS runtime."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.stack = []
        self.nested_interactive = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"a", "button"} and any(parent in {"a", "button"} for parent in self.stack):
            self.nested_interactive.append(tag)
        self.tags.append((tag, attrs))
        if tag not in {"input", "img", "br", "hr", "meta", "link"}:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.stack:
            self.stack = self.stack[: len(self.stack) - 1 - self.stack[::-1].index(tag)]


class NativeChoiceFilterPatterns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example = (ROOT / "examples/native-choice-filter-list.html").read_text(encoding="utf-8")
        cls.parsed = Markup()
        cls.parsed.feed(cls.example)

    def test_choice_cards_use_visible_native_inputs_and_checked_focus_states(self):
        css = (ROOT / "src/components/patterns.css").read_text(encoding="utf-8")
        self.assertIn("&.syn-choice-card", css)
        self.assertIn("&.syn-choice-card:has(> .syn-input:checked)", css)
        self.assertIn("&.syn-choice-card:has(> .syn-input:focus-visible)", css)
        self.assertIn("&.syn-choice-card:has(> .syn-input:disabled)", css)
        self.assertIn("border-inline-start", css)  # logical properties work in RTL
        radios = [a for tag, a in self.parsed.tags if tag == "input" and a.get("name") == "plan"]
        self.assertGreaterEqual(len(radios), 2)
        self.assertTrue(all(a.get("type") == "radio" for a in radios))
        self.assertTrue(any(tag == "fieldset" for tag, _ in self.parsed.tags))
        self.assertTrue(any(tag == "legend" for tag, _ in self.parsed.tags))

    def test_validation_has_native_and_server_invalid_states(self):
        css = (ROOT / "src/components/form-composition.css").read_text(encoding="utf-8")
        self.assertIn(':user-invalid', css)
        self.assertIn('[aria-invalid="true"]', css)
        self.assertIn("&.syn-field[data-syn-state=\"error\"] > .syn-label", css)
        self.assertIn("&.syn-field[data-syn-state=\"error\"]", css)
        inputs = [a for tag, a in self.parsed.tags if tag == "input"]
        described = [a for a in inputs if "aria-describedby" in a]
        self.assertTrue(described)
        ids = {a["id"] for _, a in self.parsed.tags if a.get("id")}
        for field in described:
            for target in field["aria-describedby"].split():
                self.assertIn(target, ids)
        self.assertTrue(any(a.get("aria-invalid") == "true" for a in inputs))

    def test_rich_list_rows_support_media_content_actions_without_nested_links(self):
        css = (ROOT / "src/components/patterns.css").read_text(encoding="utf-8")
        for selector in ("&.syn-list-row__media", "&.syn-list-row__body", "&.syn-list-row__actions"):
            self.assertIn(selector, css)
        self.assertFalse(self.parsed.nested_interactive)
        self.assertIn('class="syn-list-row__actions"', self.example)
        self.assertIn('class="syn-list-row__body"', self.example)

    def test_native_filter_chips_have_true_radio_state_and_get_submission(self):
        css = (ROOT / "src/components/patterns.css").read_text(encoding="utf-8")
        self.assertIn("&.syn-filter-choices", css)
        self.assertIn(":has(> input:checked)", css)
        self.assertIn(":has(> input:focus-visible)", css)
        self.assertIn("@media (forced-colors: active)", css)
        self.assertIn('method="get"', self.example)
        group = [a for tag, a in self.parsed.tags if tag == "input" and a.get("name") == "status"]
        self.assertGreaterEqual(len(group), 3)
        self.assertTrue(all(a.get("type") == "radio" for a in group))
        self.assertEqual(sum("checked" in a for a in group), 1)
        self.assertNotIn("<script", self.example.lower())
        self.assertNotIn('role="radio"', self.example)
        self.assertNotIn('aria-checked=', self.example)

    def test_release_distributions_and_docs_include_patterns(self):
        core = (ROOT / "dist/syntyr.core.css").read_text(encoding="utf-8")
        atomic = (ROOT / "dist/components/patterns.css").read_text(encoding="utf-8")
        docs = (ROOT / "docs/components.md").read_text(encoding="utf-8")
        for token in ("syn-choice-card", "syn-filter-choices", "syn-list-row__actions"):
            self.assertIn(token, core)
            self.assertIn(token, atomic)
            self.assertIn(token, docs)
        self.assertIn("aria-describedby", docs)
        self.assertIn("without JavaScript", docs)


if __name__ == "__main__":
    unittest.main()
