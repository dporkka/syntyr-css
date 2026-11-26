# Runnable adoption fixtures

These fixtures exercise a **real consuming build** using the local Syntyr
CSS-only package. They are independent, optional development projects.

## Tailwind CSS v4

[Source](../examples/tailwind-v4/) — one HTML page using Tailwind utility
layout plus namespaced Syntyr tokens and components. It includes nested
Noir styling and exercises the generated Tailwind `@theme inline` bridge.

```sh
cd examples/tailwind-v4
npm install
npm run build
python3 -m http.server 8000
```

## Astro

[Source](../examples/astro/) — static Astro application using Syntyr's
`core.css` package subpath. No browser JavaScript is needed for the UI.

```sh
cd examples/astro
npm install
npm run build
npm run preview
```

## Eleventy static-site generator

[Source](../examples/eleventy/) — Eleventy 3 copying Syntyr's prebuilt CSS
from `dist/` into a subpath-deployed output. Uses native Nunjucks and no
Syntyr/Eleventy browser runtime.

```sh
cd examples/eleventy
npm install
npm run build
npm run verify
```

## Hugo + portable CMS JSON

[Source](../examples/hugo-cms/) — Hugo v0.170.0 renders the existing
CMS starter JSON into static Syntyr sections and verifies project-subpath
styles and links. Optional Sveltia, Pages CMS or Decap editors can update
the source file; none run on the public page.

```sh
python3 scripts/build_hugo_cms_starter.py --hugo hugo --output /tmp/syntyr-hugo-site
```

The same Hugo adapter supports `--preset personal`, `--preset business`
and `--preset documentation`, with ordinary Markdown, native navigation,
RSS, sitemap and a 404 page. Export the complete source and checksummed
local styles with `--source-output` instead of `--output`; after export,
only the pinned Hugo executable is needed to rebuild. See the
[source starter README](../examples/hugo-cms/README.md) for commands,
release boundaries and archival guidance.

For Hugo, Jekyll, Zola, and static Next.js export, see the
[static-site generator compatibility guide](static-site-generators.md).

## shadcn/ui semantic token compatibility

[Source](../examples/shadcn-bridge/) — a Tailwind v4 project exercising
scoped shadcn semantic colors, a nested Noir palette and host isolation.
This exercises shadcn-style utility output, not an actual generated React
component. See the [adapter guide](shadcn-integration.md).

```sh
cd examples/shadcn-bridge
npm install
npm run build
python3 -m http.server 8000
```

## Real shadcn/ui React/Radix fixture

[Source](../examples/syntyr-shadcn-react/) — generated with the official
shadcn CLI's Vite template and Radix primitives. The generated button
is exercised in a React app with interactive click handling, `asChild` links,
disabled state and scoped Studio/Noir colors.

```sh
cd examples/syntyr-shadcn-react
npm install
npm run build
npm run dev
```

The Node-based Tailwind, Astro and shadcn starters refer to `"@syntyr/css": "file:../.."` to avoid implying
the alpha.5 package is published. Replace this with an actual pinned version
after npm release. Generated assets, caches and dependencies are ignored.

The Syntyr core package itself still requires no Node, Astro, Tailwind or
other runtime dependency.

## Keystatic and Payload CMS content adapters

[Keystatic](../examples/cms-keystatic/README.md) and
[Payload CMS 3](../examples/cms-payload/README.md) offer optional typed
editor schemas for the **same Syntyr CMS v1 content**. Neither adapter is a
runtime dependency of `@syntyr/css`. Both have Python standard-library
conversion tests; the TypeScript configs can be type-checked independently.

The host applications provide editing and authorization; Syntyr validates
and renders the resulting content during a static build. See
[the CMS integration guide](cms-integration.md) for conversion commands and
security boundaries.

## Astro + Keystatic static website

[Runnable source](https://github.com/dporkka/syntyr-css/tree/main/examples/astro-keystatic/)
— an Astro marketing site that consumes the exact portable CMS JSON exported
from a Keystatic homepage singleton. Build verification checks base-prefixed
local CSS and browser scripts; its fixture-specific verifier additionally
rejects extra HTML pages, any Keystatic/admin/API artifacts, and JavaScript files.

The Keystatic editor is explicitly opted into **local development only**.
Content changes can be reviewed through Git pull requests and deployed via a
hosting provider's Git integration. No public editor server, GitHub Actions
workflow, or new CSS-core dependency is required.
