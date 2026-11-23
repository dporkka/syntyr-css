# Syntyr with static-site generators

Syntyr's distribution is ordinary, scoped CSS. It does not require a
JavaScript runtime, hydration, Sass, PostCSS, browser-specific components,
or a static-site generator integration package. Generate **semantic HTML**
with your preferred template engine; load one CSS distribution from your
site's assets and put `syn-root` on the intended page or region.

**Version boundary:** the source repository currently contains an
**unreleased** alpha.5 npm package and CSS candidate. The published alpha.4
assets are different. Do not claim `npm install @syntyr/css` will fetch
alpha.5 from the registry; use an actual published, pinned version, a local
package archive, or a self-hosted versioned CSS file.

## Runnable zero-JavaScript marketing site starter

The [Waypoint SaaS marketing starter](../examples/site-starters/saas-marketing/README.md)
demonstrates how one Syntyr stylesheet can serve a **complete three-page site**:
a home page with hero, dashboard illustration, feature grid, workflow steps
and native FAQ; a pricing page; and an about page. All content is explicitly
fictional. Unlike a source-only snippet, it includes an offline exporter:

```sh
python3 scripts/export_site_starter.py --output /tmp/waypoint-static
python3 -m http.server 8000 --directory /tmp/waypoint-static
```

Open `http://localhost:8000/`. The export contains its own pinned
`assets/syntyr.core.css`, works offline, and uses **no browser JavaScript**.
The [public preview](https://syntyr-css.pages.dev/examples/site-starters/saas-marketing/)
is available only after the corresponding source change is published.
It is a starting point for Astro, Hugo or Eleventy composition, **not** a
prebuilt adapter for any generator. The source candidate remains unreleased.

## Integration matrix

| Generator | Recommended CSS delivery | Base path / deployment concern | Example |
| --- | --- | --- | --- |
| **Astro** | `import '@syntyr/css/core.css'` in an Astro page/layout (local archive or published package) | Astro `base` controls generated asset paths; prefer imported CSS to hardcoded root URLs | [Runnable Astro fixture](https://github.com/dporkka/syntyr-css/tree/main/examples/astro/) |
| **Eleventy (11ty)** | Copy `dist/syntyr.core.css` through `addPassthroughCopy` | Use `pathPrefix` and Eleventy's `url` filter | [Runnable Eleventy fixture](https://github.com/dporkka/syntyr-css/tree/main/examples/eleventy/) |
| **Hugo** | Serve prebuilt CSS from `static/` or a Hugo filesystem mount | Use `relURL` for assets, not a bare `/css/` URL on project subpaths | [Isolated Hugo proof](https://github.com/dporkka/syntyr-css/tree/main/experiments/hugo/) |
| **Jekyll** | Copy prebuilt CSS into `assets/css/`; do not process it as Sass | Use Liquid `relative_url` and configure `baseurl` for GitHub project pages | Snippet below |
| **Zola** | Copy prebuilt CSS into `static/assets/` | Use `get_url` and a correctly configured `base_url` | Snippet below |
| **Next.js static export** | Import package CSS once in `app/layout.tsx` or host CSS in `public/` | Configure `output: 'export'` and `basePath` for project subpaths | Notes below |
| **Gatsby, Docusaurus, VitePress** | Import a single local/package stylesheet in the site's global stylesheet entrypoint | Respect each generator's deployment base and output asset resolution | Same HTML and CSS contract |

If you are not using a Node build, **copy the exact released stylesheet into
your static asset directory**. No npm dependency is needed. For pure HTML
and native elements, choose `syntyr.semantic-bundle.css` *instead* of core
and opt in with `class="syn-root syn-semantic"`. For explicit components,
load `syntyr.core.css` once and use classes such as `syn-panel` and
`syn-button`. Do not combine a bundle with its constituent CSS.

## Astro

```astro
---
// examples/astro uses a local file:../.. development dependency.
import '@syntyr/css/core.css';
---
<main class="syn-root syn-page" data-syn-theme="studio">
  <h1 class="syn-heading">Static Astro page</h1>
</main>
```

The import is build-time CSS processing; no Syntyr script is injected.
To publish under a subdirectory, set `base: '/my-project/'` in
`astro.config.mjs`. Do not hardcode `href="/assets/..."` unless you also
account for `import.meta.env.BASE_URL`. See
[Astro's CSS guidance](https://docs.astro.build/en/guides/styling/)
and [base-path configuration](https://docs.astro.build/en/reference/configuration-reference/).

## Eleventy

The [Eleventy example](https://github.com/dporkka/syntyr-css/tree/main/examples/eleventy/) copies the current dist CSS
directly to `_site/assets/syntyr.core.css`; its Nunjucks template uses:

```njk
<link rel="stylesheet" href="{{ '/assets/syntyr.core.css' | url }}">
<main class="syn-root" data-syn-theme="studio">
  <h1 class="syn-heading">Static site</h1>
</main>
```

`pathPrefix: '/syntyr-eleventy/'` deliberately tests a project-pages base
path. Adapt it to your hosting path. No client-side Eleventy JavaScript is
needed. [Eleventy's URL filter](https://www.11ty.dev/docs/filters/url/)
documents subpath behavior.

## Hugo

Copy `dist/syntyr.core.css` to `static/assets/syntyr.core.css`, or use a
filesystem mount as in [the Hugo preview](https://github.com/dporkka/syntyr-css/tree/main/experiments/hugo/). In a Hugo
layout:

```html
<link rel="stylesheet" href="{{ "assets/syntyr.core.css" | relURL }}">
<main class="syn-root" data-syn-theme="studio">...</main>
```

Do not use an unprefixed `/assets/...` URL for GitHub Pages project sites.
Hugo's own preview script validates its existing rendered Markdown pages
and local links:

```sh
python3 scripts/verify_hugo_preview.py --hugo /path/to/hugo
```

## Jekyll / GitHub Pages

Jekyll needs only a copied prebuilt asset and native Liquid URL filtering.
In a consumer Jekyll site's root:

```sh
mkdir -p assets/css
cp /path/to/syntyr/dist/syntyr.core.css assets/css/syntyr.core.css
```

In a layout or page (not inside a verbatim Liquid/raw block):

```liquid
<link rel="stylesheet" href="{{ '/assets/css/syntyr.core.css' | relative_url }}">
<main class="syn-root" data-syn-theme="studio">...</main>
```

If the site lives at `https://user.github.io/project/`, set
`baseurl: "/project"` in `_config.yml`. Commit the CSS asset with your
site. Do not put front matter in the CSS file or run it through Jekyll's
Sass compiler. [Jekyll's GitHub Pages guide](https://jekyllrb.com/docs/github-pages/)
explains `relative_url`.

## Zola

In the consumer site's root:

```sh
mkdir -p static/assets
cp /path/to/syntyr/dist/syntyr.core.css static/assets/syntyr.core.css
```

In a Tera template:

```tera
<link rel="stylesheet" href="{{ get_url(path='assets/syntyr.core.css') }}">
<main class="syn-root" data-syn-theme="studio">...</main>
```

Set `base_url = "https://example.com/project/"` in `config.toml` for
subpath hosting. This URL is resolved at build time; Syntyr does not need
client JavaScript or a Zola-specific adapter. See [Zola's get_url](https://www.getzola.org/documentation/templates/).

## Next.js export, Gatsby and documentation generators

Next.js supports a static-export deployment using `output: 'export'`
in `next.config.*`. Import one Syntyr CSS file from the top-level App Router
layout and apply `syn-root` in HTML. Adjust `basePath` and static assets
when exporting to a project subpath. **Next.js/Gatsby may ship their own
hydration JavaScript:** "zero Syntyr runtime JS" does *not* mean a zero-JS
site when the generator itself uses client-side code. Gatsby, VitePress
and Docusaurus can consume the same CSS through their respective global
style entrypoints; these are integration instructions, not verified build
fixtures.

## Verification and failure modes

From the Syntyr repository root:

```sh
python3 scripts/build.py --check
python3 -m unittest tests.test_static_site_generators tests.test_adoption_starters
cd examples/eleventy
npm install
npm run build
npm run verify
```

The optional Python verifier checks **generated HTML**, not merely source
templates. It rejects missing/local-unresolvable stylesheets, stylesheet URLs
that ignore the deployment **base path**, unexpected browser scripts, missing
`syn-root` scopes, and CSS output without Syntyr selectors. For a different
generator, point it at its output and pass its exact mount prefix:

```sh
python3 scripts/verify_static_generators.py /path/to/site-output --base-path /my-project/
```

Only run it against pages deliberately built to be JavaScript-free and styled
with Syntyr; it is not a general-purpose validator for unrelated application
routes. It checks output correctness but not browser accessibility, responsive
layout, static exporter security settings, or hosting/CDN rewrite behavior.
For a visual smoke test, serve the generated output at its configured base
path and inspect styles/network requests in an actual browser.

**Common pitfalls:** using a root-absolute CSS URL on a subpath deployment;
importing core plus the semantic bundle (duplicate styles); applying
`syn-semantic` globally to an existing third-party theme; unpinned remote
CDN URLs; and assuming `file:../..` in a development fixture is a published
npm package. The Syntyr CSS runtime remains zero dependency regardless of
the generator chosen.
