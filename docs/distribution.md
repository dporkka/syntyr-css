# Syntyr CSS distribution

Syntyr CSS is MIT-licensed. No NPM install, JavaScript runtime, fonts,
icons, Sass compiler or CSS framework is required to use the distributed CSS.

## Your first five minutes (published alpha.4)

Start with a small project overview that works without application JavaScript.
These steps use only the immutable published alpha.4 core CSS, not source-candidate classes.

### 1. Download the CSS

Create a directory named `syntyr-demo`. Save the [pinned core stylesheet](https://syntyr-css.pages.dev/v/0.3.0-alpha.4/syntyr.core.css)
as `syntyr.core.css` inside it. Alternatively, from a terminal:

```sh
mkdir -p syntyr-demo
cd syntyr-demo
curl -fsSLo syntyr.core.css https://syntyr-css.pages.dev/v/0.3.0-alpha.4/syntyr.core.css
```

### 2. Create index.html

Save this complete file alongside the stylesheet:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Project overview</title>
  <link rel="stylesheet" href="./syntyr.core.css">
</head>
<body class="syn-root syn-page" data-syn-theme="studio">
  <main class="syn-shell">
    <section class="syn-panel" aria-labelledby="project-title">
      <h1 id="project-title" class="syn-heading">Project overview</h1>
      <p class="syn-muted">Your first Syntyr interface.</p>
      <details>
        <summary>Project details</summary>
        <p>This disclosure uses native HTML, not a widget runtime.</p>
      </details>
      <p><a class="syn-button syn-button--primary" href="#next">Next steps</a></p>
    </section>
    <section id="next">
      <h2>Next steps</h2>
      <p>Replace this sample content with your own.</p>
    </section>
  </main>
</body>
</html>
```

### 3. Open and try it

Open `index.html` in a modern browser. The layout and native disclosure
work offline. Activate the disclosure and the link with the keyboard.
The link navigates to a real section on the page.

### 4. Change the theme and check the viewport

Change `data-syn-theme="studio"` to `grid` or `noir` and reload.
The markup stays the same. Resize to a narrow window and check text wrapping
and keyboard focus. These checks are a first step, not an accessibility audit.

### 5. Adopt one real screen

Copy the same pinned stylesheet into your application's public assets,
choose one isolated `syn-root` region, and use real native links and forms
connected to your application. Read the [component reference](components.md)
and [integration guide](framework-integrations.md); check that any added
classes exist in the alpha.4 stylesheet before using them.

The [live component catalog](catalog.html) also includes unreleased
alpha.5 examples; do not assume every catalog pattern is available in alpha.4.

## Recommended: self-host a versioned stylesheet

1. Download the asset from the [GitHub release](https://github.com/dporkka/syntyr-css/releases/tag/v0.3.0-alpha.4), or copy the matching file from the tag.
2. Put `syntyr.core.css` in your application's static CSS directory.
3. Load it normally:

```html
<link rel="stylesheet" href="/css/syntyr.core.css">
<section class="syn-root" data-syn-theme="grid">
  <button class="syn-button syn-button--primary">Initialize</button>
</section>
```

The stylesheet's path is *your* path; mount or copy the file there.
The above works with Go templates, plain HTML, Astro, HTMX, React and other
renderers. See [the framework integration guide](framework-integrations.md) for
HTMX request-state classes, optional semantic markers, and server-side fragments. Add `syn-page` to the root only if you want full-page min-height.

## Embed inside an existing CMS theme (unreleased alpha.5)

The alpha.5 source builds a separate `dist/syntyr.embed.css` entrypoint
from the canonical core CSS, removing its outer CSS cascade layers to avoid
the normal layered-versus-unlayered theme-precedence trap. Load it **instead
of** `syntyr.core.css` for self-hosted Syntyr sections on WordPress, Shopify,
Webflow or similar themes. This file is not in published alpha.4 releases;
the CSS still uses the same `.syn-root` namespace and no runtime JavaScript.
See the [site-builder integration guide](site-builders.md) for platform limits
and copyable snippets.

## Offline SaaS preview in the next release ZIP (unreleased alpha.5)

The alpha.5 source candidate now packages `examples/saas.html` together with
`dist/syntyr.core.css` and `dist/syntyr.recipes.css`. After building or
extracting the **alpha.5** ZIP, open `examples/saas.html` directly in your
browser. Its relative stylesheets resolve within the extracted archive, so it
requires **no internet connection, local server, npm, build step or runtime
JavaScript**. You can edit the HTML and CSS locally to test integration.

This is a static **illustrative SaaS dashboard**: fictional metrics, no real
account data, authentication, filtering, API calls, or backend actions. To use
it in an application, replace sample values with server-rendered data and wire
navigation and mutations to your own server. The already published **alpha.4**
release does *not* contain this packaged example; the next alpha.5 release
has not been published yet.

## Command launcher ZIP example (unreleased alpha.5)

The optional command launcher example points to three standalone HTML
examples included in the release ZIP: the preset preview, native resource
outline, and SaaS dashboard. Both the script-free navigation and enhanced
native-dialog links resolve without fetching any unbundled docs assets.

For the interactive Ctrl/Command+K module, serve the extracted alpha.5
release directory over local HTTP, as explained for the resizable workspace
above. From the extracted ZIP's top-level folder, run:

    python3 -m http.server 8000 --bind 127.0.0.1

Open http://127.0.0.1:8000/examples/command-launcher.html.
The native navigation stays usable without JavaScript on a file:// URL, but
the optional module may be blocked by browser file-origin restrictions.
No server is necessary for the static examples/saas.html preview.

## One-file semantic starter (unreleased alpha.5 source)

For a Pico-like HTML workflow, `dist/syntyr.semantic-bundle.css` combines core and semantic CSS into a single file. Copy it to your static assets, then opt in on the region you want styled:

```html
<link rel="stylesheet" href="/css/syntyr.semantic-bundle.css">
<body class="syn-root syn-page syn-semantic" data-syn-theme="studio">
  <main class="syn-shell">
    <article><h1>Dashboard</h1><button type="button">Open</button></article>
  </main>
</body>
```

Only the controls and elements inside `.syn-root.syn-semantic` are styled semantically. This is **not** Pico's globally classless behavior: the root scope is deliberate. No script or build tool is required. [See the runnable starter](../examples/semantic-starter.html) and the [Pico migration guide](from-pico.md). **This file is not in the published alpha.4 release** and its `/dist/` URL is not an immutable release asset; pin a released version once alpha.5 is actually published. Do not load `core.css` or `semantic.css` alongside this bundle.

## Single-file presets (experimental alpha.5 source)

Choose one self-contained file and self-host it. There are **no stylesheet
imports or runtime dependencies**. Each preset includes tokens, core components,
and scoped opt-in semantic HTML styling:

| Preset | Distribution | When to choose |
| --- | --- | --- |
| Minimal | `dist/presets/minimal.css` | Documentation, forms and simple websites |
| SaaS | `dist/presets/saas.css` | Business sites, dashboards, HTMX/server-rendered apps; explicit `syn-u-*` helpers |
| Cinematic | `dist/presets/cinematic.css` | Optional Grid/Noir effects, precision frames, native CSS motion |

```html
<link rel="stylesheet" href="/css/syntyr-saas.css">
<main class="syn-root syn-semantic" data-syn-theme="studio">
  <article><h1>Settings</h1><label for="email">Email</label>
    <input type="email" id="email" required>
    <button type="button">Preview</button>
  </article>
</main>
```

Only the path is application-defined; copy `dist/presets/saas.css` to match.
**Do not stack presets** or add core/semantic/recipes CSS already inside a
preset. Styles are still isolated to `.syn-root`, while bare element styling
requires `.syn-semantic`. Native dialogs/popovers/forms retain browser behavior;
Syntyr adds no component runtime. `data-syn-theme` and `--syn-*` custom
properties remain the theme API in every preset.

Advanced users can keep a single CSS output but omit unused core components
with the optional, stdlib-only `scripts/build_selective.py --components ...
--modules ... --output ...` build. That optimization is not a consumer
requirement and does **not** purge dynamic selectors or minify CSS.

`metadata/css-contract.v1.json` is a machine-readable, deterministic
**distribution artifact manifest**: it declares preset source order, file
names, raw/gzip bytes and SHA-256 hashes, together with the library version.
The `v1` suffix versions the **manifest schema**, not the public CSS API,
which remains experimental until an explicit v1 release. `build.py --check`
rejects stale CSS and contract manifests. See [CSS API stability](api-stability.md)
and [optional visual regression testing](visual-regression.md).

Try the [script-free preset demonstration](../examples/preset-preview.html).
This is present in the alpha.5 source candidate, **not published alpha.4**.

## Optional npm/package-manager distribution

A CSS-only `@syntyr/css` manifest is available in the alpha.5 repository candidate, but **it has not been published to npm**. See [package-manager installation and local tarball testing](package-managers.md) for supported imports and an explicit no-publication boundary. No package manager is required for the documented self-hosted stylesheet path.

## Optional native animation companion

Syntyr remains CSS-only by default. Applications that need *programmatic* motion
can separately import `dist/syntyr.animate.mjs` (native Web Animations API and
IntersectionObserver only). No script is included in core or `syntyr.all.css`.
See the [animation API guide](animation.md) and the
[runnable example](../examples/animation.html).

## Optional themes and semantic HTML

Grid, Noir and Studio ship in the **same** core stylesheet; set
`data-syn-theme="grid"` or `data-syn-theme="noir"` or `data-syn-theme="studio"` on the scoped root.
You can nest differently themed elements.

The unreleased alpha.5 candidate adds Industrial, Terminal, Corporate and Minimal using the same scoped `data-syn-theme` contract. The published alpha.4 release includes Grid, Noir and Studio only.

Load `syntyr.semantic.css` after core **only** if you want automatic semantic
element styles within `.syn-semantic`. For static glows and decorative grid
effects, load `syntyr.effects.css` after core. SaaS, business and terminal layouts
are opt-in via `syntyr.recipes.css`. Optional frame geometry is in `syntyr.geometry.css`.
The alpha.5 working tree additionally provides `syntyr.utilities.css` for finite
layout helpers and `syntyr.print.css` for print-friendly reports. System-aware
Grid/Studio `data-syn-theme="auto"` is already included in core CSS, with
no additional stylesheet or runtime JavaScript. See the
[progressive-enhancement guide](progressive-enhancement.md) for examples.
The optional source-candidate `syntyr.ascii.css` composes with symbols for [ASCII effects](ascii-effects.md); it is not in the published alpha.4 release.

The optional `syntyr.symbols.css` adds BYO-SVG icon sizing, literal Unicode styling and ASCII/box-drawing alignment without shipping fonts or icons; see [symbols and accessibility](symbols.md).

`syntyr.semantic-bundle.css` bundles core and semantic styles with scoped opt-in.
`syntyr.css` bundles core and effects. `syntyr.all.css` bundles all modules
while still requiring `.syn-semantic` to opt into semantic element styles.
Avoid loading these bundles alongside their component files: that duplicates CSS. Optional utilities live in the final `syn.utilities` cascade layer, allowing explicitly applied utility classes to override ordinary component declarations; see [the architecture policy](../ARCHITECTURE.md).

## Loading contract at a glance

| Goal | Stylesheet choice | Requirement |
| --- | --- | --- |
| Explicit components | `syntyr.core.css` | `.syn-root` wraps the component subtree |
| Plain semantic HTML | `syntyr.semantic-bundle.css` | Add `.syn-semantic` to the scoped root |
| Some components only | `components/tokens.css`, `components/base.css`, then selected component styles | Keep order; include `forms.css` with `form-composition.css` |
| Application recipes | `syntyr.core.css` followed by `syntyr.recipes.css` | Use explicitly named recipe classes |
| All features | `syntyr.all.css` | Never combine with the constituent files |

Avoid combining bundles with their constituent CSS. Each separately imported
component file intentionally has **no runtime `@import`**; load tokens and base
first. Use the [intrinsic composition guide](composition-adoption.md) to build
dashboard layouts without JavaScript or viewport-specific hacks.

## Optional explicit selective build

Applications needing fewer core components can assemble a custom CSS file with
the Python standard-library-only `scripts/build_selective.py`. It does not scan
templates or purge individual selectors, and does not alter published assets.
See [selective builds and their limits](selective-builds.md).

## Pinned CDN for prototyping

```html
<link rel="stylesheet"
      href="https://syntyr-css.pages.dev/v/0.3.0-alpha.4/syntyr.core.css">
```

The first-party Cloudflare CDN serves frozen, checksum-verified CSS releases
from a global edge network. Unversioned `/dist/` URLs can change with builds;
pin `/v/<version>/` instead. The documentation's optional theme editor
has JavaScript, but the library CSS and consumer sites do not require it.
For production applications, copying the versioned CSS to your own origin
usually avoids an additional hostname connection.

## Release artifacts and guarantees

The published alpha.4 release contains seven SYNTYR CSS distributions. The
unreleased alpha.5 source candidate includes modular SYNTYR distributions,
including the optional utilities, print and symbols stylesheets, plus
the terminal ANSI palette JSON, this guide, MIT license, and README. No retired compatibility aliases are shipped. The ZIP is created deterministically using only
Python's standard library:

```sh
python3 scripts/build.py --check
python3 -m unittest discover -s tests -v
python3 scripts/package_release.py
```

Both visual themes and all essential components are MIT-licensed. Commercial
premium templates, if introduced, will be independently authored and sold
separately. This v0.3 alpha is **not** a v1 production compatibility guarantee;
cross-browser and full accessibility audits are still release gates.

The `syn-` selectors, `--syn-` custom properties and `data-syn-` attributes are the only supported source API.
