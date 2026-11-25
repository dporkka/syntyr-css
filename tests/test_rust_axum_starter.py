"""Contract tests for the runnable, copy-owned Rust Axum/Askama example."""
from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
STARTER = ROOT / "examples/rust-axum"


class RustAxumStarterTests(unittest.TestCase):
    def test_standalone_cargo_manifest_has_no_frontend_build_tools(self):
        manifest = tomllib.loads((STARTER / "Cargo.toml").read_text())
        self.assertEqual(manifest["package"]["edition"], "2021")
        self.assertIn("axum", manifest["dependencies"])
        self.assertIn("askama", manifest["dependencies"])
        self.assertIn("tokio", manifest["dependencies"])
        self.assertNotIn("build", manifest["package"])

    def test_server_embeds_versioned_local_css_from_the_repository(self):
        source = (STARTER / "src/main.rs").read_text()
        self.assertIn('include_str!("../../../dist/syntyr.core.css")', source)
        self.assertIn('"/assets/syntyr.core.css"', source)
        self.assertIn("text/css", source)
        self.assertNotIn("https://", source)

    def test_template_has_native_accessible_search_and_results(self):
        template = (STARTER / "templates/dashboard.html").read_text()
        for part in ('class="syn-root', 'data-syn-theme="studio"',
                     'method="get"', 'name="q"', 'aria-invalid=',
                     'aria-describedby=', 'class="syn-input"', 'class="syn-button',
                     'class="syn-table"', '<caption>', '<th scope="col"',
                     'role="alert"', 'id="search-error"'):
            with self.subTest(part=part):
                self.assertIn(part, template)
        self.assertNotIn("<script", template.lower())
        self.assertNotIn("cdn.", template.lower())

    def test_public_guide_and_starter_readme_are_published_together(self):
        from scripts.build_cloudflare_site import source_files
        files = source_files()
        self.assertTrue("docs/rust-saas-integration.md" in files, "missing published Rust guide source")
        self.assertTrue("docs/rust-saas-integration.html" in files, "missing published Rust guide HTML")
        self.assertTrue("examples/rust-axum/README.md" in files, "missing published starter README")
        self.assertIn("rust-axum", (ROOT / "llms.txt").read_text())

    def test_docs_state_runtime_and_security_boundaries(self):
        readme = (STARTER / "README.md").read_text()
        self.assertIn("cargo run", readme)
        self.assertIn("cargo test", readme)
        self.assertIn("read-only", readme.lower())
        self.assertIn("HTML escaping", readme)
        self.assertIn("Rust", (ROOT / "docs/rust-saas-integration.md").read_text())


if __name__ == "__main__":
    unittest.main()
