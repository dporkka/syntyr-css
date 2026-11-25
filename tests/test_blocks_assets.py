"""Copy-owned block/asset catalog contract. No consumer JavaScript or build tool."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "blocks/manifest.json"
ALLOWED = {"core", "recipes", "geometry", "symbols", "viz", "motion", "effects", "utilities"}


class InspectHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attributes = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attributes.append(dict(attrs))


class BlocksAssetsTests(unittest.TestCase):
    def test_all_independent_copy_owned_blocks(self):
        blocks = json.loads(MANIFEST.read_text(encoding="utf-8"))["blocks"]
        self.assertEqual(len(blocks), 102)
        self.assertEqual(len({b["id"] for b in blocks}), len(blocks))
        self.assertGreaterEqual(len({b["category"] for b in blocks}), 3)
        for block in blocks:
            with self.subTest(block=block["id"]):
                self.assertRegex(block["id"], r"^[a-z][a-z0-9-]+$")
                self.assertTrue(block["title"] and block["description"] and block["tags"])
                self.assertTrue(set(block["modules"]).issubset(ALLOWED))
                self.assertIn("core", block["modules"])
                source = (ROOT / "blocks" / "snippets" / (block["id"] + ".html")).read_text(encoding="utf-8")
                parser = InspectHTML()
                parser.feed(source)
                self.assertTrue(any("syn-root" in a.get("class", "").split() for a in parser.attributes))
                self.assertNotIn("script", parser.tags)
                self.assertNotIn("iframe", parser.tags)
                self.assertNotIn("onclick", " ".join(k for a in parser.attributes for k in a))
                self.assertNotIn('href="#"', source)
                self.assertNotIn("javascript:", source.lower())
                self.assertNotIn("http://", source)
                self.assertNotIn("https://", source)
                self.assertNotIn("data:image", source)
                self.assertIn("</", source)
                self.assertNotIn("syntyr.all.css", source)

    def test_first_tranche_covers_native_application_and_marketing_workflows(self):
        blocks = json.loads(MANIFEST.read_text(encoding="utf-8"))["blocks"]
        by_id = {block["id"]: block for block in blocks}
        new_blocks = {
            "auth-sign-in", "auth-recovery", "error-recovery", "empty-state",
            "comparison-table", "integrations-grid", "newsletter-signup",
            "announcement-banner",
        }
        self.assertEqual(len(blocks), 102)
        for ident in new_blocks:
            with self.subTest(ident=ident):
                self.assertIn(ident, by_id)
                self.assertIn(by_id[ident]["category"], {"Marketing", "Applications"})
                self.assertEqual(by_id[ident]["modules"], ["core"])

    def test_seven_original_marketing_sections_extend_without_replacing_existing_blocks(self):
        # Preserve all 31 existing canonical blocks, including the three
        # application workflows that #248 would otherwise have removed.
        original = set("""hero-product,hero-security,feature-grid,feature-checklist,pricing-trio,testimonial,faq,cta-band,metric-overview,activity-feed,data-table,filter-toolbar,settings-form,team-directory,billing-summary,onboarding-steps,terminal-session,incident-notice,telemetry-status,release-notes,resource-workspace,crm-workspace,billing-workspace,auth-sign-in,auth-recovery,error-recovery,empty-state,comparison-table,integrations-grid,newsletter-signup,announcement-banner""".split(","))
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))["blocks"]
        old = original
        current = {b["id"] for b in manifest}
        sections = {"logo-wall", "process-steps", "services-grid", "service-areas",
                    "portfolio-grid", "team-grid", "contact-quote"}
        self.assertEqual(len(manifest), 102)
        self.assertTrue(sections <= current - old)
        self.assertTrue(old <= current, "New blocks must not replace existing blocks")
        for ident in sections:
            source = (ROOT / "blocks/snippets" / f"{ident}.html").read_text()
            parser = InspectHTML()
            parser.feed(source)
            self.assertIn("h2", parser.tags)
            self.assertTrue(any("syn-root" in a.get("class", "").split()
                                for a in parser.attributes))
            self.assertNotIn("script", parser.tags)
        contact = (ROOT / "blocks/snippets/contact-quote.html").read_text()
        self.assertIn('type="email"', contact)
        self.assertIn('method="post"', contact)

    def test_gallery_filter_categories_match_manifest_categories(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))["blocks"]
        gallery = (ROOT / "docs/blocks.html").read_text()
        class Categories(HTMLParser):
            def __init__(self):
                super().__init__()
                self.in_filter = False
                self.values = []
            def handle_starttag(self, tag, attrs):
                a = dict(attrs)
                if tag == "select" and a.get("id") == "blocks-category":
                    self.in_filter = True
                if tag == "option" and self.in_filter and a.get("value") != "all":
                    self.values.append(a.get("value"))
            def handle_endtag(self, tag):
                if tag == "select":
                    self.in_filter = False
        parsed = Categories()
        parsed.feed(gallery)
        self.assertEqual(set(parsed.values), {b["category"] for b in manifest})
        self.assertEqual(len(parsed.values), len(set(parsed.values)))
        self.assertTrue({"Services", "Portfolio"} <= set(parsed.values))

    def test_form_previews_are_disabled_without_modifying_copyable_snippets(self):
        from html import unescape

        class FormAudit(HTMLParser):
            def __init__(self):
                super().__init__()
                self.in_form = False
                self.disabled_stack = []
                self.controls = []

            def handle_starttag(self, tag, attrs):
                attributes = dict(attrs)
                if tag == "form":
                    self.in_form = True
                elif tag == "fieldset" and self.in_form:
                    self.disabled_stack.append(
                        "disabled" in attributes or any(self.disabled_stack))
                elif tag in {"input", "select", "button", "textarea"} and self.in_form:
                    self.controls.append(any(self.disabled_stack))

            def handle_endtag(self, tag):
                if tag == "fieldset" and self.disabled_stack:
                    self.disabled_stack.pop()
                elif tag == "form":
                    self.in_form = False
                    self.disabled_stack.clear()

        page = (ROOT / "docs/blocks.html").read_text(encoding="utf-8")
        for ident in ("auth-sign-in", "auth-recovery", "newsletter-signup", "resource-workspace"):
            with self.subTest(ident=ident):
                card = page.split(f'data-block-id="{ident}"', 1)[1].split('      </article>', 1)[0]
                preview = card.split('<div class="blocks-preview">', 1)[1].split('<details class="blocks-details">', 1)[0]
                audit = FormAudit()
                audit.feed(preview)
                self.assertTrue(audit.controls, f"{ident}: missing preview form controls")
                self.assertTrue(all(audit.controls), f"{ident}: controls outside disabled fieldset")
                self.assertNotIn('href=', preview, f"{ident}: gallery preview may navigate")
                snippet = (ROOT / "blocks/snippets" / f"{ident}.html").read_text().strip()
                source = card.split('<pre class="blocks-source"><code>', 1)[1].split('</code></pre>', 1)[0]
                self.assertEqual(unescape(source).strip(), snippet)
        css = (ROOT / "docs/blocks.css").read_text()
        self.assertIn('.syn-root .syn-form>.blocks-preview-disabled', css)
        self.assertIn('.syn-root .syn-filter-bar>.blocks-preview-disabled', css)
        self.assertIn('flex-grow:1', css)

    def test_preview_transform_does_not_enable_fake_form_actions_or_navigation(self):
        from scripts.build_blocks import preview_markup
        sample = ('<form data-rule="length > 0" action="/pretend" method="post">'
                  '<input name="query"><button type="submit">Submit</button></form>'
                  '<a href="/pretend/recover">Recover</a>')
        preview = preview_markup(sample)
        self.assertIn('<form data-rule="length > 0"><fieldset', preview.replace(' action="/pretend" method="post"', ''))
        self.assertIn('disabled>', preview)
        self.assertIn('<input name="query"><button', preview)
        self.assertIn('</fieldset></form>', preview)
        self.assertIn('<a>Recover</a>', preview)
        self.assertNotIn('href="/pretend/recover"', preview)

    def test_preview_transform_respects_textarea_and_attribute_boundaries(self):
        from scripts.build_blocks import preview_markup
        source = (
            '<form id="demo" action="/submit"><textarea name="notes">Keep literal '
            '</form> text</textarea><fieldset><input name="nested"></fieldset>'
            '<button type="submit">Inside</button></form>'
            '<a aria-label=\'Documentation: href="/help"\' href="/help">Help</a>'
            '<button type="submit" form="demo">Outside</button>'
        )
        preview = preview_markup(source)
        self.assertIn('<textarea name="notes">Keep literal </form> text</textarea>', preview)
        self.assertEqual(preview.count('</fieldset></form>'), 1)
        self.assertIn('<a aria-label=\'Documentation: href="/help"\'>Help</a>', preview)
        self.assertIn('<button type="submit" form="demo" disabled>Outside</button>', preview)
        self.assertNotIn('<a aria-label=\'Documentation: href="/help"\' href=', preview)

    def test_preview_form_audit_handles_nested_fieldsets(self):
        from scripts.build_blocks import preview_markup
        source = (
            '<form action="/submit"><fieldset><input name="nested"></fieldset>'
            '<button type="submit">Submit</button></form>'
        )
        preview = preview_markup(source)
        class Audit(HTMLParser):
            def __init__(self):
                super().__init__()
                self.disabled_stack = []
                self.control_states = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "fieldset":
                    self.disabled_stack.append("disabled" in attrs or
                        bool(self.disabled_stack and self.disabled_stack[-1]))
                if tag in {"button", "input"}:
                    self.control_states.append(bool(self.disabled_stack and self.disabled_stack[-1]))
            def handle_endtag(self, tag):
                if tag == "fieldset":
                    self.disabled_stack.pop()
        audit = Audit()
        audit.feed(preview)
        self.assertEqual(audit.control_states, [True, True])

    def test_reviewed_comparison_and_error_copy_is_accessible_and_truthful(self):
        comparison = (ROOT / 'blocks/snippets/comparison-table.html').read_text()
        recovery = (ROOT / 'blocks/snippets/error-recovery.html').read_text()
        self.assertRegex(comparison, r'class="syn-table-wrap"[^>]*role="region"[^>]*tabindex="0"')
        self.assertNotIn('You can retry', recovery)

    def test_scrollable_resource_and_billing_tables_have_named_keyboard_regions(self):
        from html.parser import HTMLParser

        class TableRegionAudit(HTMLParser):
            def __init__(self):
                super().__init__()
                self.wrapper = None
                self.in_wrapper = False
                self.contains_table = False
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "div" and "syn-table-wrap" in attrs.get("class", "").split():
                    self.wrapper = attrs
                    self.in_wrapper = True
                if tag == "table" and self.in_wrapper:
                    self.contains_table = True
            def handle_endtag(self, tag):
                if tag == "div" and self.in_wrapper:
                    self.in_wrapper = False

        for ident in ("resource-workspace", "billing-workspace"):
            with self.subTest(block=ident):
                source = (ROOT / "blocks/snippets" / (ident + ".html")).read_text()
                audit = TableRegionAudit()
                audit.feed(source)
                self.assertTrue(audit.contains_table)
                self.assertEqual(audit.wrapper.get("role"), "region")
                self.assertEqual(audit.wrapper.get("tabindex"), "0")
                self.assertTrue(audit.wrapper.get("aria-label"), "Missing table region name")

    def test_gallery_is_generated_and_progressively_enhanced(self):
        result = subprocess.run(
            [sys.executable, "scripts/build_blocks.py", "--check"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        page = (ROOT / "docs/blocks.html").read_text(encoding="utf-8")
        parsed = InspectHTML()
        parsed.feed(page)
        ids = [a["data-block-id"] for a in parsed.attributes if "data-block-id" in a]
        self.assertEqual(len(ids), len(json.loads(MANIFEST.read_text())["blocks"]))
        self.assertEqual(len(set(ids)), len(ids))
        self.assertIn('src="blocks.js"', page)
        self.assertIn('href="blocks-assets.css"', page)
        self.assertIn('id="blocks-search"', page)
        self.assertIn('id="blocks-results"', page)
        self.assertIn("Copy HTML", page)
        self.assertIn("<details", page)
        self.assertIn('id="blocks-theme"', page)
        self.assertIn("without JavaScript", page)

    def test_repeated_source_and_copy_controls_have_contextual_names(self):
        page = (ROOT / "docs/blocks.html").read_text(encoding="utf-8")
        parser = InspectHTML()
        parser.feed(page)
        copy_labels = [attrs.get("aria-label", "") for attrs in parser.attributes
                       if "data-block-copy" in attrs]
        self.assertEqual(len(copy_labels), len(json.loads(MANIFEST.read_text())["blocks"]))
        self.assertEqual(len(set(copy_labels)), len(copy_labels))
        self.assertTrue(all(name.startswith("Copy HTML for ") for name in copy_labels))
        for block in json.loads(MANIFEST.read_text(encoding="utf-8"))["blocks"]:
            self.assertIn("View HTML source for " + block["title"] + "</summary>", page)
        for icon in json.loads((ROOT / "blocks/icons.json").read_text(encoding="utf-8"))["icons"]:
            self.assertIn("SVG source for " + icon["label"] + "</summary>", page)

    def test_twelve_opt_in_decorative_asset_recipes(self):
        css = (ROOT / "docs/blocks-assets.css").read_text(encoding="utf-8")
        ids = re.findall(r"/\* asset: ([a-z][a-z0-9-]+) \*/", css)
        self.assertEqual(len(ids), 12)
        self.assertEqual(len(set(ids)), 12)
        for ident in ids:
            self.assertIn(".syn-block-asset--" + ident, css)
        self.assertNotIn("@import", css)
        self.assertNotIn("url(", css)
        self.assertNotIn("@font-face", css)
        self.assertIn("prefers-reduced-motion", css)

    def test_fine_grid_caption_has_opaque_backplate(self):
        # The fine grid crosses small caption glyphs unless the caption is
        # painted over an opaque semantic surface, unlike decorative patterns.
        css = (ROOT / "docs/blocks-assets.css").read_text(encoding="utf-8")
        self.assertRegex(
            css,
            r"\.syn-root :is\([^)]*\.syn-block-asset--fine-grid[^)]*\)>span\s*\{"
            r"\s*background:var\(--syn-surface\);"
        )
        self.assertIn(".syn-block-asset--dot-field", css)
        self.assertIn(".syn-block-asset--diagonal", css)

    def test_radar_asset_caption_uses_high_contrast_theme_text(self):
        # The decorative radar ring crossed muted caption text at 390px;
        # don't rely on a narrowly passing background sample.
        css = (ROOT / "docs/blocks-assets.css").read_text(encoding="utf-8")
        self.assertRegex(
            css, r"\.syn-root \.syn-block-asset--radar>span\s*\{\s*color:var\(--syn-text\)"
        )

    def test_expanded_original_svg_icon_examples(self):
        icons = json.loads((ROOT / "blocks/icons.json").read_text(encoding="utf-8"))["icons"]
        self.assertGreaterEqual(len(icons), 150)
        self.assertEqual(len({icon["id"] for icon in icons}), len(icons))
        for icon in icons:
            with self.subTest(icon=icon["id"]):
                self.assertRegex(icon["id"], r"^[a-z][a-z0-9-]+$")
                self.assertTrue(icon["label"])
                self.assertTrue(icon["body"].startswith("<"))
                self.assertNotIn("<script", icon["body"])
                self.assertNotIn("href=", icon["body"])
                self.assertNotIn("url(", icon["body"])
        from xml.etree import ElementTree
        for icon in icons:
            with self.subTest(svg=icon["id"]):
                svg = ElementTree.fromstring('<svg xmlns="http://www.w3.org/2000/svg">' + icon["body"] + '</svg>')
                self.assertTrue(all(element.tag.split("}")[-1] in {"svg", "path", "circle", "rect", "line", "polyline", "ellipse"} for element in svg.iter()))
        essential = {"home", "menu", "plus", "minus", "edit", "trash", "copy", "share",
                     "refresh", "loader", "eye", "eye-off", "mail", "phone", "link",
                     "folder", "file", "image", "heart", "star", "play", "pause",
                     "chevron-down", "chevron-up", "arrow-left", "arrow-right",
                     "more-horizontal", "check-circle", "help-circle", "log-out",
                     "log-in", "grid", "list", "sun", "moon", "send"}
        self.assertTrue(essential.issubset({icon["id"] for icon in icons}))
        next_wave = {
            "layout-dashboard", "panel-left", "panel-right", "layers", "compass",
            "navigation", "map", "route", "maximize", "minimize", "move", "grip",
            "arrow-up-right", "arrow-down-right", "corner-down-left", "corner-down-right",
            "expand", "shrink", "undo", "redo", "sort-asc", "sort-desc", "zoom-in",
            "zoom-out", "archive", "inbox", "paperclip", "clipboard", "clipboard-check",
            "file-plus", "file-text", "folder-open", "folder-plus", "hard-drive",
            "package", "tag", "pin", "message-square", "at-sign", "bell-off",
            "video", "mic", "mic-off", "headphones", "camera", "music",
            "volume-x", "wifi", "wifi-off", "alert-circle", "x-circle",
            "circle-plus", "circle-minus", "shield-check", "activity", "power",
            "laptop", "monitor", "smartphone", "cpu", "server", "battery",
            "battery-charging", "user-plus", "user-check", "user-x", "wallet",
            "receipt", "dollar-sign", "gift", "pie-chart", "trending-up",
            "trending-down"
        }
        self.assertTrue(next_wave.issubset({icon["id"] for icon in icons}))

        page = (ROOT / "docs/blocks.html").read_text(encoding="utf-8")
        parser = InspectHTML()
        parser.feed(page)
        previews = [a for a in parser.attributes if "data-icon-id" in a]
        self.assertEqual(len(previews), len(icons))
        self.assertIn('id="blocks-icons-heading"', page)
        self.assertIn('aria-hidden="true"', page)
        self.assertIn('id="blocks-icon-search"', page)
        self.assertIn('id="blocks-icon-results"', page)
        self.assertIn('syn-icon--on-interact', page)
        self.assertEqual(page.count('class="syn-button blocks-motion-example"'), 14)

        script = (ROOT / "docs/blocks.js").read_text(encoding="utf-8")
        self.assertIn("function filterIcons()", script)
        self.assertIn("iconQuery.addEventListener", script)

    def test_public_site_ships_only_reviewed_gallery_files(self):
        from scripts.build_cloudflare_site import source_files
        files = source_files()
        for name in ("docs/blocks.html", "docs/blocks.css",
                     "docs/blocks.js", "docs/blocks-assets.css",
                     "docs/blocks-guide.md"):
            self.assertIn(name, files)
        self.assertFalse(any(name.startswith("blocks/") for name in files))


if __name__ == "__main__":
    unittest.main()
