# Syntyr + Astro + Keystatic (static-first reference)

An **executable marketing-site fixture** using the Syntyr CSS core, Astro,
and Keystatic's typed homepage singleton. Keystatic acts as an **optional
local development editor**; the public build exports **static HTML and CSS**
without editor routes, browser JavaScript, or a running CMS.

This example uses Astro 7 and Keystatic Astro 6. Use Node.js 24 LTS (or at least Node.js 22.23.4).
The underlying Syntyr CSS is sourced from the checked-out repository:
`"@syntyr/css": "file:../.."`. This is not a claim that the unreleased
alpha.5 package can be installed from npm.

## Build and preview

From the Syntyr monorepository checkout:

```sh
cd examples/astro-keystatic
npm ci
npm run build
npm run verify
```

The build automatically runs `scripts/export_cms_adapter.py keystatic`
against `content/pages/home.json`, validates the exact Syntyr CMS v1
contract (Hero, Features, Pricing, FAQ and CTA), and generates a temporary
`src/data/home.json`. Astro then renders that validated JSON as semantic
HTML with autoescaped content. Unknown fields, unsafe URLs, or duplicate
section anchors fail the export before Astro begins.

This fixture deliberately sets `base: '/syntyr-astro-keystatic/'` to test
project-subpath deployment. Its CSS and local links are base-aware. When
serving a local preview, ensure the output is mounted at that path; for
**Cloudflare Pages at the domain root**, change the base to `'/'`, update the verifier's `--base-path` argument to `/`, and
publish the `dist/` directory directly. Do not deploy this subpath fixture
unchanged to a root-only site; its assets would load from the wrong URL.

## Optional local editor

```sh
npm run dev:editor
```

Visit `http://127.0.0.1:4321/keystatic` on the same machine. Both the
Keystatic admin and its dev API are available **only when**
`SYNTYR_ENABLE_LOCAL_EDITOR=1` and `NODE_ENV=development`. Astro binds
to `127.0.0.1` (loopback), not a public network interface. The editor uses
`storage.kind: local` and edits the same `content/pages/home.json`
fixture consumed by the static build. Restart or rebuild the public preview
after saving changes so the validated content export is refreshed.

Do not expose the dev server with a reverse proxy, a tunnel, or a public
`--host` flag. Local Keystatic mode is not an authenticated hosted editor.

## Git-backed publishing without GitHub Actions

1. Edit the checked-in content using `npm run dev:editor` on an authorized
   developer workstation.
2. Run `npm run build && npm run verify`, review the changed JSON, and
   commit the content changes to a feature branch.
3. Open a pull request and merge only after review. Deploy from the protected
   `main` branch through your hosting provider's **Git integration**
   (e.g. Cloudflare Pages), using `npm ci && npm run build` from the example
   directory and publishing `dist/` with an appropriate site `base`.
4. The hosting build has **no Keystatic editor or OAuth service**. The Git
   commit is the source of truth; the deployment contains only generated
   HTML and CSS.

A separately hosted Keystatic **GitHub storage** editor can be added if
nontechnical collaborators need remote editing, but it requires a GitHub App,
server-side OAuth secrets, an Astro server adapter, access review and an
operational security model. None of that is silently enabled here. See the
[official GitHub mode guide](https://keystatic.com/docs/github-mode) and
[Astro integration guide](https://keystatic.com/docs/installation-astro).

## Maintenance boundaries

The editor configuration is currently vendored from
`examples/cms-keystatic/keystatic.config.ts`. Keep them synchronized when
evolving the portable CMS v1 fields. Keep the editor packages in this
fixture, not in the CSS-core `package.json`.

Do not edit `src/data/home.json` directly; it is generated and gitignored.
The public site does not expose editor credentials, internal Payload
metadata, or unvalidated source JSON.
