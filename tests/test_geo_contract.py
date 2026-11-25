"""Opt-in, renderer-neutral geospatial presentation contract."""
from html.parser import HTMLParser
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build import distributions  # noqa: E402
from scripts.build_cloudflare_site import source_files  # noqa: E402


class GeoHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.nodes = []

    def handle_starttag(self, tag, attrs):
        self.nodes.append((tag, dict(attrs)))


class GeoContract(unittest.TestCase):
    def test_geo_is_opt_in_and_available_in_all_distributions(self):
        m = distributions()
        self.assertEqual(m["syntyr.geo.css"], ("geo.css",))
        self.assertIn("geo.css", m["syntyr.all.css"])
        for bundle in ("syntyr.core.css", "syntyr.css", "syntyr.recipes.css", "syntyr.viz.css"):
            self.assertNotIn("geo.css", m[bundle])
        css = (ROOT / "src/geo.css").read_text()
        self.assertEqual((ROOT / "dist/syntyr.geo.css").read_text(), css.strip() + "\n")
        self.assertIn("dist/syntyr.geo.css", source_files())
        pkg = json.loads((ROOT / "package.json").read_text())
        self.assertEqual(pkg["exports"]["./geo.css"], "./dist/syntyr.geo.css")

    def test_geo_surface_tokens_and_core_primitives(self):
        css = (ROOT / "src/geo.css").read_text()
        self.assertIn("@layer syn.viz", css)
        self.assertIn(".syn-root .syn-geo-shell", css)
        self.assertNotIn("[data-syn-theme]", css, "Geo styling should inherit theme tokens without a component theme fork")
        for key in ("--syn-geo-land", "--syn-geo-water", "--syn-geo-road",
                    "--syn-geo-parcel", "--syn-geo-point",
                    "--syn-geo-route", "--syn-geo-zone"):
            self.assertIn(key + ":", css)
        for selector in (".syn-geo-shell", ".syn-geo-workspace", ".syn-geo-sidebar",
                         ".syn-geo-viewport", ".syn-geo-map", ".syn-geo-overlay",
                         ".syn-geo-controls", ".syn-geo-control", ".syn-geo-marker",
                         ".syn-geo-cluster", ".syn-geo-legend", ".syn-geo-swatch",
                         ".syn-geo-scale", ".syn-geo-attribution", ".syn-geo-callout",
                         ".syn-geo-layer-list", ".syn-geo-data-list"):
            with self.subTest(selector=selector):
                self.assertIn(selector, css)
        self.assertIn("[data-syn-selected=\"true\"]", css)
        self.assertIn("pointer-events: none", css)
        self.assertIn("pointer-events: auto", css)
        self.assertIn(":focus-visible", css)
        self.assertIn("margin: 0; /* Reset UA figure margins", css)
        self.assertIn("@container syn-geo", css)
        self.assertIn("forced-colors: active", css)
        self.assertIn("prefers-reduced-motion: reduce", css)
        for forbidden in ("@import", "url(", "!important", "@keyframes", "animation:"):
            self.assertNotIn(forbidden, css)
        self.assertNotIn(".maplibregl-", css)
        self.assertNotIn(".leaflet-", css)

    def test_static_marker_coordinates_remain_physical_in_rtl(self):
        css = (ROOT / "src/geo.css").read_text()
        rule = css.split(".syn-root .syn-geo-marker-layer > .syn-geo-marker {", 1)[1].split("}", 1)[0]
        self.assertIn("left: var(--syn-geo-x, 50%)", rule)
        self.assertIn("top: var(--syn-geo-y, 50%)", rule)
        self.assertIn("transform: translate(-50%, -50%)", rule)
        self.assertNotIn("inset-inline-start:", rule)
        self.assertNotIn("inset-block-start:", rule)

    def test_selected_cluster_has_visible_ring_even_when_marker_glyph_hidden(self):
        css = (ROOT / "src/geo.css").read_text()
        self.assertIn(
            '.syn-root .syn-geo-marker[data-syn-selected="true"] .syn-geo-cluster',
            css,
        )
        self.assertIn(
            '.syn-root .syn-geo-marker[aria-current="location"] .syn-geo-cluster',
            css,
        )
        normal = css.split("/* Selected clusters need their own visible ring")[1].split("/* Surface treatment")[0]
        self.assertIn("box-shadow: 0 0 0 3px var(--syn-surface)", normal)
        forced = css.split("@media (forced-colors: active)")[1]
        self.assertIn('.syn-root .syn-geo-marker[data-syn-selected="true"] .syn-geo-cluster', forced)
        self.assertIn("outline: 3px solid Highlight;", forced)
        self.assertIn("outline-offset: 4px;", forced)

    def test_static_demo_does_not_fake_live_gis_features(self):
        html = (ROOT / "examples/geo.html").read_text()
        parsed = GeoHTML()
        parsed.feed(html)
        self.assertIn('syntyr.geo.css', html)
        self.assertNotIn('aria-current="location"', html, "Illustrative schematic must not claim a current geographic location")
        self.assertIn('syn-geo-workspace', html)
        self.assertIn('Not to scale', html)
        self.assertIn('Schematic', html)
        self.assertNotIn("<script", html.lower())
        self.assertNotIn('https://', html)
        self.assertNotIn('http://', html)
        self.assertTrue(any(tag == "main" for tag, _ in parsed.nodes))
        self.assertTrue(any(tag == "h1" for tag, _ in parsed.nodes))
        self.assertTrue(any(tag == "figcaption" for tag, _ in parsed.nodes))
        self.assertTrue(any(tag == "table" for tag, _ in parsed.nodes))
        self.assertTrue(any(tag == "caption" for tag, _ in parsed.nodes))
        self.assertTrue(any(tag == "svg" and attrs.get("aria-hidden") == "true"
                            for tag, attrs in parsed.nodes))
        markers = [attrs for tag, attrs in parsed.nodes
                   if tag == "a" and "syn-geo-marker" in attrs.get("class", "").split()]
        self.assertGreaterEqual(len(markers), 3)
        ids = {attrs["id"] for _, attrs in parsed.nodes if attrs.get("id")}
        for marker in markers:
            self.assertTrue(marker.get("aria-label"), marker)
            self.assertIn(marker["href"].lstrip("#"), ids)
        for tag, attrs in parsed.nodes:
            if tag == "button" and "syn-geo-control" in attrs.get("class", "").split():
                self.assertIn("disabled", attrs, "Static demo must not imply operational map controls")
        self.assertTrue(any(tag == "a" and attrs.get("href") == "#assets"
                            for tag, attrs in parsed.nodes))

    def test_agent_registry_and_editor_metadata_offer_geo_opt_in(self):
        manifest = json.loads((ROOT / "metadata/components.json").read_text())
        geo = [item for item in manifest["components"] if item["module"] == "syntyr.geo.css"]
        self.assertTrue(geo, "Geo API must be discoverable for coding agents")
        self.assertIn("syn-geo-marker", geo[0]["classes"])
        registry = json.loads((ROOT / "registry/r/geo.json").read_text())
        self.assertEqual(registry["name"], "geo")
        self.assertEqual(registry["files"][0]["target"], "~/syntyr/css/syntyr.geo.css")
        self.assertIn("syn-geo-shell", (ROOT / "metadata/syntyr-api.json").read_text())
        self.assertIn("--syn-geo-point", (ROOT / "metadata/syntyr.css-custom-data.json").read_text())
        self.assertIn("docs/geo.md", (ROOT / "llms.txt").read_text())

    def test_packaged_demo_integration_guide_link_is_present_in_release(self):
        from scripts.package_release import FILES
        html = (ROOT / "examples/geo.html").read_text()
        self.assertIn("examples/geo.html", FILES)
        self.assertIn("docs/geo.md", FILES)
        self.assertIn('href="../docs/geo.md"', html)
        self.assertNotIn('href="../docs/geo.html"', html)

    def test_live_maplibre_smoke_is_dev_only(self):
        harness = (ROOT / "tests/geo_maplibre_browser.mjs").read_text()
        fixture = (ROOT / "tests/fixtures/geo-maplibre.html").read_text()
        from scripts.build_cloudflare_site import source_files
        from scripts.package_release import FILES
        app = (ROOT / "tests/fixtures/geo-maplibre-app.js").read_text()
        self.assertIn("maplibregl.Map", app)
        self.assertIn("maplibregl.Marker", app)
        self.assertIn(".setLngLat(", app, "Coordinates belong to MapLibre, not CSS percentages")
        self.assertIn("map.jumpTo(", app, "The renderer must own camera selection")
        self.assertIn("map.zoomIn", app)
        self.assertIn("filterSites()", app, "Map and data list must share filtering")
        self.assertIn("marker.remove()", app)
        self.assertIn('marker.getElement().dataset.synSelected = "false"', app)
        self.assertIn("aria-current", app)
        self.assertIn("site-selection-announcement", fixture)
        self.assertIn('role="status"', fixture)
        self.assertIn('id="site-status"', fixture)
        self.assertIn('id="site-details"', fixture)
        self.assertIn("No matching sites", app)
        self.assertNotIn("innerHTML", app, "Untrusted labels must use textContent")
        self.assertIn("server must provide only", app, "Client filters cannot assert tenant authorization")
        self.assertIn("getSelected", harness)
        self.assertIn("marker.getLngLat()", harness, "Browser must verify actual projection")
        self.assertIn('page.keyboard.press("Enter")', harness)
        self.assertIn("Space", harness)
        self.assertIn("forcedColors", harness)
        self.assertIn("let browser;", harness, "Browser launch must be cleanup-protected")
        self.assertIn("SYNTYR_VENDOR_NODE_MODULES", harness)
        self.assertIn("syntyr.geo.css", fixture)
        for reference in ("tests/fixtures/geo-maplibre.html",
                          "tests/fixtures/geo-maplibre-app.js",
                          "tests/geo_maplibre_browser.mjs"):
            with self.subTest(reference=reference):
                self.assertNotIn(reference, source_files())
                self.assertNotIn(reference, FILES)

    def test_guide_and_discovery_make_renderer_boundary_explicit(self):
        guide = (ROOT / "docs/geo.md").read_text()
        readme = (ROOT / "README.md").read_text()
        gallery = (ROOT / "docs/index.html").read_text()
        for term in ("MapLibre", "Leaflet", "OpenLayers", "attribution",
                     "screen reader", "projection", "Syntyr does not"):
            self.assertIn(term, guide)
        self.assertIn("syntyr.geo.css", guide)
        self.assertIn("syntyr.geo.css", readme)
        self.assertIn("docs/geo.md", readme)
        self.assertIn("../examples/geo.html", gallery)


if __name__ == "__main__":
    unittest.main()
