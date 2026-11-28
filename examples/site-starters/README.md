# Portable Syntyr website starters

Four original multi-page MIT starters built with ordinary HTML, local CSS and
native links. Each includes three connected pages. No client-side JavaScript,
framework, npm, CDN, remote font, or database is required.

| Starter | Composition | Preview after publication |
| --- | --- | --- |
| `saas-marketing` | Product homepage, pricing, about | [Waypoint](https://syntyr-css.pages.dev/examples/site-starters/saas-marketing/) |
| `documentation` | Overview, code-example guide, reference with native FAQ | [Fieldnotes Docs](https://syntyr-css.pages.dev/examples/site-starters/documentation/) |
| `blog` | Journal index, two editorial articles with dates and pagination | [Quiet Systems](https://syntyr-css.pages.dev/examples/site-starters/blog/) |
| `portfolio` | Selected work, project case study, about | [Avery Lane](https://syntyr-css.pages.dev/examples/site-starters/portfolio/) |

The three new archetypes share one private composition stylesheet in the
repository. They have separate semantic markup and theme selections; each export
contains an independent copy of that stylesheet. The existing SaaS starter
keeps its original layout CSS and CLI default.

## Export (no generator required)

From the repository root, verify the current candidate distribution:

```sh
python3 scripts/build.py --check
python3 scripts/export_site_starter.py --starter documentation --output /tmp/fieldnotes
python3 scripts/export_site_starter.py --starter documentation --output /tmp/fieldnotes --check
python3 -m http.server 8000 --directory /tmp/fieldnotes
```

Open `http://localhost:8000/` or open the exported `index.html` directly in
a browser. Replace the starter name with any of the four listed above. Omit
`--starter` for the backward-compatible Waypoint export.

Each export contains exactly three HTML files, `assets/syntyr.core.css`,
`assets/site.css` and `LICENSE`. The exporter validates local stylesheets,
native landmarks, script-free HTML and local navigation/fragment targets before
atomically publishing a new directory. It refuses existing destinations,
including symlinks; `--check` verifies exact source bytes without overwriting.
Two exports of identical sources contain identical file bytes. The output is
portable at the root or a subpath and has no mandatory build/runtime dependency.
The checker is not a browser accessibility audit or general HTML sanitizer.

## Versioned candidate ZIPs

A maintainer can produce all four archives with the same explicit export
allowlist and a SHA-256 manifest. No generator or npm is used to package them.

```sh
python3 scripts/package_site_starters.py --output /tmp/syntyr-starter-candidates
python3 scripts/package_site_starters.py --output /tmp/syntyr-starter-candidates --check
```

Names are `syntyr-starter-<name>-<VERSION>.zip`; each has six files at its
root, fixed timestamps and file modes, and stored bytes (no compressor-version
drift). The manifest records each ZIP's byte count, SHA-256, and per-file
hashes. The package builder verifies compiled CSS first, refuses existing
destinations and publishes new directories atomically. Check mode rebuilds in
a temporary directory and compares all bytes without modifying the originals.

These are **unreleased candidate archives**, not downloads hosted by Syntyr
or signed releases. An unsigned checksum detects drift relative to a trusted
manifest; it does not authenticate the publisher. Do not advertise these
archives as alpha.5 releases until the separate release approval process in
[`docs/release-freeze.md`](../../docs/release-freeze.md) is complete.

## Adapt to an existing generator or website

- Copy the complete exported site (including the MIT license), or copy the
  local stylesheet and only the selected semantic section into an existing
  Syntyr-scoped page. Preserve native elements and valid heading relationships.
- For Hugo, Eleventy or Astro, use your generator's native layout/includes for
  the header, navigation and footer. Keep links generator-base-aware; validate
  the rendered HTML, not only the source template.
- Keep the Syntyr CSS pinned to the chosen release. These examples use the
  **unreleased alpha.5 source candidate**, not the published alpha.4 snapshot.
- Replace fictional names, product/project claims and contact information.
  Remove `noindex,follow` from exported demos only when the content is ready for
  public indexing; configure canonical URLs in the host application.
- Backend forms, authentication, billing, analytics and dynamic content remain
  host-owned. None of the examples is a live product or commercial offer.

The source folders are repository-relative previews. Do **not** copy one folder
alone without exporting; its stylesheet references reach the shared sources.
No additional CSS public API or premium SKU is introduced by these MIT examples.

## Browser validation

The `portable-starters.yaml` Woodpecker gate checks related PRs and main
pushes, plus all manual/tag runs. It reuses the existing locked Lit-example
Node Playwright development driver, avoiding Woodpecker's blocked PyPI
access. Independently verify it locally with:

```sh
npm ci --prefix examples/lit --no-audit --no-fund
node examples/lit/portable-starters-browser.mjs
```

The CI check compares exact PNG bytes in Chromium in the same run (no saved
golden images). The optional Python runner below additionally supports
cross-generator CMS fixtures and a small pixel tolerance. Neither runner is
required by the library or exported sites.

### Optional cross-generator browser validation

From the repository root, with maintainer-only Playwright, Pillow and Chromium
installed:

```sh
python3 -m tests.static_site_visual_browser
```

This compares the repository preview with each exported page served under a
nested base path at 320, 390 and 1280 pixels. Browser JavaScript is disabled
and external network requests are blocked. It checks stylesheet loading,
horizontal overflow, keyboard skip links, native disclosures and navigation.
Full-page screenshots are compared within the same browser run (no fragile
platform-dependent baseline files).

For cross-generator CMS output, supply independently built landing pages from
the portable CMS parity implementation (PR #444) and their actual mount paths:

```sh
python3 -m tests.static_site_visual_browser --cms-only \
  --cms-site Hugo /tmp/hugo-output /syntyr-hugo/ \
  --cms-site Eleventy examples/eleventy/_site /syntyr-eleventy/ \
  --cms-site Astro examples/astro-keystatic/dist /syntyr-astro-keystatic/
```

The comparison uses the existing Python CMS renderer as the reference. At
least two independent output directories are required for CMS comparison.
Set `SYNTYR_CHROMIUM_EXECUTABLE` to an already installed browser if needed.
These are visual and native-interaction smoke tests, not accessibility
conformance certification.
