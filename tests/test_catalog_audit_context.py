"""The catalog's dynamic release selection is part of the audit's evidence."""

import unittest
from unittest.mock import Mock

from tests.catalog_audit_context import (
    CATALOG_PAGE, CATALOG_STYLESHEETS, catalog_context_from_report, select_catalog_context,
)


class CatalogAuditContextTests(unittest.TestCase):
    def test_both_modes_wait_for_selected_loaded_css_and_matching_cards(self):
        for mode, stylesheet in CATALOG_STYLESHEETS.items():
            with self.subTest(mode=mode):
                page = Mock()
                self.assertEqual(select_catalog_context(page, mode),
                                 {"mode": mode, "stylesheet": stylesheet})
                page.locator.assert_called_once_with("#catalog-release-filter")
                page.locator.return_value.select_option.assert_called_once_with(mode)
                wait = page.wait_for_function.call_args
                self.assertEqual(wait.kwargs["arg"], {"mode": mode, "stylesheet": stylesheet})
                self.assertIn("link.sheet?.href", wait.args[0])
                self.assertIn("card.hidden", wait.args[0])

    def test_unloaded_or_wrong_stylesheet_never_gets_a_context(self):
        page = Mock()
        page.wait_for_function.side_effect = RuntimeError("stylesheet failed to load")
        with self.assertRaisesRegex(RuntimeError, "stylesheet failed"):
            select_catalog_context(page, "source-alpha5")

    def test_unknown_mode_rejected_before_browser_interaction(self):
        page = Mock()
        with self.assertRaisesRegex(ValueError, "Unknown"):
            select_catalog_context(page, "latest")
        page.locator.assert_not_called()

    def test_report_round_trip_for_both_release_modes(self):
        for mode, stylesheet in CATALOG_STYLESHEETS.items():
            context = {"mode": mode, "stylesheet": stylesheet}
            self.assertEqual(catalog_context_from_report(
                {"page": CATALOG_PAGE, "catalog_context": context}), context)
        self.assertIsNone(catalog_context_from_report({"page": "docs/blocks.html"}))

    def test_rejects_legacy_catalog_report_and_wrong_stylesheet(self):
        for context in (None, {}, {"mode": "source-alpha5", "stylesheet": "other.css"},
                        {"mode": "latest", "stylesheet": "../dist/syntyr.all.css"},
                        {"mode": [], "stylesheet": "../dist/syntyr.all.css"}):
            with self.subTest(context=context), self.assertRaisesRegex(ValueError, "rerun"):
                catalog_context_from_report({"page": CATALOG_PAGE, "catalog_context": context})


if __name__ == "__main__":
    unittest.main()
