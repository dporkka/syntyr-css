"""SvelteKit reference must use existing Syntyr primitives, not change the CSS runtime."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "examples" / "sveltekit"


class SveltekitReferenceContracts(unittest.TestCase):
    def test_isolated_app_uses_sveltekit_3_and_stable_css_modules(self):
        package = json.loads((APP / "package.json").read_text())
        self.assertIn("@sveltejs/kit", package["devDependencies"])
        self.assertTrue(package["devDependencies"]["@sveltejs/kit"].startswith("^3."))
        self.assertIn("svelte", package["devDependencies"])
        self.assertIn("vite", package["devDependencies"])
        layout = (APP / "src/routes/+layout.svelte").read_text()
        self.assertIn("syntyr.core.css", layout)
        self.assertIn("syntyr.recipes.css", layout)
        self.assertIn("syn-root", layout)
        self.assertIn("syn-app-shell", layout)
        self.assertIn("{@render children()}", layout)
        self.assertNotIn("<style", layout)

    def test_form_posts_without_javascript_and_enhances_without_replacing_browser_semantics(self):
        page = (APP / "src/routes/settings/+page.svelte").read_text()
        for fragment in ('method="POST"', 'action="/settings"', "use:enhance",
                         "syn-field", "syn-input", "syn-error-summary",
                         "aria-describedby", "aria-invalid", "syn-operation-feedback",
                         "aria-busy", "disabled={submitting}", "type=\"submit\""):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, page)
        self.assertNotIn("{@html", page)
        self.assertNotIn("fetch(", page)
        self.assertIn("readonly={submitting}", page)
        # A pending enhanced POST must never redirect the user back to
        # Settings after they navigate to another route.
        self.assertIn("onDestroy", page)
        self.assertIn("pageActive", page)
        self.assertIn("if (!pageActive) return;", page)
        # Native maxlength uses UTF-16 code units; the server counts Unicode
        # code points so the native limit would reject otherwise valid values.
        self.assertNotIn('minlength="2"', page)
        self.assertNotIn('maxlength="80"', page)
        actions = (APP / "src/routes/settings/+page.server.js").read_text()
        self.assertIn("request.formData()", actions)
        self.assertIn("fail(400", actions)
        self.assertNotIn("localStorage", actions)

    def test_nested_layout_and_named_composition_snippets_use_existing_classes(self):
        layout = (APP / "src/routes/settings/+layout.svelte").read_text()
        self.assertIn("syn-detail-layout", layout)
        self.assertIn("syn-detail-main", layout)
        self.assertIn("syn-detail-aside", layout)
        panel = (APP / "src/lib/AppPanel.svelte").read_text()
        self.assertIn("Snippet", panel)
        self.assertIn("{@render children()}", panel)
        self.assertIn("{@render actions()}", panel)
        self.assertIn("{@render footer()}", panel)
        self.assertIn("syn-panel", panel)

    def test_documentation_distinguishes_sveltekit_host_from_syntyr_core(self):
        readme = (APP / "README.md").read_text()
        guide = (ROOT / "docs/framework-integrations.md").read_text()
        self.assertIn("npm run test", readme)
        self.assertIn("npm run build", readme)
        self.assertIn("examples/sveltekit", guide)
        self.assertIn("server-side", readme.lower())
        self.assertIn("no JavaScript", readme)
        self.assertIn("CSRF", readme)
        self.assertIn("Syntyr", guide)
        self.assertNotIn("SvelteKit", (ROOT / "src/components/form-composition.css").read_text())


if __name__ == "__main__":
    unittest.main()
