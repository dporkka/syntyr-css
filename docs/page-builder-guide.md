# Syntyr visual page builder (experimental)

The [visual builder](page-builder.html) is a local-first, optional editing tool in the public Syntyr documentation. It assembles a small set of existing Syntyr CSS/HTML patterns; it is **not** an application framework, CMS, universal importer, SaaS hosting product, or complete GrapesJS integration.

## What works

- Add hero, feature-card, split-text, testimonial, FAQ, CTA, site header and footer sections from the palette.
- Browse and search **85 copy-owned website/SaaS sections** from the generated canonical `metadata/section-composer.v1.json` library, filter by category, and edit their textual content and safe links. The library tracks the Blocks source manifest and snippets, so it does not maintain a second hand-edited section inventory.
- Search and insert **gallery components** from the generated `metadata/component-gallery.v1.json` contract (16 curated examples in the current source candidate). Edit their visible text, placeholders and safe links; examples carry the CSS modules needed and can be repeated without duplicate input IDs.
- The gallery is loaded from the same origin as the builder. If the JSON is missing, the original eight semantic page sections remain available; no external API or build service is required.
- Select sections in the outline or preview, edit text and safe links, reorder with keyboard-accessible **Up, Down, First, Last** buttons or drag-and-drop; duplicate or remove sections. Choose **Add after selected block** when inserting a new section in the middle of a page. Keyboard focus remains in the outline during reordering; native FAQ disclosures open in the preview.
- Switch among themes available to the unreleased source candidate and preview true 1200px desktop, 760px tablet, and 390px mobile iframe viewports. Narrow canvases scroll rather than silently scaling the device viewport.
- Undo and redo editing changes (limited in-memory history).
- Download a **static website ZIP** with `index.html`, the matching `syntyr.all.css`, any self-hosted SVG image assets, the MIT license and a brief publishing README. The ZIP contains **no JavaScript**. Standalone HTML/CSS downloads remain available.
- Download a JSON project and reopen that JSON to restore editability.

The builder runs entirely in your browser. It does not upload projects or require a server account. Save the JSON file before closing the page: unsaved edits are not persisted.

## Static-first export and assets

The optional browser-based builder uses JavaScript **only as an authoring tool**.
Its static ZIP output contains ordinary HTML/CSS and required local images,
without a Syntyr script, framework or build step. Native `details` disclosures,
image links, download links and visual layouts work without client JavaScript.
Use the ZIP when composing image sections so assets stay alongside `index.html`.
The standalone HTML download is only complete if you also supply the matching
stylesheet and referenced images. Asset paths in the exported site are relative
to the page, not to Syntyr's docs.

For the generated section library, the manifest contains only reviewed,
copy-owned canonical HTML. Imported projects contain **no executable HTML
templates**; text and links are escaped and restricted to declared editable
fields. Category search and section selection are optional editor behaviors,
not dependencies in exported markup.

Static exports deliberately **do not implement** authentication, commerce,
newsletter subscriptions, server forms, real search/filter results or
dynamic data. Those blocks are *presentational* and their form actions/routes
must be wired to your own backend. Replace fictional examples and claims.
Save the project JSON separately to continue editing; ZIP HTML is not a
lossless project source file.

## Framework-independent output

Gallery-backed blocks use a `gallery:<catalog-example-id>` type with only typed,
string-valued editable properties. The trusted native HTML fragment comes from
the generated, publicly published manifest, **never from imported project JSON**.
Imported projects referencing missing gallery definitions or incompatible
editable-field schemas fail validation rather than executing arbitrary markup.
A changed definition with the same field names can still import, potentially
placing saved strings in different locations. Preserve an exported HTML copy
for long-term rendering when the optional source catalog changes. The manifest is an **unreleased alpha.5 source candidate**; these
examples are not promised in the published alpha.4 release.

The document schema is syntyr.page.v1, with schema, title, theme, and an ordered array of id, type, and props blocks. The canonical validation and renderer are in page-builder-model.mjs, a dependency-free ESM module with no browser globals.

The exported index.html uses ordinary HTML sections, anchors, buttons-styled links, native FAQ disclosures, and existing syn-* classes. The local syntyr.all.css stylesheet must be hosted next to it; the page does not contain React, a builder script, or Syntyr editor dependencies. You can instead load CSS modules required by your chosen components using the [distribution guide](distribution.md).

An HTML export does **not** preserve editor metadata sufficiently for arbitrary HTML import; the JSON project is the editable source of truth. Proprietary embeds, CMS integrations, React/Vue/Svelte code generation, hosting, and collaboration are not yet implemented.

## Security boundaries

Imported project data is strictly validated: only recognized string block types and string fields, unique safe IDs, a known theme, up to 50 blocks, bounded property lengths, and a 16 MiB UTF-8 JSON import cap compatible with the maximum valid exported project size. Repeating gallery snippets scopes internal HTML IDs and their `for`,
`list`, `commandfor`, and ARIA references to each block instance.
The gallery manifest is restricted to checked-in, validated markup; links
are normalized to local anchors/paths or HTTPS. Every user-controlled text value is HTML escaped, and unsupported href protocols (including javascript: and data:) are rendered as #. The preview is inside a sandboxed iframe without script or form-submission permissions. The exported result is still **static HTML**, not a backend application.

This experimental tool is deliberately separate from the MIT CSS core. It uses only small first-party documentation scripts; adopting a heavyweight editor engine such as GrapesJS should be justified through comparative testing, not as a mandatory dependency.

## Maintainer verification

Run from repository root:

    node --test tests/page_builder_model.test.mjs tests/page_builder_gallery.test.mjs tests/page_builder_sections.test.mjs tests/page_builder_zip.test.mjs
    python3 scripts/build_section_composer.py --check
    python3 -m unittest tests.test_cloudflare_site -v
    python3 scripts/build_cloudflare_site.py --check

For the optional browser smoke test:

    python3 tests/page_builder_browser.py
    python3 tests/page_builder_sections_browser.py

The browser smoke test requires Playwright and a local browser installation. Validate keyboard access, small screens, malicious imported JSON, and download/export before treating this as a stable product.
