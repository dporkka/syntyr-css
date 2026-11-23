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
npm ci --include=dev
npm run build
npm run verify
```

The `npm run verify` command additionally rejects any generated CMS/API route, non-index HTML page, or browser JavaScript asset; the generic SSG verifier by itself does not enforce those fixture-specific checks.

The build automatically runs `scripts/export_cms_adapter.py keystatic`
against `content/pages/home.json`, validates the exact Syntyr CMS v1
contract (Hero, Features, Pricing, FAQ and CTA), and generates a temporary
`src/data/home.json`. Astro then renders that validated JSON as semantic
HTML with autoescaped content. Unknown fields, unsafe URLs, or duplicate
section anchors fail the export before Astro begins.

<!-- coderabbit-ai-generated:v1 -->

<!-- coderabbit-ai-generated-section:v1:454d1687cc1d8ab485ae78b3810f984f3333ac37e94f38acf512b342d27f1a37 -->

This fixture uses `base: '/syntyr-astro-keystatic/'`. Mount its output at
that path when previewing or hosting it. For **Cloudflare Pages at the domain
root**, set `base: '/'` in `astro.config.mjs`, then run:

```sh
npm run build && npm run verify -- --base-path /
```

Publish `dist/` only after verification passes.

<!-- /coderabbit-ai-generated:v1 -->

## Optional local editor

```sh
npm run dev:editor
```

Visit `http://127.0.0.1:4321/syntyr-astro-keystatic/keystatic` on the same machine. Both the
Keystatic admin and its dev API are available **only when**
`SYNTYR_ENABLE_LOCAL_EDITOR=1` and `NODE_ENV=development`. Astro binds
to `127.0.0.1` (loopback), not a public network interface. The editor uses
`storage.kind: local` and edits the same `content/pages/home.json`
fixture consumed by the static build. Restart or rebuild the public preview
after saving changes so the validated content export is refreshed.

Do not expose the dev server with a reverse proxy, a tunnel, or a public
`--host` flag. Local Keystatic mode is not an authenticated hosted editor.

## Git-backed publishing without GitHub Actions

<!-- coderabbit-ai-generated:v1 -->

<!-- coderabbit-ai-generated-section:v1:5674b9748a5dd80440e091ceafc3289b57240b7c8af05436b2fd97b5225a0661 -->

1. Run `npm run dev:editor` on an authorized developer workstation and edit
   the checked-in content.
2. Build and verify locally, review the changed JSON, and commit it to a
   feature branch. Open a pull request and merge only after review.
3. In your hosting provider's **Git integration**, build from the protected
   `main` branch. In the example directory, use
   `npm ci --include=dev && npm run build && npm run verify`. If you change
   Astro's mount path, give the verifier that path with leading and trailing
   slashes, for example `npm run verify -- --base-path /` at the domain root.
4. Publish `dist/` only after the entire command succeeds. The Git commit is
   the source of truth. The output contains only generated HTML and CSS, with
   no Keystatic editor or OAuth service.

<!-- /coderabbit-ai-generated:v1 -->

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
