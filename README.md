# SYNTYR CSS

**Experimental v0.3.0-alpha.5 (unreleased candidate)** — framework-neutral, low-dependency, CSS-first styling for modern SaaS apps, professional business websites and optional cinematic Grid/Noir designs.

## Quick start — published alpha.4

Copy the HTML below into `index.html` and open it in a browser. It uses the
**published, immutable alpha.4 CSS** from the versioned site; **alpha.5 remains
unreleased**. The example needs no JavaScript, build tool, or app framework.

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Syntyr first page</title>
  <link rel="stylesheet" href="https://syntyr-css.pages.dev/v/0.3.0-alpha.4/syntyr.core.css">
</head>
<body>
  <main class="syn-root syn-shell" data-syn-theme="studio">
    <section class="syn-panel" aria-labelledby="overview-title">
      <h1 id="overview-title" class="syn-heading">Project overview</h1>
      <p class="syn-muted">A readable interface using ordinary HTML and one stylesheet.</p>
      <a class="syn-button syn-button--primary" href="https://syntyr-css.pages.dev/docs/">
        Browse components
      </a>
    </section>
  </main>
</body>
</html>
```

For production, **self-host the same pinned release** rather than depending on
a public CDN. From the directory containing `index.html`:

```sh
curl -fsSLo syntyr.core.css https://syntyr-css.pages.dev/v/0.3.0-alpha.4/syntyr.core.css
```

Replace the stylesheet reference in the HTML with `href="./syntyr.core.css"`.
The page's styles then work without a network connection; its documentation
link still points online. For the **unreleased alpha.5 source candidate**,
see [the single-file semantic starter](examples/semantic-starter.html) and
[distribution guide](docs/distribution.md). Do not mix alpha.4 and alpha.5
stylesheets.

- **The `syn-` class, CSS token, and HTML data-attribute namespace is the public API.**
- **0 JavaScript / 0 runtime dependencies / 0 network assets.** Works with server-rendered HTML, React, HTMX, Go templates, Astro, and other HTML renderers.
- **Compositional layouts:** native container-query responsive telemetry, empty states and pricing layouts. State styles use ARIA when semantic and data attributes otherwise.
- **Modern, plain CSS.** Native HTML primitives, cascade layers, color-mix, responsive Grid, accessible contrast targets and scoped theme tokens.
- **Neutral Studio palette by default:** opt into Grid, Noir, Industrial, Terminal, Corporate, or Minimal with `data-syn-theme`. Seven palettes are in the unreleased alpha.5 candidate; published alpha.4 provides Grid, Noir, and Studio.
- **Quiet component surfaces by default:** use `.syn-surface--accent` from optional recipes and `.syn-badge--accent` for deliberate visual emphasis.
- **Independent visual intensity:** optional `data-syn-intensity="quiet|standard|cinematic"` controls decorative effects without changing the theme, component semantics or runtime JavaScript contract.
- **Two modes:** explicit component classes, and a Pico-like *optional* `.syn-semantic` mode.
- **Modular:** separate core, semantic and decorative effects files; includes convenience bundles.
- **Optional website animations (alpha.5 source):** fade, slide, zoom and emphasis presets with finite/infinite loop controls and a native Web Animations API helper ([guide](docs/animation.md)).
- **Real navigation and loading states:** semantic breadcrumbs, touch-friendly page links, and static accessible skeleton placeholders.
- **No installation:** copy prebuilt CSS. Python 3 is used only by maintainers to regenerate it.
- **Visual page starters + offline images (alpha.5 source):** four editable complete-site starting layouts (portfolio, agency, SaaS, local business); replace original gallery examples with local PNG/JPEG/WebP photos and export a self-contained static ZIP without JavaScript. Editor JSON retains photos. [Builder](docs/page-builder.html).
- **Static page composition (alpha.5 source):** browse and rearrange all 91 copy-owned sections in the optional visual builder, then download a self-hostable HTML/CSS/image ZIP without application JavaScript. Backend forms remain host-owned. [Builder](docs/page-builder.html).
- **Opt-in universal registry (alpha.5 source):** 91 copy-owned HTML blocks plus 9 CSS modules in shadcn-compatible static JSON; no consumer runtime dependency. See [blocks guide](docs/blocks-guide.md).

## Live gallery and installation

- [Live website on Cloudflare](https://syntyr-css.pages.dev/)
- [Tailwind alternative decision guide](docs/tailwind-alternative.html): honest tradeoffs against Tailwind v4 and plain CSS, free SaaS demos, and HTML-first adoption guidance.
- [Server-rendered validation states](examples/form-state-contracts.html) and [dependency-aware, collision-safe local registry planner](docs/blocks-guide.md) (unreleased alpha.5 candidate).
- [Native enterprise data table example](examples/data-tables.html) and [accessible table guide](docs/data-tables.html)
- [Design resources directory](https://syntyr-css.pages.dev/docs/design-resources.html): curated galleries, design systems, accessibility, typography, motion and Syntyr study priorities.
- [Component gallery](https://syntyr-css.pages.dev/docs/)
- [Common HTML and UI example](examples/common-ui.html): navigation links, avatars, chips, list groups, notices and native form controls; no JavaScript
- [SaaS settings and billing showcase](examples/settings-billing.html): original three-level navigation, annual/monthly price comparison, current-plan states, and responsive billing workspace; static illustrative data, no JavaScript or live subscription actions
- [Native HTML elements demo](examples/native-elements.html): lists, code, media, forms, progress, and native overlays with optional semantic CSS
- [91 copy-owned blocks, 12 CSS textures, 6 typography directions, and 150 SVG icons](https://syntyr-css.pages.dev/docs/blocks.html) ([authoring guide](docs/blocks-guide.md))
- [Practical installation, integration and performance guides](https://syntyr-css.pages.dev/docs/guides.html)
- [Task-based How-To tutorials](docs/how-to.html): search 10 native HTML workflows and edit 20 existing MIT blocks in the sandboxed CodeMirror playground (unreleased alpha.5 source candidate)
- [Searchable, copyable component catalog](docs/catalog.html) with theme and width previews; [generated, portable gallery manifest](metadata/component-gallery.v1.json) for visual builders
- [Media & Entertainment collection](docs/media-entertainment.md) and [original CSS-only example](examples/media-entertainment.html)
- [Shared design principles, component-state matrix and native composition patterns](docs/design-principles.md) ([dependency-free 84-pair contrast audit](scripts/design_conformance.py)).
- [Canonical DESIGN.md contract](DESIGN.md): Google-compatible Studio tokens generated from CSS, component states, accessibility rules, and AI implementation guidance ([sync/check tool](scripts/sync_design_md.py)).
- [AI / coding agent quickstart](docs/ai-quickstart.md) and [agent integration guide](docs/agent-integration.md) (includes optional offline `init`/`check` CLI for portable consumer Skills and version-pinned HTML validation)
- [LLM documentation index](llms.txt), [full public reference](llms-full.txt), and [validated curated component manifest](metadata/components.json)
- [Optional local read-only MCP server](agent_mcp/README.md) (separate Python SDK, no CSS runtime dependency)
- [Portable Syntyr consumer Agent Skill](agents/syntyr/SKILL.md) (manual opt-in, not automatically installed); read-only project inventory via `python3 scripts/syntyr_agent.py info --project /path/to/app --json`
- [Per-component CSS imports and native HTML patterns](docs/native-patterns.md), [static demo](examples/native-recipes.html)
- [Optional keyboard command launcher](examples/command-launcher.html): existing command-panel CSS with native dialog, safe filtering, Ctrl/⌘ + K, and a script-free destination list (alpha.5 source candidate).
- [Native interaction recipes](https://syntyr-css.pages.dev/examples/native-interactions.html): exclusive accordions, GET search, dialog confirmations, datalist, meter/output without application JavaScript
- [Intrinsic sidecar and cluster layouts](docs/composition-adoption.md), [zero-JS example](examples/composition-adoption.html): container-width wrapping and configurable alignment
- [Runnable Go + html/template + optional HTMX](examples/go-htmx/README.md): native GET fallback, escaped queries and tested HTML fragments
- [Runnable Go resource workbench](examples/go-resource-workbench/README.md): real server-side filtering, pagination, safe bulk previews and local-only POST edits with signed CSRF form tokens; zero frontend JavaScript
- [Optional headless interactions](docs/headless-interactions.md): accessible Radix menus/toasts and React Aria combobox source example; no core JavaScript dependency
- [Copy-owned form recipes](docs/component-recipes.md), [live form compositions](https://syntyr-css.pages.dev/examples/form-composition.html), and [optional Radix styling adapter](docs/radix-integration.md)
- [Form customizer](docs/form-builder.html): build, preview, and export progressively enhanced HTML forms with no JavaScript required on the published form
- [GitHub Pages mirror](https://dporkka.github.io/syntyr-css/)
- [Tagged GitHub releases](https://github.com/dporkka/syntyr-css/releases)
- [Architecture, API stability and low-entropy maintenance policy](ARCHITECTURE.md)
- [Contributing guide](https://github.com/dporkka/syntyr-css/blob/main/CONTRIBUTING.md) and [private security reporting policy](https://github.com/dporkka/syntyr-css/blob/main/SECURITY.md)
- [Public API and prerelease stability policy](docs/api-stability.md)
- [Dependency-free CSS distribution guide](docs/distribution.md)
- [Optional email UI components and semantic HTML demo](docs/email-components.md): signup, inbox, composition, preferences and verification with no runtime JS
- [Animated gradient wash and text accents](docs/animation.md#animated-gradient-wash-composable-css): optional CSS-only drift, underline and headline glint that respect motion preferences.
- [CSS-only block effects](docs/animation.md#website-block-effects-css-only): opt-in parallax backgrounds, scroll fades/slides/zoom, and hover image zoom with reduced-motion fallbacks.
- [Optional native animation companion](docs/animation.md) ([interactive example](examples/animation.html)): Web Animations API, stagger and viewport reveals, no animation dependency or change to the CSS-only default
- [Migrating from Pico.css: differences and practical steps](docs/from-pico.md)
- [Optional CSS-only npm package (unpublished alpha.5 candidate)](docs/package-managers.md)
- [Performance and design polish guide (no size gate)](docs/performance-and-polish.md)
- [Progressive loading and critical CSS decision guide](docs/progressive-loading.md) and [zero-JS performance-first example](examples/performance-first.html)
- [WordPress, Wix, Shopify, Webflow, Framer and CMS/site-builder installation](docs/site-builders.md) (13 platform-specific SEO guides, unlayered alpha.5 embed CSS, WordPress/Shopify source examples, and host-theme isolation fixture).
- [Framework-independent CMS starter (Sveltia CMS + Pages CMS)](examples/cms-starter/README.md): portable JSON blocks, native HTML/CSS renderer and optional Git-backed editors ([integration guide](docs/cms-integration.md)); experimental alpha.5 source.
- [Framework integrations: LiveView, Livewire, Hotwire/Turbo, HTMX, Go templ and frontend stacks](docs/framework-integrations.md)
- [Mobile integration: React Native / Expo native tokens, plus Flutter, SwiftUI, Compose and Ionic](docs/mobile-frameworks.md) (opt-in alpha.5 source adapter; no native CSS runtime)
- [Runnable Expo SDK 58 native test fixture](examples/expo-native-smoke/README.md) (native component tests, Android/iOS Metro exports; native simulator/device verification still required)
- [JSX and TSX with React, Preact and Solid: copy-owned recipes and verified builds](docs/jsx-tsx-integration.md)
- [Verified Node.js, React/Vite and Next.js App Router adoption fixtures](docs/node-react-next-integration.md) (experimental, unpublished React wrappers)
- [Framework-free native Custom Elements, Declarative Shadow DOM, and form-associated integration](https://github.com/dporkka/syntyr-css/tree/main/examples/web-components): native `HTMLElement`, lifecycle-safe events, accessibility, SSR preservation, and cross-engine browser tests; no application framework or Syntyr JavaScript package.
- [Lit / Web Components integration guide](docs/lit-integration.md), [opt-in runnable example](https://github.com/dporkka/syntyr-css/tree/main/examples/lit), and [component-authoring contract](docs/component-authoring.md) (includes optional React 19 and HTMX interoperability fixtures and isolated browser CI)
- [Runnable HTMX + Python local example](examples/htmx.html) (requires local demo server; not part of the static Cloudflare site)
- [Runnable Datastar + SSE + native GET fallback example](examples/datastar.html) (uses [localhost Python server](examples/datastar_server.py); not part of the static site)
- [Runnable Unpoly and Turbo browser integrations](examples/unpoly.html) ([Turbo fixture](examples/turbo.html), [local HTML server](examples/hypertext_server.py), [opt-in cross-browser test suite](tests/hypertext_browser.py))
- [Cloudflare static hosting and immutable CSS CDN releases](docs/cloudflare-hosting.md)
- [Performance validation protocol and measured CSS size baseline](docs/performance-validation.md)
- [Optional five-framework browser benchmark: Syntyr, plain CSS, Pure, Tailwind v4 and UnoCSS](docs/framework-performance.md)
- [Theme customization, component-local layout tokens, native states, and opt-in OKLCH mixing](docs/theme-customization.md)
- [Design research: Linear, Resend, and developer tooling](docs/design-research-linear-resend.md)
- [Premium CSS-only compositions](docs/premium-compositions.md) and [Studio/Grid/Noir live gallery](examples/premium-compositions.html): layered surfaces, detail inspector, command presentation, timeline, and showcase
- [Optional interactive theme editor (documentation-only JavaScript)](docs/theme-editor.html)
- [Optional framework-independent copy interaction](docs/clipboard.md): separate native ESM, no mandatory JS; [runnable HTML demo](examples/copy.html)
- [Interactive component playground — live prerelease preview](https://8cfcb0ce.syntyr-css.pages.dev/docs/playground.html) ([permanent site URL after merge](https://syntyr-css.pages.dev/docs/playground.html); [HTML source](docs/playground.html))
- [Agent-readable composition recipes with validated slots, variants and stylesheet requirements](docs/editor-integration.md#agent-ready-composition-recipes)
- [Editor autocomplete, full component contract, class/token namespace collision audit and optional static HTML diagnostics](docs/editor-integration.md) (`metadata/syntyr-contract.json`, `scripts/syntyr_check.py`)
- [Tailwind v4 interoperability, local VS Code extension, and Figma token exports](docs/ecosystem-integrations.md) (opt-in alpha.5 source adapters)
- [Static-site generators: Astro, Eleventy, Hugo, Jekyll, Zola and Next.js export](docs/static-site-generators.md) ([runnable Eleventy example](examples/eleventy/))
- [Runnable Tailwind v4, Astro and shadcn-token adoption projects](docs/adoption-starters.md) and [editable Figma component kit pilot](docs/figma-component-kit.md)
- [Opt-in shadcn/ui semantic token bridge](docs/shadcn-integration.md), [official CLI-generated React/Radix example](examples/syntyr-shadcn-react/), [Chromium visual regression](docs/visual-regression.md), and [release readiness](docs/release-readiness-ecosystem.md)
- [Accessibility and browser-matrix methodology](docs/accessibility.md)
- [Progressive enhancement, automatic color scheme and print styling](docs/progressive-enhancement.md)
- [Commercial Console Kit concept (not available for purchase)](docs/console-kit.html)
- [Public design-partner review issue (seeking 10 participants)](https://github.com/dporkka/syntyr-css/issues/3)
- [Preliminary SYNTYR brand-risk review (NOT clearance)](business/syntyr-trademark-screen.md)
- [Design-partner interview pilot (not yet recruited)](business/design-partner-pilot.md)
- [Free original Noir resource archive demo](examples/resources.html)
- [Seven-theme comparison gallery (unreleased)](examples/themes.html)
- [Design-system states and typography example](examples/design-states.html): semantic tokens, accessible control states, nested themes and compact density
- [Minimalist patterns demo (system palette, fluid type, intrinsic layouts and classless form)](examples/minimalist-patterns.html)
- [Single-file, Pico-style semantic starter (unreleased alpha.5)](examples/semantic-starter.html)
- [Alpha.5 integration and test evidence](RELEASE_CHECKS_ALPHA5.md)
- [Alpha.5 manual accessibility review checklist](docs/accessibility-alpha5-review.md)
- [Advanced frame and terminal lab](examples/geometry-terminal.html) with [geometry integration guide](docs/geometry-terminal.md) and [interactive geometry mixer](docs/playground.html#geometry-title)
- [Quiet / standard / cinematic intensity comparison](examples/intensity-geometry.html) with [composability guide](docs/visual-intensity.md): independent effect controls, composable frame accents, and nested presets without JavaScript
- [Optional SVG icons, Unicode markers and ASCII/box-drawing demo](examples/symbols.html) with [copy-paste guide](docs/symbols.md)
- [CSS-only geospatial schematic demo](examples/geo.html) and [renderer-neutral GIS styling guide](docs/geo.md): optional `syntyr.geo.css` map/list/inspector workspace, markers, legends, layers and attribution with no bundled map engine (unreleased source candidate)
- [Opt-in enterprise data-grid CSS module](docs/data-grid.md), with [static styling example](examples/data-grid.html): framework-neutral, no JavaScript, reusable ARIA states, density and aligned column primitives.
- [Seven-theme static visualization gallery](examples/viz.html) and [Syntyr Viz guide](docs/viz.md): charts, sparklines, bar lists, status trackers and heatmaps, no runtime JavaScript
- [Three flagship visual compositions](docs/visual-composition.md): [Studio operations](examples/flagship-studio.html), [Noir editorial](examples/flagship-noir.html), and [Grid control](examples/flagship-grid.html); original, static, zero-JavaScript showcases.
- [Free production-shaped operations console](examples/operations-console.html): responsive SaaS dashboard composed from existing CSS modules; no backend or runtime JS
- [Search, filtering, settings and pagination SaaS workflow demonstration](examples/saas-workflows.html): server-ready semantic HTML, static illustrative data, zero JavaScript
- [Role-permissions review matrix](examples/permission-matrix.html): accessible native checkbox/table composition for enterprise authorization UIs; local preview only, no real permissions or JavaScript
- [Workflow operations compositions](examples/workflow-operations.html): progress steps, expandable activity diagnostics, and human approval queue using existing Syntyr classes; no backend or JavaScript
- [Operation feedback and revision comparison recipes](examples/operation-revisions.html): five host-owned states and semantic before/after record values using the existing definition-list layout (unreleased alpha.5 source)
- [Native file lifecycle presentation](examples/file-lifecycle.html): file picker, queued/uploading/completed/failed snapshots, and host-owned upload boundaries (unreleased alpha.5 source)
- [Vertigo-inspired four-stage resource lifecycle reference](examples/vertigo-resource-workflow.html): schema-driven CRUD visual patterns (index, detail, editor, settings) with zero runtime JavaScript and disabled mutations.
- [Optional Vertigo admin styling demo](examples/vertigo-admin.html) and [integration guide](docs/vertigo-integration.md)
- [Optional Rust SaaS Foundation / Askama / HTMX integration guide](docs/rust-saas-integration.md)
- [Runnable Rust Axum / Askama dashboard starter](examples/rust-axum/README.md) — same-origin embedded CSS, real search and validation, no client JavaScript
- [Static vs Hugo vs Zola decision](docs/site-generator-decision.md) and [isolated Hugo preview](experiments/hugo/README.md)

The linked alpha.4 release is already published; it does not include the four additional palettes or the optional utilities module. These are in the unreleased alpha.5 source candidate.

Use the release ZIP, copy `dist/syntyr.core.css` into your static assets, and load it with a normal stylesheet link. The **unreleased alpha.5** ZIP candidate also includes `examples/saas.html`, a self-contained offline SaaS demo with relative CSS references (not included in the published alpha.4 archive). The candidate ZIP's interactive `examples/resizable-workspace.html`
requires a local HTTP server for its optional module: after extracting
the ZIP, change to `syntyr-css-<version>`, run
`python3 -m http.server 8000 --bind 127.0.0.1`, and visit
`http://127.0.0.1:8000/examples/resizable-workspace.html`. Opening it
directly from `file://` preserves the static layout but browser security
can prevent interactive resizing. This example-specific JavaScript is
not part of the Syntyr CSS runtime.

No NPM, JS or build step is needed in an application. For package-manager projects, an optional CSS-only `@syntyr/css` manifest is now prepared for an **unpublished** alpha.5 candidate; [test it locally](docs/package-managers.md) until registry ownership and release approval are confirmed. No package installation is required by Syntyr itself.

## Documentation for humans and AI agents

- **For humans:** [browse every guide as HTML](https://syntyr-css.pages.dev/docs/reference.html), or start with [practical walkthroughs](https://syntyr-css.pages.dev/docs/guides.html). All publicly approved Markdown guides have readable, navigable HTML counterparts; links on the site prefer HTML.
- **For LLMs and coding agents:** retrieve [llms.txt](https://syntyr-css.pages.dev/llms.txt) to discover the public Markdown guides, or use [llms-full.txt](https://syntyr-css.pages.dev/llms-full.txt) as one curated source. Raw Markdown is publicly accessible, but intentionally excluded from human search indexing. Do not rely on crawler detection or user-agent-specific content.

Maintain one authored Markdown source per guide. After changing approved public Markdown, regenerate the committed HTML:

```sh
python3 -m pip install -r requirements-docs.txt  # maintainers only
python3 scripts/build_doc_pages.py
python3 scripts/build_doc_pages.py --check
```

The authoring dependency does **not** ship to consumers or run during the static-site build. CI's stdlib-only tests verify that HTML source hashes match the public Markdown allowlist. See the [agent documentation integration contract](docs/agent-integration.md).

## Source checkout demos and experimental modes

For the unreleased alpha.5 source checkout, open [docs/index.html](docs/index.html) in a browser. Try the [SaaS dashboard](examples/saas.html), [enterprise compositions](examples/enterprise-compositions.html), [business website](examples/business.html), [browser terminal](examples/terminal.html), [Grid console](examples/console.html), [Noir landing page](examples/landing.html), or [Noir pricing demo](examples/pricing.html). The gallery needs no server, Node, NPM, runtime JS or remote fonts.

```html
<link rel="stylesheet" href="syntyr.core.css">
<section class="syn-root" data-syn-theme="grid">
  <article class="syn-panel syn-panel--cut">
    <span class="syn-badge">SYSTEM ONLINE</span>
    <h2 class="syn-heading">Command Center</h2>
    <button class="syn-button syn-button--primary">Execute</button>
  </article>
</section>
```

For a **one-file Pico-style setup** in the unreleased alpha.5 source candidate, copy `dist/syntyr.semantic-bundle.css` and [open the live-source starter](examples/semantic-starter.html):

```html
<link rel="stylesheet" href="syntyr.semantic-bundle.css">
<main class="syn-root syn-semantic" data-syn-theme="studio">
  <article><h1>Project settings</h1><button type="button">Continue</button></article>
</main>
```

This is intentionally scoped: the `syn-root syn-semantic` opt-in is still required, unlike Pico's global classless default. This new bundle is **not** present in the published alpha.4 release. It includes the core and semantic styles; do not also load those separate files alongside it.

For a smaller two-file installation, add `syntyr.semantic.css` **after** core:

```html
<link rel="stylesheet" href="syntyr.core.css">
<link rel="stylesheet" href="syntyr.semantic.css">
<div class="syn-root syn-semantic" data-syn-theme="noir">
  <article>
    <label for="operator">Operator<input id="operator" required></label>
    <button>Continue</button>
  </article>
</div>
```

`syn-semantic` styles unclassed semantic elements inside that subtree. Add `data-syn-semantic` to an element that will receive transient framework classes (for example, HTMX's `htmx-request`) so its appearance survives updates. Elements outside the subtree are unaffected. Core component classes do not rely on semantic mode. Switch `data-syn-theme` among all seven palettes in the unreleased alpha.5 candidate, including nested themed areas.

## Standalone, low-maintenance CSS presets (alpha.5 source candidate)

Every preset is **one complete CSS file**: no `@import`, required JavaScript,
Sass, Node, remote fonts or package manager. Copy the CSS into static assets
and use semantic HTML in a scoped `.syn-root.syn-semantic` region. Themes stay
runtime-switchable through existing `data-syn-theme` tokens; there is no
per-theme stylesheet fork.

| Preset | File | Includes |
| --- | --- | --- |
| Minimal | `dist/presets/minimal.css` | Core + opt-in semantic HTML |
| SaaS | `dist/presets/saas.css` | Minimal + business/SaaS layouts, native recipes, server states, finite opt-in utilities |
| Cinematic | `dist/presets/cinematic.css` | Minimal + layouts, frames, symbols, optional visual effects and native motion |

```html
<link rel="stylesheet" href="/css/saas.css">
<main class="syn-root syn-semantic" data-syn-theme="studio">
  <article><h1>Account</h1><label for="email">Email</label><input id="email" type="email"></article>
</main>
```

Use **one** preset, not multiple presets or a preset plus its included
modules. The named presets are not in the published alpha.4 release. See
[distribution and optional selective optimization](docs/distribution.md),
[offline preset preview](examples/preset-preview.html), and the
[versioned CSS artifact contract](metadata/css-contract.v1.json). The
manifest schema version (`1`) does **not** imply Syntyr's CSS API has reached v1.
Development-only screenshots live in `tests/visual-baselines/presets/`.

## Build outputs

| File | Description |
| --- | --- |
| `dist/syntyr.core.css` | Tokens, scoped base, components (default choice) |
| `dist/components/*.css` | Individually importable tokens, base and component stylesheets |
| `dist/syntyr.semantic.css` | Optional semantic HTML styling (load after core) |
| `dist/syntyr.server.css` | Optional request-state presentation bridge for LiveView, Livewire 4, HTMX and Turbo (load after core) |
| `dist/syntyr.semantic-bundle.css` | Core + semantic in one file; scoped opt-in, alpha.5 source only |
| `dist/syntyr.effects.css` | Optional, static decorative effects |
| `dist/syntyr.motion.css` | Optional scroll progress, block parallax and reveal effects, image hover zoom, and overlay transitions |
| `dist/syntyr.geometry.css` | Optional bevel, notch, bracket, inset and circuit panel frames |
| `dist/syntyr.symbols.css` | Optional vendor-neutral SVG icons, Unicode symbols and text-art alignment |
| `dist/syntyr.viz.css` | Optional theme-aware data visualization styles, no chart renderer or JS |
| `dist/syntyr.recipes.css` | Optional SaaS, marketing and browser-terminal layouts |
| `dist/syntyr.native-recipes.css` | Optional floating labels, timelines and captioned code |
| `dist/syntyr.utilities.css` | Optional finite spacing, layout and visually hidden helpers |
| `dist/syntyr.print.css` | Optional printer-friendly reports and business documents |
| `terminal/palettes.json` | Color palettes for native ANSI terminal applications (not CSS) |
| `dist/syntyr.css` | Backwards-compatible core + effects bundle |
| `dist/syntyr.all.css` | All modules (semantic still opt-in by class) |

Grid/Studio system-aware `data-syn-theme="auto"` is built into the core stylesheet;
no separate automatic-theme file is required. The optional print sheet is
separate from core and included only in the all-in-one bundle.

Geometry, symbols, Viz and utilities are opt-in; neither the core bundle nor ordinary component selectors require them. The symbols module ships no SVG assets, icon fonts, glyph sets or runtime dependencies.

The source is split into `src/components/*.css`, `src/tokens.css`, `src/base.css`, `src/semantic.css`, `src/recipes.css`, `src/effects.css`, `src/motion.css`, `src/geometry.css`, `src/symbols.css`, `src/viz.css`, `src/print.css` and `src/utilities.css`. The optional utilities module uses a final dedicated `syn.utilities` cascade layer, and `scripts/build.py` is the single authoritative manifest of CSS distribution filenames. Check the [component and token contract](docs/components.md), [free composition recipes](docs/recipes.md), and [Tailwind/Tailwind Plus study](docs/tailwind-research.md).

## Modern SaaS, CLI and business websites

Use `data-syn-theme="studio"` for a neutral, professional light theme. Grid and Noir remain available. Themes control color and typography roles; optional `syn-frame--precision`, `syn-frame--industrial` and `syn-frame--soft` classes control visual geometry independently. Add `data-syn-density="compact"` to `.syn-root` or a nested region to tighten control heights, rows, and card padding without shrinking type.

For production-oriented examples, load `syntyr.core.css` **then** `syntyr.recipes.css` for responsive application shells (`syn-app-shell`), business landing layouts (`syn-site-hero`) and browser terminal panels (`syn-terminal`). Continue to use real headings, tables, labels, links and forms. The recipes provide layout and presentation, not authentication, data fetching, filtering or backend actions.

**Native CLI apps cannot consume CSS.** Instead, use `terminal/palettes.json` with Go, Rust, Python or another CLI implementation to define ANSI 16-color palettes and foreground/background preferences. See the [stdlib Python demonstration](examples/ansi_cli.py) and [integration guide](docs/saas-cli-business.md). Respect `NO_COLOR`, TTY detection and user terminal preferences.

All additions are MIT licensed and do not change the core runtime dependency contract. The Studio theme, recipes and CLI palettes are included in the v0.3.0-alpha.4 release.

For dropdowns and native selects, see the [dropdown patterns guide](docs/dropdowns.md) and [scriptless interactive example](examples/dropdowns.html). Action panels stay JavaScript-free; an optional, explicitly initialized ARIA menu adapter is available as `@syntyr/css/menu.mjs` for applications needing arrow-key navigation.

For native platform integration, see the [browser API compatibility and progressive enhancement guide](docs/native-browser-apis.md) and the [script-free native API demo](examples/native-apis.html). The core stays JavaScript-free; native CSS anchors and content-sized textareas are opt-in, and scroll-progress / overlay transitions live in the dedicated motion module.

## Development and verification

```sh
python3 scripts/build.py
python3 scripts/build.py --check
python3 scripts/export_api_metadata.py --check # editor metadata stays in sync
python3 scripts/asset_report.py # informational raw/gzip sizes, no hard ceiling
python3 -m unittest discover -s tests -v
python3 scripts/package_release.py
```

Browser checks and the synthetic performance benchmark use Playwright (a **dev-only optional tool**) and run with:

```sh
python3 tests/browser_test.py
python3 tests/browser_matrix.py --browsers chromium firefox webkit
python3 tests/reflow_test.py --browsers chromium firefox webkit # enlarged-text reflow stress check
python3 tests/progressive_browser.py --browsers chromium firefox webkit # opt-in auto/print/scoping behavior
python3 tests/axe_audit.py --axe-file /tmp/axe.min.js # dev-only checker; see docs/accessibility.md
python3 tests/theme_editor_browser.py # optional docs-only editor browser checks
python3 scripts/perf_benchmark.py --browsers chromium,firefox,webkit --runs 3 --rows 1200 --sections 12 # local synthetic performance
```

The browser scripts require developer-installed `playwright` and the browser engines selected for testing; Chromium is autodetected from `chromium` or `chromium-browser`, or may be set with `PLAYWRIGHT_CHROMIUM_EXECUTABLE`. The benchmark records unavailable browsers as blocked. Consumers of the CSS do **not** require Playwright or browser automation. This project intentionally avoids adding a package manager or dependency manager to the runtime/library.

### Verifying PR merge candidates (maintainers only)

The optional Woodpecker `pr-merge` pipeline fetches the current `main` and tests
an **isolated combined working tree** instead of validating the PR head alone.
To reproduce locally from your feature branch:

```sh
git fetch --no-tags origin main
python3 scripts/check_merge_candidate.py --base FETCH_HEAD
```

The test checks CSS, editor API metadata, consolidated agent documentation,
Python contracts, Cloudflare allowlisted assets, and release packaging. It
leaves the source branch unchanged and requires only Python 3 and Git.

**Race boundary:** A passing check proves compatibility with the specific
base SHA it fetched. It does not protect against another PR landing afterward.
To prevent stale generated artifacts from reaching `main`, require the
merge-candidate Woodpecker check on the **current base** through branch rules
or a merge queue, and verify the actual main push is green. The workflow YAML
alone does not prove a Woodpecker pipeline has executed; do not assume it is
an enforced required check until the GitHub/CI integration is verified.

## Important boundaries

- This is a **CSS library**, not a JS widget framework. Native `dialog`, `[popover]` and `details` provide native interaction in supported browsers. The HTML Invoker Commands API used to open modal dialogs is not supported in every older browser. Use progressive enhancement for critical interactions.
- No custom combobox, tabs, virtualized tables, or fake ARIA widgets. Advanced widgets can be built separately without coupling them to the visual system.
- Accessibility and cross-browser compatibility require more verification before a production v1.0 release. Test real applications at 200% and 400% zoom and with screen readers.
- Runtime zero dependencies does not mean zero maintainer/tooling dependencies. The standard library build script is deliberately small, and Playwright is only used for optional tests.
- The `syn-root` scope works for compact embedded sections. `body.syn-root` gets full viewport height, or add `.syn-page` explicitly when needed.

## Roadmap

v0.2-alpha: free console + landing demos, accessible form-error styles, button variants, independent page/embedded scopes. v0.3-alpha: portable container-query recipes, attribute state styling, pricing example and Tailwind/Plus architectural study. v0.4: docs/theme editor; v1: stability + expanded browser/accessibility validation. Performance: raw/gzip sizes are reported per distributable, not bounded by arbitrary byte ceilings; runtime JS remains 0 bytes. Browser behavior and modular loading matter more than a fixed compressed-size target.

## Provenance and license

This implementation is original MIT-licensed code; it has not imported or ported any Pico, Chota, Open Props or other third-party source. Those libraries are design/architecture research references only. Any future code borrowing must retain necessary copyright and license notices in `THIRD_PARTY_NOTICES.md`.

See [LICENSE](LICENSE).


## Business model: open source stays open source

**The entire current repository (including core, themes, examples, docs and tests) is MIT-licensed.** The design system is not a crippled free tier. A future business can sell **separately authored premium page templates and design kits**, plus optional custom integrations. The premium template source, if created, would ship separately with a commercial license; any embedded MIT Syntyr core retains MIT rights.

- [Business strategy, product scope and price tests](business/strategy.md)
- [Proposed premium Console Kit scope (not on sale)](business/console-kit-spec.md)
- [Draft license boundary for *future* premium assets](business/premium-license-draft.md) — **not an operative contract**
- [Validation and go/no-go plan](business/validation-plan.md)
- [Console Kit buyer validation, pre-sale release gates and measured metrics](business/commercial-launch-gates.md)

No paid kit has been shipped or put up for sale in this repository. No billing or license-key code is included. The Grid and Noir visual themes are original, not officially affiliated with any entertainment franchise. **SYNTYR is the selected but not trademark-cleared name**, pending documented brand clearance. The preliminary risk screen is not authorization for paid branding.

## Additional native application screens

Five copy-owned [SaaS application screens](docs/app-screens.md) cover onboarding, team membership and invitations, notifications, integrations, and security. They are static HTML/CSS examples built from the existing core and recipes, with no required application JavaScript or live account actions.
