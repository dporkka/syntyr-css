"""Every public browser-matrix page also receives automated a11y coverage."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def pages_in(path: str) -> set[str]:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "PAGES"
            for target in node.targets
        ):
            return set(ast.literal_eval(node.value))
    raise AssertionError(f"{path} is missing the static PAGES list")


class AuditPageCoverageTests(unittest.TestCase):
    def test_document_starter_is_in_regular_browser_reflow_and_axe_gates(self):
        for script in ("tests/browser_matrix.py", "tests/reflow_test.py", "tests/axe_audit.py"):
            with self.subTest(script=script):
                self.assertIn("examples/document-starter.html", pages_in(script))
        self.assertIn("docs/static-site-generators.html", pages_in("tests/axe_audit.py"))

    def test_public_browser_matrix_pages_are_all_axe_audited(self):
        browser_pages = pages_in("tests/browser_matrix.py")
        axe_pages = pages_in("tests/axe_audit.py")
        self.assertTrue(browser_pages, "browser coverage must not be empty")
        self.assertFalse(browser_pages - axe_pages,
                         f"Pages missing axe review: {sorted(browser_pages - axe_pages)}")


if __name__ == "__main__":
    unittest.main()
