"""Regression contract for the CSS-first component catalog navigation."""
import html
import re
import unittest
from pathlib import Path


PAGE = Path(__file__).resolve().parents[1] / "docs" / "catalog.html"


class CatalogNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PAGE.read_text(encoding="utf-8")
        cls.cards = [
            (ident, html.unescape(label))
            for ident, label in re.findall(
                r'<article class="catalog-card[^"]*[^>]*aria-labelledby="([^"]+)"[^>]*>\s*'
                r'<div class="catalog-card-top">\s*<h2[^>]*>([^<]+)</h2>',
                cls.source,
            )
        ]

    def test_alphabetized_sidebar_links_to_every_component(self):
        index = re.search(
            r'<nav id="catalog-index"[^>]*>(.*?)</nav>',
            self.source,
            re.DOTALL,
        )
        self.assertIsNotNone(index, "A semantic catalog-index navigation landmark is required")
        links = [
            (target, html.unescape(label))
            for target, label in re.findall(
                r'<a class="catalog-index-link" href="#([^"]+)">([^<]+)</a>',
                index.group(1),
            )
        ]
        self.assertGreaterEqual(len(self.cards), 32)
        self.assertEqual(len(links), len(self.cards))
        self.assertEqual(dict(links), dict(self.cards))
        self.assertEqual(
            [label.casefold() for _, label in links],
            sorted(label.casefold() for _, label in links),
        )
        self.assertEqual(len({target for target, _ in links}), len(links))

    def test_live_view_and_other_actions_share_inline_group(self):
        groups = re.findall(
            r'<div class="catalog-actions">\s*'
            r'<a class="syn-button catalog-live" href="#([^"]+)">Live View</a>\s*'
            r'<button[^>]*data-catalog-copy[^>]*>Copy HTML</button>\s*'
            r'<a class="syn-button catalog-edit" href="([^"]+)">Edit in playground</a>\s*'
            r'</div>',
            self.source,
            re.DOTALL,
        )
        self.assertEqual(len(groups), len(self.cards))
        for (preview, target), (card_id, _) in zip(groups, self.cards):
            self.assertEqual(preview, f"{card_id}-preview")
            self.assertIn(f'id="{preview}"', self.source)
            self.assertIn(f"#component={card_id}", target)


if __name__ == "__main__":
    unittest.main()
