"""Optional, keyboard-accessible resizable workspace; no core runtime coupling."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


class ResizableWorkspaceContract(unittest.TestCase):
    def test_optional_styles_do_not_enter_core(self):
        css = read("src/recipes.css")
        self.assertIn("&.syn-resizable-workspace", css)
        self.assertIn("container-type: inline-size;", css)
        self.assertIn("--syn-workspace-leading", css)
        self.assertIn(":focus-visible", css)
        self.assertIn("forced-colors: active", css)
        self.assertNotIn("syn-resizable-workspace", read("dist/syntyr.core.css"))

    def test_forced_colors_grip_has_explicit_system_background(self):
        css = read("src/recipes.css")
        self.assertIn(
            "&.syn-resizable-workspace .syn-resizable-workspace__separator::before { background: CanvasText; }",
            css,
        )

    def test_stack_spacing_across_hidden_separator(self):
        css = read("src/recipes.css")
        self.assertIn(
            "&.syn-resizable-workspace .syn-resizable-workspace__separator + .syn-resizable-workspace__pane",
            css,
        )

    def test_active_pointer_is_not_replaced_by_second_touch(self):
        js = read("examples/resizable-workspace.mjs")
        self.assertIn("if (pointer !== null || event.button !== 0) return;", js)

    def test_accessible_separator_and_fallback(self):
        html = read("examples/resizable-workspace.html")
        for token in ("role=\"separator\"", "aria-orientation=\"vertical\"",
                      "aria-valuenow=\"35\"", "aria-valuemin=\"20\"",
                      "aria-valuemax=\"70\"", "aria-controls=",
                      "tabindex=\"-1\"", "syn-resizable-workspace__panes"):
            self.assertIn(token, html)
        self.assertIn('type="module"', html)
        self.assertNotIn("role=\"tree\"", html)

    def test_optional_logic_supports_pointer_keyboard_and_rtl(self):
        js = read("examples/resizable-workspace.mjs")
        for token in ("pointerdown", "pointermove", "pointerup", "pointercancel",
                      "setPointerCapture", "ArrowLeft", "ArrowRight",
                      "Home", "End", "aria-valuenow", "direction"):
            self.assertIn(token, js)
        self.assertNotIn("localStorage", js)

    def test_packaged_module_demo_documents_local_http_server(self):
        docs = read("docs/recipes.md")
        readme = read("README.md")
        for text in (docs, readme):
            self.assertIn("python3 -m http.server 8000 --bind 127.0.0.1", text)
            self.assertIn("examples/resizable-workspace.html", text)
            self.assertIn("file://", text)

    def test_recipe_docs_and_release_package_include_demo(self):
        docs = read("docs/recipes.md")
        self.assertIn("Resizable workspace", docs)
        self.assertIn("application-owned", docs)
        from scripts.package_release import FILES
        self.assertIn("examples/resizable-workspace.html", FILES)
        self.assertIn("examples/resizable-workspace.mjs", FILES)


if __name__ == "__main__":
    unittest.main()
