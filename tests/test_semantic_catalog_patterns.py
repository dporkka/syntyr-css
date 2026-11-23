"""Common semantic patterns must remain copyable, accessible and discoverable."""
from html import unescape
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs/catalog.html"

# Every addition is a native HTML composition, not a JavaScript widget.
SEMANTIC_PATTERNS = {
    "catalog-primary-nav-title": ("Primary navigation", "navigation", "<nav", "aria-current=\"page\""),
    "catalog-table-of-contents-title": ("On-page table of contents", "navigation", "<nav", "href=\"#catalog-toc-overview\""),
    "catalog-footer-nav-title": ("Footer link groups", "navigation", "<footer", "<nav"),
    "catalog-pagination-title": ("Pagination navigation", "navigation", "<nav", "aria-current=\"page\""),
    "catalog-contact-title": ("Contact details", "layout", "<address", "mailto:"),
    "catalog-aside-title": ("Section and complementary aside", "layout", "<section", "<aside"),
    "catalog-heading-group-title": ("Heading group", "typography", "<hgroup", "<h3"),
    "catalog-event-agenda-title": ("Event agenda", "data", "<time", "datetime="),
    "catalog-table-totals-title": ("Table with totals", "data", "<tfoot", "<caption"),
    "catalog-revisions-title": ("Revisions and abbreviations", "typography", "<ins", "<del"),
    "catalog-form-help-title": ("Form help and validation", "forms", "<form", "aria-describedby="),
}


class SemanticCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = CATALOG.read_text(encoding="utf-8")
        cls.cards = {}
        pattern = re.compile(
            r'<article class="catalog-card syn-panel"(?P<attrs>[^>]*)>'
            r'(?P<body>.*?)(?=\n        <article class="catalog-card syn-panel"|\n      </div>\n    </section>)',
            re.S,
        )
        for match in pattern.finditer(cls.page):
            label = re.search(r'aria-labelledby="([^"]+)"', match["attrs"])
            if label:
                cls.cards[label.group(1)] = match.groupdict()

    def test_common_semantic_patterns_have_live_copyable_examples(self):
        self.assertGreaterEqual(len(self.cards), 43)
        for identifier, (title, category, *required) in SEMANTIC_PATTERNS.items():
            with self.subTest(identifier=identifier):
                self.assertIn(identifier, self.cards)
                card = self.cards[identifier]
                self.assertIn(f'data-catalog-category="{category}"', card["attrs"])
                self.assertIn(f'<h2 class="syn-heading" id="{identifier}">{title}</h2>', card["body"])
                preview = re.search(
                    r'<div class="catalog-preview">\n(.*?)\n          </div>\n'
                    r'          <details class="catalog-code-details">.*?'
                    r'<pre class="catalog-source"><code>(.*?)</code></pre>',
                    card["body"], re.S
                )
                self.assertIsNotNone(preview)
                self.assertEqual(preview.group(1).strip(), unescape(preview.group(2)).strip())
                for token in required:
                    self.assertIn(token, preview.group(1))
                self.assertIn(f'href="#{identifier}"', self.page)
                self.assertIn(f'href="#{identifier}-preview"', card["body"])
                self.assertIn(f'href="playground.html#component={identifier}"', card["body"])

    def test_pagination_targets_use_the_page_link_composition(self):
        """Bare text links render ~10x25px and fail WCAG 2.2 SC 2.5.8.

        Every pagination target must carry the documented .syn-page-link class
        that keeps the 44px control box, matching the other shipped examples.
        """
        body = self.cards["catalog-pagination-title"]["body"]
        preview = re.search(
            r'<div class="catalog-preview">\n(.*?)\n          </div>\n'
            r'          <details class="catalog-code-details">',
            body, re.S,
        )
        self.assertIsNotNone(preview)
        markup = preview.group(1)
        self.assertIn('<nav class="syn-pagination"', markup)
        targets = re.findall(r'<(?:a|span)\b[^>]*>', markup)
        self.assertGreaterEqual(len(targets), 5)
        for target in targets:
            with self.subTest(target=target):
                self.assertIn('class="syn-page-link"', target)

    def test_semantic_navigation_and_form_have_accessible_names(self):
        for identifier in ("catalog-primary-nav-title", "catalog-table-of-contents-title",
                           "catalog-footer-nav-title", "catalog-pagination-title"):
            with self.subTest(identifier=identifier):
                self.assertRegex(self.cards[identifier]["body"], r'<nav[^>]*aria-label="[^"]+"')
        form = self.cards["catalog-form-help-title"]["body"]
        self.assertIn('id="catalog-validation-help"', form)
        self.assertIn('aria-describedby="catalog-validation-help"', form)
        self.assertIn("required", form)

    def test_catalog_static_count_and_sidebar_match_cards(self):
        count = len(self.cards)
        self.assertIn(f'{count} examples available.', self.page)
        self.assertIn(f'Components <span class="syn-badge">{count}</span>', self.page)
        self.assertEqual(self.page.count('class="catalog-index-link"'), count)


if __name__ == "__main__":
    unittest.main()
