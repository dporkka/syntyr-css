"""Machine-friendly docs are small, release-safe and explicitly published."""
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts.build_cloudflare_site import source_files

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://syntyr-css.pages.dev"


class LlmDiscoveryTests(unittest.TestCase):
    def test_small_primary_index_links_topic_indices_and_pinned_release(self):
        index = (ROOT / "llms.txt").read_text(encoding="utf-8")
        self.assertLess(len(index.encode("utf-8")), 16000)
        for path in ("llms-components.txt", "llms-frameworks.txt",
                     "v/0.3.0-alpha.4/llms.txt"):
            self.assertIn(f"{ORIGIN}/{path}", index)

    def test_curated_topic_indices_are_available_without_internal_material(self):
        from scripts.package_release import FILES
        published = source_files()
        for filename, required in (
            ("llms-components.txt", ("docs/components.md", "docs/recipes.md",
                                     "metadata/syntyr-contract.json")),
            ("llms-frameworks.txt", ("docs/framework-integrations.md",
                                     "docs/htmx-components.md", "docs/site-builders.md")),
        ):
            self.assertIn(filename, published)
            self.assertIn(filename, FILES)
            body = published[filename].decode()
            for target in required:
                self.assertIn(target, body)
            self.assertNotIn("business/", body)
            self.assertNotIn("private/", body)
            self.assertLess(len(body.encode()), 12000)
        headers = published["_headers"].decode()
        for filename in ("llms.txt", "llms-full.txt", "llms-components.txt",
                         "llms-frameworks.txt"):
            self.assertIn(f"/{filename}\n  X-Robots-Tag: noindex", headers)

    def test_pinned_release_index_only_claims_published_assets(self):
        published = source_files()
        pinned = "v/0.3.0-alpha.4/llms.txt"
        self.assertIn(pinned, published)
        content = published[pinned].decode()
        self.assertIn("/v/0.3.0-alpha.4/syntyr.core.css", content)
        self.assertIn("studio", content)
        self.assertIn("grid", content)
        self.assertIn("noir", content)
        self.assertNotIn("alpha.5", content)
        self.assertNotIn("syntyr.semantic-bundle.css", content)
        self.assertIn("/v/*\n", published["_headers"].decode())

    def test_modified_pinned_release_index_is_rejected(self):
        frozen = ROOT / "site-releases/0.3.0-alpha.4/llms.txt"
        read_bytes = Path.read_bytes

        def changed_read(path):
            data = read_bytes(path)
            return data + b"unexpected edit" if path == frozen else data

        with patch.object(Path, "read_bytes", changed_read):
            with self.assertRaisesRegex(ValueError, r"Modified immutable release documentation: .*llms\.txt"):
                source_files()

    def test_agent_discovery_metadata_on_docs_html(self):
        published = source_files()
        html = published["docs/components.html"].decode()
        self.assertIn(f'<link rel="describedby" href="{ORIGIN}/llms.txt"', html)
        self.assertIn('rel="alternate" type="text/markdown"', html)
        self.assertNotIn('rel="describedby"', published["index.html"].decode())


if __name__ == "__main__":
    unittest.main()
