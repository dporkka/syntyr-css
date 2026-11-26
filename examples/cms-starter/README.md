# Syntyr portable CMS starter (experimental alpha.5)

A working **static HTML + CSS** landing page with optional Git-backed editors.
The source of truth is [content/pages/home.json](content/pages/home.json). [Sveltia CMS](https://sveltiacms.app/), [Pages CMS](https://pagescms.org/) and the optional
[Decap CMS configuration](decap/) edit the same file. None becomes a dependency of Syntyr's MIT CSS core.

This is an example template, not an installed CMS on syntyr-css.pages.dev.
It demonstrates five semantic, reusable section types: hero, features, pricing,
FAQ and CTA. No arbitrary raw HTML blocks, app runtime, CMS database or server
process are required for the published page.

## Build locally from the Syntyr repository

From the Syntyr repository root, after building Syntyr's current source candidate:

```sh
python3 scripts/build.py
python3 scripts/render_cms_starter.py
python3 -m http.server 8080 --directory examples/cms-starter/_site
```

Visit http://localhost:8080/ to see the rendered site (without a browser JS
framework). The optional Sveltia editor is at `/admin/`. To use remote GitHub
editing, configure authentication as described below before signing in.

## Copy into an independent site repository

```sh
mkdir -p ../my-syntyr-site/scripts ../my-syntyr-site/css
cp -R examples/cms-starter/. ../my-syntyr-site/
cp scripts/render_cms_starter.py ../my-syntyr-site/scripts/
cp dist/syntyr.core.css dist/syntyr.recipes.css ../my-syntyr-site/css/
cd ../my-syntyr-site
python3 scripts/render_cms_starter.py --source . --css-root css --output public
python3 -m http.server 8080 --directory public
```

Commit the source files **including** `.pages.yml`, `admin/config.yml`,
`admin/index.html`, `content/pages/home.json`, `scripts/render_cms_starter.py`
and vendored CSS. Do not commit the generated `public/` output unless your
hosting provider requires it. Refresh vendored CSS intentionally from one
version; do not mix alpha.4 and alpha.5 stylesheets.

Use `python3 scripts/render_cms_starter.py --source . --css-root css --output public`
as the build command for your static hosting provider, and set the publish
directory to `public`. Commits to the content repository must trigger a build
and deployment; the editor does **not** deploy changes itself.

Section IDs in `content/pages/home.json` are required, stable lowercase slugs.
Keep them unchanged when moving blocks, so links like `/#section-features`
remain valid; duplicate IDs or unsafe slugs fail validation. All editor
configurations expose this field.

## Validate content before rendering

The portable [v1 JSON Schema](blocks.schema.json) describes the allowlisted
document and block shape for editor tooling. The canonical Python validator
adds constraints that the structural schema cannot express, including unique
stable IDs, nonblank strings and URL safety.

```sh
python3 scripts/render_cms_starter.py --validate-only
# In the standalone site repository:
python3 scripts/render_cms_starter.py --source . --validate-only
```

This read-only command fails before any HTML is emitted. Python rendering,
Hugo staging and the Keystatic/Payload export adapters reuse strict UTF-8
JSON ingestion: duplicate keys, invalid Unicode, non-finite numbers,
documents larger than 16 MiB and excessive nesting are rejected. The bounds
protect build tooling, not a live upload endpoint. Normal HTML escaping and
URL validation still apply; raw HTML is not an allowed block. Generator
integrations should invoke the canonical validator rather than parsing
untrusted JSON separately.

## Choose an optional editor

**Sveltia CMS (recommended default)**

1. In `admin/config.yml`, replace `REPLACE_OWNER/REPLACE_REPO` with the GitHub
   repository containing the **site root** (`content/pages/home.json`).
   Set `backend.branch` to the branch holding that file (the default is
   `main`); change it if your content branch differs. The sample
   `media_folder` is `media/` and should be tracked or created by the editor
   before handling uploads.
2. Commit and deploy the site (the generated `public/admin/` contains the
   Sveltia editor HTML/config). Open `/admin/` and authenticate.
3. Developers can use a scoped fine-grained GitHub token; for nontechnical
   editors, deploy the [official Sveltia Cloudflare Worker GitHub App
   authenticator](https://github.com/sveltia/sveltia-cms-auth) and set
   `backend.base_url` in `admin/config.yml`. Keep OAuth secrets only in
   Worker secrets, not in Git.
4. Editorial workflow is enabled by default: changes use pull requests, so
   protected branches remain protected. Review/merge the PR to publish.
   Authenticate with GitHub permissions that include both contents and PRs.

The Sveltia **editor only** uses third-party JavaScript from UNPKG; the public
site doesn't. Do not deploy this starter's admin under Syntyr's existing
strict documentation CSP without a dedicated compatible, reviewed policy.
For production, audit and control external editor assets and restrict access
to the editor as appropriate.

**Pages CMS (alternative)**

1. Leave `.pages.yml` at the **repository root** of your copied site.
2. Open [Pages CMS](https://pagescms.org/), connect the same GitHub repository
   and select the desired branch. Pages will discover the config and show
   Homepage as a structured block-editable file.
3. Save changes, review commits/PRs according to your repository's settings,
   and let your existing Git-triggered static build deploy the result.

`.pages.yml` is nested inside the example in the Syntyr mono-repository on
purpose, to avoid changing the configuration of the Syntyr library itself.
When moved to a standalone site it becomes effective at the site repo root.

**Do not run multiple editors simultaneously against the same file** without
coordinating edits; use normal Git review to resolve concurrent updates.

**Decap CMS (optional third editor)**

The [Decap configuration](decap/config.yml) and [editor shell](decap/index.html)
use the same five block types, the same `type` discriminator and the same
`content/pages/home.json` document. To use it, copy those two files to
`admin/config.yml` and `admin/index.html` in the **standalone site's**
repository, replacing the Sveltia versions; replace
`REPLACE_OWNER/REPLACE_REPO` and configure GitHub OAuth separately.
The editor's JavaScript is pinned to Decap 3.18.0 and is **admin-only**.
The default build does not publish Decap; review CDN/CSP and authentication
requirements before deployment. For a Hugo front end, see the
[runnable Hugo CMS fixture](../hugo-cms/README.md).

## Portable contract and safety

- [blocks.schema.json](blocks.schema.json) defines version-one JSON shapes.
  Section `type` maps to a fixed, allowlisted Syntyr renderer; arbitrary
  custom HTML and unknown properties are rejected.
- The Python renderer uses standard-library escaping and checks links: only
  root-relative and absolute `http(s)` URLs are accepted. Never insert CMS
  strings directly into `innerHTML` or unescaped host framework templates.
- The first section is a hero with the page's unique `h1`; following sections
  get `h2` landmarks. FAQ uses native HTML `details`/`summary`.
- The editor's field schemas and JSON contract deliberately cover a small
  stable marketing-page subset. Images, uploads, Markdown-to-HTML, commerce
  transactions and back-end functionality are out of scope, not mocked.
- Migrating to Astro/Hugo/Go templates means reading the same JSON and
  mapping known section types to each host's Syntyr HTML components; CSS stays
  independently versioned. A future Directus adapter can produce the same JSON.
- This example uses the **unreleased alpha.5 source CSS**. The published
  alpha.4 lacks some newer styles/themes. Pin a tested distribution before
  using the starter in production.

For further implementation details see [the repository CMS integration guide](../../docs/cms-integration.md).
