"""One shared probe source for Python and TypeScript consumers."""
import json
from pathlib import Path
import unittest
from responsive_viewports import CANONICAL_VIEWPORTS

ROOT = Path(__file__).resolve().parents[1]


class SharedProbeContract(unittest.TestCase):
    def test_probe_has_versioned_geometry_and_exact_viewports(self):
        payload = json.loads((ROOT / "metadata/responsive-probe.v1.json").read_text())
        self.assertEqual(payload["schemaVersion"], 1)
        self.assertEqual(payload["viewports"], [
            {"id": name, "width": width, "height": height}
            for name, width, height in CANONICAL_VIEWPORTS
        ])
        self.assertIn("scrollableAncestor", payload["inspectLayout"])
        self.assertIn("label.htmlFor", payload["inspectTouchTargets"])

    def test_probe_is_exposed_on_public_site(self):
        from scripts.build_cloudflare_site import source_files
        files = source_files()
        self.assertEqual(files["metadata/responsive-probe.v1.json"],
                         (ROOT / "metadata/responsive-probe.v1.json").read_bytes())
