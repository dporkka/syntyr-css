"""Generate the static, copy-owned Syntyr Blocks gallery from tested HTML fragments.

Documentation build only. Browser users receive prebuilt markup; no app runtime.
"""
from __future__ import annotations

import argparse
from html import escape
from html.parser import HTMLParser
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/blocks.html"

ASSETS = (
    ("fine-grid", "Fine grid"),
    ("dot-field", "Dot field"),
    ("radar", "Radar rings"),
    ("ambient-glow", "Ambient glow"),
    ("glass", "Frosted surface"),
    ("blueprint", "Blueprint"),
    ("signal-stripes", "Signal stripes"),
    ("diagonal", "Diagonal hatch"),
    ("beam", "Scanning beam"),
    ("corners", "Corner markers"),
    ("horizon", "Horizon"),
    ("circuit", "Circuit trace"),
)

TYPOGRAPHY = (
    ("studio", "Studio sans", "system-ui, sans-serif", "Interface-first typography"),
    ("editorial", "Editorial serif", "ui-serif, Georgia, serif", "Considered storytelling"),
    ("mono", "Terminal mono", "ui-monospace, monospace", "Machine-readable surfaces"),
    ("technical", "Technical sans", "Arial, Helvetica, sans-serif", "Precise operational labels"),
    ("reading", "Reading serif", "Georgia, serif", "Long-form product narratives"),
    ("compact", "Compact system", "system-ui, sans-serif", "Dense dashboards, still legible"),
)


# Only presentation in the documentation gallery is transformed. Copyable
# source and universal registry snippets retain the real host-owned routes.
# Use parsed token positions instead of regex substitutions on whole HTML.
# For example, </form> in a textarea value must not close the preview wrapper.
ATTR_TOKEN = re.compile(
    r"""(?P<ws>\s+)(?P<name>[^\s=/>]+)(?:\s*=\s*(?P<value>"[^"]*"|'[^']*'|[^\s>]+))?"""
)


def _without_link_target(tag_text: str) -> str:
    """Remove a genuine href attribute, never href-looking text in another value."""
    element_name = re.match(r"<\s*[a-z][a-z0-9-]*", tag_text, re.IGNORECASE)
    if element_name is None:
        return tag_text
    pos = element_name.end()
    pieces = [tag_text[:pos]]
    while pos < len(tag_text):
        matched = ATTR_TOKEN.match(tag_text, pos)
        if matched is None:
            pieces.append(tag_text[pos:])
            break
        if matched.group("name").lower() != "href":
            pieces.append(matched.group())
        pos = matched.end()
    return "".join(pieces)


def preview_markup(source: str) -> str:
    """Render inert HTML previews while leaving source and copy exports unchanged."""
    # HTMLParser handles quoted attributes, multiline tags, and actual end-tag
    # boundaries. Textarea/title are HTML raw-text-ish contexts here: literal
    # fake </form> strings must never trigger wrapper substitutions.
    class PreviewParser(HTMLParser):
        CDATA_CONTENT_ELEMENTS = ("script", "style", "textarea", "title")

        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.line_offsets = [0]
            for line in source.splitlines(keepends=True):
                self.line_offsets.append(self.line_offsets[-1] + len(line))
            self.edits = []
            self.form_ids = set()
            self.associated_controls = []

        def source_offset(self):
            line, column = self.getpos()
            return self.line_offsets[line - 1] + column

        def handle_starttag(self, tag, attrs):
            attributes = dict(attrs)
            raw = self.get_starttag_text()
            start = self.source_offset()
            if tag == "form":
                self.edits.append((start + len(raw), start + len(raw),
                                   '<fieldset class="blocks-preview-disabled" disabled>'))
                if attributes.get("id"):
                    self.form_ids.add(attributes["id"])
            elif tag == "a":
                safe = _without_link_target(raw)
                if safe != raw:
                    self.edits.append((start, start + len(raw), safe))
            elif tag in {"button", "input", "select", "textarea"}:
                if attributes.get("form") and "disabled" not in attributes:
                    self.associated_controls.append((start, raw, attributes["form"]))

        def handle_startendtag(self, tag, attrs):
            self.handle_starttag(tag, attrs)

        def handle_endtag(self, tag):
            if tag == "form":
                start = self.source_offset()
                self.edits.append((start, start, "</fieldset>"))

    parser = PreviewParser()
    parser.feed(source)
    parser.close()

    # A submit control associated by form=id can live outside the form tree:
    # disabling only descendant fieldsets does not disable such controls.
    for start, raw, form_id in parser.associated_controls:
        if form_id in parser.form_ids:
            closing = re.search(r"\s*/?>$", raw)
            if closing is None:
                raise ValueError("Invalid associated form control markup")
            safe = raw[:closing.start()] + " disabled" + raw[closing.start():]
            parser.edits.append((start, start + len(raw), safe))

    preview = source
    for start, end, replacement in sorted(parser.edits, key=lambda edit: edit[0], reverse=True):
        preview = preview[:start] + replacement + preview[end:]
    return preview


def build() -> str:
    blocks = json.loads((ROOT / "blocks/manifest.json").read_text(encoding="utf-8"))["blocks"]
    count = len(blocks)
    # New categories must be discoverable without hardcoded UI options.
    categories = list(dict.fromkeys(block["category"] for block in blocks))
    category_options = "".join(
        f'<option value="{escape(category, quote=True)}">{escape(category)}</option>'
        for category in categories
    )
    cards = []
    for block in blocks:
        ident = block["id"]
        snippet = (ROOT / "blocks/snippets" / f"{ident}.html").read_text(encoding="utf-8").strip()
        # Preview-only fieldset prevents accidental submissions to fictional
        # endpoints; preserve the original HTML in the copyable code sample.
        preview = preview_markup(snippet)
        modules = " + ".join(f"syntyr.{module}.css" for module in block["modules"])
        tags = " ".join([block["title"], block["description"], *block["tags"]])
        cards.append(f"""
      <article class="blocks-card syn-panel" data-block-id="{escape(ident)}"
               data-block-category="{escape(block['category'])}"
               data-block-keywords="{escape(tags, quote=True)}"
               aria-labelledby="block-title-{escape(ident)}">
        <div class="blocks-card-heading">
          <div><p class="syn-eyebrow">{escape(block['category'])}</p>
            <h2 class="syn-heading" id="block-title-{escape(ident)}">{escape(block['title'])}</h2></div>
          <span class="syn-badge">{escape(modules)}</span>
        </div>
        <p class="syn-muted">{escape(block['description'])}</p>
        <div class="blocks-preview">
{preview}
        </div>
        <details class="blocks-details">
          <summary data-block-source>View HTML source for {escape(block['title'])}</summary>
          <pre class="blocks-source"><code>{escape(snippet)}</code></pre>
        </details>
        <button type="button" class="syn-button blocks-copy" data-block-copy
                aria-label="Copy HTML for {escape(block['title'], quote=True)}" hidden>Copy HTML</button>
      </article>""")
    icons = json.loads((ROOT / "blocks/icons.json").read_text(encoding="utf-8"))["icons"]
    icon_count = len(icons)
    icon_cards = []
    for icon in icons:
        ident, label = escape(icon["id"]), escape(icon["label"])
        svg = ('<svg class="syn-icon" viewBox="0 0 24 24" fill="none" '
               'stroke="currentColor" stroke-width="1.7" '
               'stroke-linecap="round" stroke-linejoin="round" '
               'aria-hidden="true" focusable="false">'
               + icon["body"] + '</svg>')
        icon_cards.append(f"""
        <div class="blocks-icon-card" data-icon-id="{ident}">
          <div class="blocks-icon-preview">{svg}<strong>{label}</strong></div>
          <details><summary data-icon-source>SVG source for {escape(icon['label'])}</summary><pre><code>{escape(svg)}</code></pre></details>
        </div>""")
    animation_cards = []
    motion_examples = (("spin", "refresh"), ("pulse", "heart"),
                       ("bounce", "arrow-up"), ("shake", "notification"),
                       ("wiggle", "star"), ("pop", "check-circle"))
    icon_by_id = {icon["id"]: icon for icon in icons}
    for preset, icon_id in motion_examples:
        icon = icon_by_id[icon_id]
        svg = ('<svg class="syn-icon syn-icon--' + preset + ' syn-icon--on-interact" '
               'viewBox="0 0 24 24" fill="none" stroke="currentColor" '
               'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
               'aria-hidden="true" focusable="false">' + icon["body"] + '</svg>')
        animation_cards.append(
            '<button type="button" class="syn-button blocks-motion-example">'
            + svg + '<span>' + preset.capitalize() + '</span></button>'
        )
    asset_cards = []
    for ident, title in ASSETS:
        asset_cards.append(f"""
        <div class="blocks-asset-preview syn-block-asset syn-block-asset--{ident}">
          <strong>{escape(title)}</strong><span>Original CSS, no image required</span>
        </div>""")
    type_cards = []
    for ident, name, _, demo in TYPOGRAPHY:
        type_cards.append(f"""
        <div class="blocks-type blocks-type--{ident}"><span class="syn-caption">{escape(name)}</span>
          <strong>{escape(demo)}</strong><small>Aa 0123456789</small></div>""")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="{count} original HTML/CSS blocks, 12 visual assets, and {icon_count} SVG icon examples for Syntyr. View, filter, and copy without a framework.">
  <title>Free HTML/CSS Blocks and UI Assets — Syntyr CSS</title>
  <link rel="stylesheet" href="../dist/syntyr.all.css">
  <link rel="stylesheet" href="docs.css">
  <link rel="stylesheet" href="blocks.css">
  <link rel="stylesheet" href="blocks-assets.css">
  <script src="blocks.js" defer></script>
</head>
<body class="syn-root syn-page" data-syn-theme="studio">
  <a href="#blocks-main" class="syn-button blocks-skip">Skip to blocks</a>
  <header class="syn-header syn-shell">
    <a class="syn-logo" href="index.html">SYNTYR / BLOCKS &amp; ASSETS</a>
    <nav class="syn-nav" aria-label="Documentation">
      <a href="index.html">Gallery</a><a href="catalog.html">Components</a>
      <a href="blocks-guide.html">Integration guide</a><a href="how-to.html">How-To</a>
    </nav>
  </header>
  <main class="syn-shell" id="blocks-main">
    <section class="docs-section">
      <p class="syn-eyebrow">COPY-OWNED / FRAMEWORK-INDEPENDENT</p>
      <h1 class="syn-title">{count} production-shaped blocks.</h1>
      <p class="syn-lede">Build faster with original HTML compositions styled by Syntyr.
      Every preview renders without JavaScript. Search, theme switching, and copying
      are documentation-only enhancements, not dependencies for your application.</p>
      <p class="syn-caption">These are static illustrative presentations: real authentication,
      billing, filtering, form validation, persistence and permissions belong to your application.
      <a href="blocks-guide.html">Read integration and accessibility guidance.</a></p>
      <div class="blocks-controls" id="blocks-controls" hidden>
        <div><label class="syn-label" for="blocks-search">Search blocks</label>
          <input class="syn-input" type="search" id="blocks-search" placeholder="Try pricing, settings, telemetry…" autocomplete="off"></div>
        <div><label class="syn-label" for="blocks-category">Category</label>
          <select class="syn-select" id="blocks-category"><option value="all">All categories</option>
            {category_options}</select></div>
        <div><label class="syn-label" for="blocks-theme">Preview theme</label>
          <select class="syn-select" id="blocks-theme">
            <option value="studio">Studio</option><option value="grid">Grid</option>
            <option value="noir">Noir</option><option value="industrial">Industrial</option>
            <option value="terminal">Terminal</option><option value="corporate">Corporate</option>
            <option value="minimal">Minimal</option>
          </select></div>
      </div>
      <p id="blocks-results" class="syn-caption" role="status" aria-live="polite">{count} blocks available.</p>
      <p id="blocks-feedback" class="syn-caption" role="status" aria-live="polite" aria-atomic="true"></p>
      <p id="blocks-empty" class="syn-alert" hidden>No blocks found. Try a different search or category.</p>
      <div id="blocks-grid" class="blocks-grid">{''.join(cards)}
      </div>
    </section>
    <section class="docs-section" aria-labelledby="blocks-assets-heading">
      <p class="syn-eyebrow">OPTIONAL / DOCS-ONLY CSS</p>
      <h2 id="blocks-assets-heading" class="syn-title">12 original visual textures</h2>
      <p class="syn-muted">Opt into these styles separately; they are not included in the core or all-in-one Syntyr bundles.
      Copy <a href="blocks-assets.css">the documented asset stylesheet</a> only if needed.
      Effects are decorative and never convey application state.</p>
      <div class="blocks-assets-grid">{''.join(asset_cards)}
      </div>
    </section>
    <section class="docs-section" aria-labelledby="blocks-icons-heading">
      <p class="syn-eyebrow">INLINE SVG / NO ICON FONT</p>
      <h2 id="blocks-icons-heading" class="syn-title">{icon_count} original SVG icon examples</h2>
      <p class="syn-muted">Small, copyable SVGs that inherit theme color and work with the existing
      Syntyr symbol-sizing contract. These are examples, not a bundled icon dependency.
      When icons are used alone as controls, add accessible names.</p>
      <div class="blocks-icon-controls" id="blocks-icon-controls" hidden>
        <label class="syn-label" for="blocks-icon-search">Find an icon</label>
        <input class="syn-input" type="search" id="blocks-icon-search" placeholder="Search icons, e.g. mail, home, copy" autocomplete="off">
      </div>
      <p class="syn-caption" id="blocks-icon-results" role="status" aria-live="polite">{icon_count} icons available.</p>
      <div class="blocks-icons-grid">{''.join(icon_cards)}</div>
      <h3 class="syn-heading">Icon animation presets</h3>
      <p class="syn-muted">Hover or keyboard-focus these examples. Add a motion class to any icon,
      plus <code>syn-icon--on-interact</code> to animate only during interaction. Continuous
      animation is also supported. Motion respects reduced-motion preferences.
      <a href="symbols.html">Read the CSS API and examples.</a></p>
      <div class="syn-actions blocks-motion-examples">{''.join(animation_cards)}</div>
    </section>
    <section class="docs-section" aria-labelledby="blocks-type-heading">
      <p class="syn-eyebrow">FONT-AGNOSTIC / NO REMOTE FONTS</p>
      <h2 id="blocks-type-heading" class="syn-title">Six typography directions</h2>
      <p class="syn-muted">Reference combinations use system or installed fallback fonts. Customize
      <code>--syn-font-ui</code>, <code>--syn-font-display</code> and <code>--syn-mono</code>.
      The examples do not download or bundle typefaces.</p>
      <div class="blocks-type-grid">{''.join(type_cards)}</div>
    </section>
  </main>
  <footer class="syn-shell blocks-footer"><p class="syn-caption">MIT-licensed Syntyr source; original block markup and textures.</p>
    <a href="blocks-guide.html">License, framework setup and accessibility notes</a></footer>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = build()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != output:
            print("STALE Blocks gallery: run python3 scripts/build_blocks.py", file=sys.stderr)
            return 1
        print("OK Blocks gallery is reproducible")
        return 0
    OUTPUT.write_text(output, encoding="utf-8")
    print("Generated docs/blocks.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
