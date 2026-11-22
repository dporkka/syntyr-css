# Syntyr Blocks & Assets — integration guide

**Status:** Experimental alpha.5 source gallery, not an immutable release or published npm package.

[Browse 68 blocks](blocks.html) | [Component catalog](catalog.html) | [Themes](theme-customization.md) | [Accessibility](accessibility.md)

## Contract

The 68 copy-owned HTML compositions cover marketing, application, services, portfolio, editorial, navigation, publishing, commerce and technical use
cases. Each contains its own Syntyr root, uses accessible native markup and requires
no application JavaScript. The data, testimonials and prices are illustrative, not live.

The gallery script powers optional documentation search, theme switching and copy
buttons. Disable JavaScript and all 68 static previews remain visible, with
selectable source under native disclosure elements. No scripts are included in
application CSS, and the core Syntyr build is unchanged.

## Safe local registry installation (experimental alpha.5 source)

The static [universal registry](../registry/registry.json) contains the 68 MIT
HTML blocks and nine CSS module entries. Every item includes its exact
source-tree version, SHA-256 content hashes, declared CSS dependencies, files,
and destination paths. This is **not** a published immutable alpha.5 release.

A no-network, optional Python standard-library helper can preview a block's
complete dependency plan (the core CSS, any optional modules, the HTML file and
one MIT license notice) without modifying a project:

~~~sh
python3 scripts/registry_install.py resource-workspace --project /path/to/app
# After reviewing every path/digest, opt in to copying missing files only:
python3 scripts/registry_install.py resource-workspace --project /path/to/app --apply
~~~

The script refuses incompatible versions, mismatched hashes, untrusted
registry URLs, unsafe/symlinked paths, and changed existing files. It never
executes installed markup or installs JavaScript dependencies. Re-running an
identical installation is safe. The helper intentionally does **not** offer
a force-overwrite mode; manage customization and upgrades through your own
source control. Syntyr still works by copying a prebuilt CSS file directly,
without Python in the consuming application.

For reproducible developer-only checks (without shipping a browser runtime),
run `node tests/registry_form_workflows_browser.cjs` with
`SYNTYR_PLAYWRIGHT_MODULE` pointing to an installed Playwright package and
optionally `SYNTYR_CHROME_BIN` pointing to Chromium. The checks verify real
computed component token styles and the form/workflow gallery at 320, 390
and 1280 CSS pixels, plus browser-emulated forced colors. These do not replace
manual keyboard, screen-reader or actual browser zoom review.

The three complete application compositions in this source candidate are:
`resource-workspace` (GET search and records),
`crm-workspace` (accessible, keyboard-scrollable pipeline), and
`billing-workspace` (server-owned billing contact and invoices). They
contain **illustrative data and placeholder host routes**. Their host
application must supply authorization, data queries, CSRF protection,
validation and persistence. See [form state contracts](component-recipes.md).

## SaaS and business collection (experimental alpha.5 source)

Twelve additional copy-owned compositions expand the collection from 56 to 68:
six marketing sections (scrollable card rail, bento features, product preview hero,
split feature detail spotlight, full example case study, pricing comparison) and six SaaS
workspaces (sign-up, resource management, workspace invitations, billing usage,
integration connection states, API keys and webhooks).

For generic horizontal collections, load `syntyr.recipes.css` and use
`syn-scroll-rail` on a named, focusable `role="region"` wrapper. Each direct
child is an independent card. Customize `--syn-scroll-rail-card-width` and
`--syn-scroll-rail-gap` locally. Native overflow and scroll snapping work
without JavaScript; this does **not** add carousel buttons, autoplay or a new
interaction runtime. The existing `syn-media-rail` remains unchanged and
better suited to media/poster catalogs.

For asymmetric feature cards, use `syn-bento-grid` and opt-in
`syn-bento-card--wide` on an individual card. The grid's own container width
determines when a wide card may span two columns. The previous `syn-grid`
and `syn-feature-grid` remain available for equal-size cards. Reuse
`syn-showcase` for split product storytelling rather than creating another
split-layout API.

Dense four-column tables in the SaaS screen examples opt into
`syn-table--readable`. Place them inside an existing named, keyboard-focusable
`syn-table-wrap` and customize `--syn-table-readable-min` (default 38rem) to
preserve readable columns while allowing local horizontal scrolling.

All example names, plan details, statuses and usage metrics are illustrative.
Registration, authorization, invites, persistence, CSRF protection, OAuth,
billing, webhook security and API key issuance are **host application** responsibilities.
Replace example routes and sample data before deploying.

## Native HTML and framework integration

Load the specific CSS modules shown on each block, from the same pinned version.
For example, blocks using both core and recipes:

~~~html
<link rel="stylesheet" href="/css/syntyr.core.css">
<link rel="stylesheet" href="/css/syntyr.recipes.css">
<!-- Paste a copied HTML block here. -->
~~~

Do not load all.css alongside individual CSS files. Most snippets have their own
root class and default Studio theme. If the application already has a Syntyr root,
you may remove a redundant nested root while retaining the necessary theme scope.

Three supported approaches:

1. **Server HTML / Go templ / Django / PHP / Rust Askama:** Paste snippets into
   templates and bind actual data and routes, with server-side escaping,
   authorization, CSRF protection for writes, and validation.
2. **HTMX / Datastar:** Keep native forms, links and server fallbacks working.
   Add progressive enhancement attributes only in the application; Syntyr
   does not bundle those JavaScript libraries.
3. **React / Astro / Vue / Svelte:** Convert HTML syntax where required, e.g.
   class to className and for to htmlFor in JSX. Bind interactive state and
   event handlers in the host app, not in Syntyr.

Routes like /settings and /checkout/team are example host-app routes. Replace
them before using in production. Static samples do not implement authentication,
filtering, payments, sorting, persistence or actual monitoring.

## Optional scroll, parallax, and hover effects

Any copied block can opt into decorative animation by loading
[syntyr.motion.css](animation.md#website-block-effects-css-only) alongside its
existing CSS. Add `data-syn-scroll="rise"` or `data-syn-scroll="fade"` directly
to a heading or card in its original HTML; do not clone the block to create
an animation variant. A decorative background can use `data-syn-parallax`
with a separate media layer, and image tiles can use `data-syn-hover="zoom"`.

These are CSS-first progressive enhancements: unsupported browser versions
and users requesting reduced motion retain visible, static content. See the
[block effects guide and examples](animation.md#website-block-effects-css-only)
and the [live animation gallery](../examples/animation.html).

Use the existing static gradient wash with the optional motion module to
add a gentle animated background without inventing a new block variant.
`data-syn-gradient="drift"` works on `syn-gradient-wash` with a
`data-syn-gradient-content` foreground wrapper. Short editorial headings
may opt into `data-syn-text="underline"` or
`data-syn-text="glint"`. Motion and high-contrast fallbacks are explained
in the [animation guide](animation.md#animated-gradient-wash-composable-css).

## 12 original, optional CSS asset recipes

The complete source is [blocks-assets.css](blocks-assets.css). It includes:
fine-grid, dot-field, radar, ambient-glow, glass, blueprint, signal-stripes,
diagonal, beam, corners, horizon and circuit. The gallery displays all twelve.

The CSS is **docs-only** and outside Syntyr's core and all-in-one builds.
You may copy individual modifiers with their necessary base rules into your
application-owned stylesheet. It contains no images, external fonts, canvas,
JavaScript or network imports. Scanning beam animation respects reduced-motion
preferences, and effects disable in forced-colors mode.

Existing Syntyr geometry and effects modules should be the default choice when
they already provide the desired result.

## Six font recipes and 150 original SVG icons

Six system-font typography directions are displayed in the gallery:
Studio sans, Editorial serif, Terminal mono, Technical sans, Reading serif
and Compact system. They do not bundle or download font files. Customize
CSS tokens for UI, display and monospace type, preserving readable fallbacks.

The gallery now provides 150 original, copyable inline SVG examples using
Syntyr's existing generic icon sizing contract. These are not a dependency,
icon font or stand-alone icon runtime. You may also use appropriately licensed
provider packs such as Lucide, Tabler and Heroicons; none are vendored here. Icon-only controls need accessible
names. Icons can optionally use 14 no-JavaScript animation presets, with
hover/focus activation and reduced-motion support. See [symbols](symbols.md)
for supported integration patterns.

## Source, build and maintenance

Editable fragments live in the blocks/snippets directory. Metadata and module
dependencies live in blocks/manifest.json. The gallery is generated, not hand
edited, by the Python standard-library script:

~~~sh
python3 scripts/build_blocks.py
python3 scripts/build_blocks.py --check
python3 -m unittest discover -s tests -p test_blocks_assets.py -v
python3 -m unittest discover -s tests -v

# Optional developer-only browser checks (Playwright plus browser engines):
python tests/blocks_browser.py --browsers chromium firefox webkit --axe-file /tmp/axe.min.js
~~~

Only the rendered gallery and its reviewed documentation assets are publicly
allowlisted by Cloudflare; raw authoring files are not published.

## Accessibility, fidelity and licensing

Test all adapted blocks with keyboard-only navigation, mobile widths, 200% and
400% zoom, forced colors and an actual screen reader. Check contrast with the
real application theme. Do not announce static sample status as live system
state or retain fabricated customer endorsements in production.

All new snippets, original CSS assets and documentation are MIT licensed.
No premium Tailwind, commercial UI kit or third-party icon artwork has been
copied into the public project. The separate private Console Kit is unaffected.

## Experimental shadcn universal-item registry

The source candidate can generate a **copy-owned, framework-independent**
shadcn-compatible universal-item registry from the same 68 MIT blocks and
checked-in CSS distributions. It neither replaces nor duplicates the native
block installer from PR #104. Universal files use explicit project-relative
targets, so no React, Tailwind, or Syntyr runtime JavaScript is required.

```sh
python3 scripts/build.py --check
python3 scripts/build_shadcn_registry.py       # generate registry/registry.json and registry/r/*
python3 scripts/build_shadcn_registry.py --check
# Optional, developer-only shadcn 4.23.0 integration smoke (requires npm):
python3 tests/shadcn_registry_cli_smoke.py --package shadcn@4.23.0
```

Each `registry/r/<block-id>.json` contains the source HTML at
`~/syntyr/blocks/<block-id>.html` and absolute same-origin registry dependencies for
the required stylesheets at `~/syntyr/css/`. Each registry item also installs
the original MIT `LICENSE` at `~/syntyr/LICENSE`. Install in an existing project
only after reviewing the exact files, license and project configuration. For
example, **after publishing the reviewed candidate site**, a shadcn CLI may
consume `https://syntyr-css.pages.dev/registry/r/faq.json`. This is a
candidate endpoint, not a claim that it is currently deployed. The independent
local-mirror smoke verifies that CLI 4.23.0 can install both core-only and
core-plus-recipes blocks without a consumer package.json or runtime dependencies.

The generated index is intended for editor/agent inspection. The generator
never reads private Console Kit assets or executes downloaded code. No dynamic
service, telemetry, npm dependency, or customer license is introduced.
Published alpha.4 assets remain immutable; registry payloads declare their
source-candidate Syntyr version and must not be confused with a tagged release.
