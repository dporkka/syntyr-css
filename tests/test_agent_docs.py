"""Agent-facing docs must be reproducible, version-correct, and safe to publish."""
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


class AgentDocsTests(unittest.TestCase):
    def test_canonical_docs_and_agent_skill(self):
        for path in ("AGENTS.md", "llms.txt", "llms-full.txt",
                     "docs/ai-quickstart.md", "docs/agent-integration.md",
                     "agents/syntyr/SKILL.md", "metadata/components.json"):
            self.assertTrue((ROOT / path).is_file(), path)
        self.assertIn("0.3.0-alpha.4", (ROOT / "docs/ai-quickstart.md").read_text())
        self.assertIn("0.3.0-alpha.5", (ROOT / "docs/ai-quickstart.md").read_text())

    def test_generated_llm_reference_is_current(self):
        command = [sys.executable, str(ROOT / "scripts/build_agent_docs.py"), "--check"]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_component_manifest_classes_are_real(self):
        manifest = json.loads((ROOT / "metadata/components.json").read_text())
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["source_version"], (ROOT / "VERSION").read_text().strip())
        for component in manifest["components"]:
            sheet = ROOT / "dist" / component["module"]
            self.assertTrue(sheet.is_file(), component["name"])
            css = sheet.read_text()
            for name in component["classes"]:
                import re
                selector = r"\." + re.escape(name) + r"(?![a-zA-Z0-9_-])"
                self.assertRegex(css, selector, (component["name"], name))

    def test_cloudflare_and_release_allowlists_include_public_docs(self):
        from scripts.build_cloudflare_site import source_files
        from scripts.package_release import FILES
        names = ("llms.txt", "llms-full.txt", "docs/ai-quickstart.md",
                 "docs/agent-integration.md", "metadata/components.json",
                 "agents/syntyr/SKILL.md")
        published = source_files()
        for name in names:
            self.assertIn(name, published)
            self.assertIn(name, FILES)
        self.assertNotIn("AGENTS.md", published)
        self.assertNotIn("tests/test_agent_docs.py", published)

    def test_llms_index_points_to_existing_public_docs(self):
        from scripts.build_cloudflare_site import source_files
        published = source_files()
        index = (ROOT / "llms.txt").read_text()
        self.assertIn("https://syntyr-css.pages.dev/docs/ai-quickstart.md", index)
        self.assertIn("https://syntyr-css.pages.dev/llms-full.txt", index)
        self.assertIn("0.3.0-alpha.4", index)
        self.assertIn("alpha.5 candidate validation and remaining manual gates", index)
        for name in ("llms-full.txt", "docs/components.md", "docs/distribution.md",
                     "docs/api-stability.md", "docs/ai-quickstart.md"):
            self.assertIn(name, published)

    def test_pinned_quickstart_classes_exist_in_alpha4_release(self):
        import re
        example = (ROOT / "docs/ai-quickstart.md").read_text()
        sheets = list((ROOT / "site-releases/0.3.0-alpha.4").glob("*.css"))
        self.assertTrue(sheets)
        css = "\n".join(p.read_text() for p in sheets)
        for val in re.findall(r'class="([^"]+)"', example):
            for cls in val.split():
                if cls.startswith("syn-"):
                    self.assertIn("." + cls, css, cls)

    def test_public_agent_markdown_links_resolve(self):
        from scripts.build_cloudflare_site import source_files
        from urllib.parse import urlsplit, unquote
        import re
        import posixpath

        published = source_files()
        for page in ("docs/ai-quickstart.md", "docs/agent-integration.md",
                     "agents/syntyr/SKILL.md"):
            markdown = (ROOT / page).read_text()
            for target in re.findall(r"\]\(([^)]+)\)", markdown):
                parsed = urlsplit(target)
                if parsed.scheme or target.startswith("#"):
                    continue
                relative = posixpath.normpath(posixpath.join(posixpath.dirname(page),
                                                            unquote(parsed.path)))
                self.assertIn(relative, published, (page, target))

    def test_generated_text_does_not_leak_internal_docs(self):
        full = (ROOT / "llms-full.txt").read_text()
        self.assertNotIn("business/strategy.md", full)
        self.assertNotIn("business/premium-license-draft.md", full)


if __name__ == "__main__":
    unittest.main()
