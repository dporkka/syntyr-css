# Hosting SYNTYR on Cloudflare

SYNTYR is a static website and CSS library. It does not need a server,
database, JavaScript runtime, Node install, NPM install, or a CDN SDK.

## Reproducible, allowlisted output

From the repository root:

```sh
python3 scripts/build.py --check
python3 -m unittest discover -s tests -v
python3 scripts/build_cloudflare_site.py
python3 scripts/build_cloudflare_site.py --check
```

The generated `.cloudflare-public/` directory is the **only** directory
that may be published. Never deploy the repository root: it contains tests,
scripts, experiments, and business planning material.

The site retains relative HTML links, component examples, Markdown guides,
terminal palette JSON, and public CSS assets. The optional documentation-only theme editor has its
own small JavaScript file; consuming apps and other demos require none.

See [the provider-neutral staging and experimental Nulang Cloud guide](nulang-cloud-hosting.md) for an optional portable artifact workflow. This does not replace the existing production Cloudflare hosting path.

## Cloudflare hosting

Preferred for new deployments: Cloudflare Workers Static Assets. A simple
existing Cloudflare Pages project also serves these files globally without a
Worker runtime; use Pages when its Git integration is already in place.

For a Git-connected static deployment, use:

- Repository: `dporkka/syntyr-css`, production branch `main`
- Build command: `python3 scripts/build.py --check && python3 -m unittest discover -s tests -q && python3 scripts/build_cloudflare_site.py`
- Output directory: `.cloudflare-public`
- Project root: repository root
- No server-side functions and no install command

Cloudflare Pages project: `syntyr-css`, configured for `main` and the
`.cloudflare-public` output, with hostname `syntyr-css.pages.dev`. This
project uses Git-connected builds, and its live production deployment was
verified with HTTP 200 responses for public pages/assets and HTTP 404 for
non-public paths. Cloudflare builds run the Python test suite as a release gate.

Configure a custom domain only after DNS and trademark/name clearance.
Keep the existing GitHub Pages site as a rollback until production checks pass.

## Browser security policy

The generated `_headers` file applies a site-wide enforced
`Content-Security-Policy`, `Strict-Transport-Security`, `Permissions-Policy`,
`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, and the
`Referrer-Policy`. It disallows inline scripts, script evaluation, third-party
script sources, object embedding, and cross-origin framing. `frame-src 'self'`
is needed for the docs-only sandboxed `about:srcdoc` component playground.
`img-src 'self' data:` and `connect-src 'self'` prevent unsolicited remote
asset loads or fetches from compromised page code.

**Known tradeoff:** `style-src 'self' 'unsafe-inline'` remains necessary because
existing human-facing documentation uses inline style attributes and a few
inline `<style>` elements. This does *not* permit inline JavaScript. To tighten
it, migrate presentational attributes to classes/external stylesheets, remove
inline style elements, exercise the playground and all published pages in
Chromium/Firefox/WebKit, then evaluate `style-src 'self'` in a report-only
policy before enforcing. Do not simply drop `unsafe-inline` and break the
live documentation.

These headers secure the *Syntyr website*, not software using `@syntyr/css`.
Applications embedding the stylesheet must configure their own CSP and
server-side authentication, authorization, CSRF, and billing protections.
The CSP also does not make user-controlled HTML safe; applications still
need contextual escaping and safe DOM APIs.

Validate the deployed origin after every production publish:

```sh
curl -fsSI https://syntyr-css.pages.dev/docs/playground | grep -iE 'content-security-policy|strict-transport-security|permissions-policy|x-frame-options'
```

An HTTP header check must inspect the **deployed** site, not just `_headers`
in the built artifact. Avoid making security claims based only on configuration
or a GitHub check. HSTS affects the Syntyr origin, not third-party consumers.

## Immutable stylesheets for the live documentation site

The Cloudflare publish builder rewrites its **own HTML stylesheet links**
to content-addressed `/_assets/css/<sha256>.css` copies. Cloudflare serves
these with `Cache-Control: public, max-age=31536000, immutable`, so
repeat visits avoid unnecessary stylesheet revalidation. A change to any
CSS asset changes the hash and the generated HTML reference in the same
deployment. The original source HTML files are **not** edited.

The regular `/dist/*` preview and download URLs remain available,
mutable and revalidated (`max-age=0, must-revalidate`); never mark
unversioned preview CSS immutable. Frozen public `/v/<version>/*`
releases remain byte-for-byte unchanged. Third-party applications should
still self-host or pin versioned assets, rather than copy the hashed
documentation-only URLs.

Before adding a new frozen CDN version, follow the [release freeze review
procedure](release-freeze.md) and run `python3 scripts/freeze_site_release.py
--check`. The `--apply` freeze operation requires an exact-commit human evidence record
and a fresh deterministic CSS build; the read-only technical preflight,
routine CI and candidate ZIP creation do not grant publication approval.

The builder recognizes local linked stylesheet files that are included
in the public allowlist. It rejects CSS containing unresolved `@import`
or `url()` dependencies rather than silently moving it to a different
relative path. If a new CSS file needs relative assets, explicitly add
and test a relocation strategy before publishing.

## CSS CDN URLs

Unversioned CSS: `/dist/syntyr.core.css` for previews and quick starts.

Frozen CSS: `/v/0.3.0-alpha.4/syntyr.core.css` for pinned consumers.
Every version under `site-releases/` is copied to `/v/<version>/`.
Published snapshots have SHA-256 hashes in `site-releases/manifest.json`.
Do not modify, reuse, or delete a published version; release a new version.
The build refuses mismatched hashes, and the `_headers` file marks only
`/v/*` assets as immutable.

**Self-host CSS in the consuming application's own origin when possible.**
A separate CDN hostname can cost an additional DNS lookup, connection, and
TLS negotiation even when Cloudflare serves it from a nearby edge.

## HTTP validation after deploy

```sh
BASE=https://<your-cloudflare-site>
curl -fsSI "$BASE/"
curl -fsSI "$BASE/docs/"
curl -fsSI "$BASE/dist/syntyr.core.css"
curl -fsSI "$BASE/v/0.3.0-alpha.4/syntyr.core.css"
curl -fsS -o /dev/null -w '%{http_code}\n' "$BASE/business/strategy.md"
```

Expected: HTML and CSS 200; internal business document 404. The published
root `404.html` is required: without it, Cloudflare Pages serves unknown
paths as an SPA fallback with HTTP 200.
Check MIME types (`text/html`, `text/css`), Cache-Control,
`cf-cache-status` where present, and gzip/Brotli transfer behavior.

Cloudflare routing may normalize trailing-slash URLs. Check for 301/308
redirects as well as final 200 responses. The `_headers` file applies
security and cache policy without adding application JavaScript.

## CI release checks

`.woodpecker/quality.yaml` gates pull requests and `main` pushes with
Python-only CSS verification, the repository contract tests, the allowlisted
Cloudflare output and deterministic release packaging. The existing Cloudflare
build command independently runs the same Python tests.

`.woodpecker/browser.yaml` is a manual/tag release gate using Playwright's
pinned browser image (Chromium, Firefox and WebKit), enlarged-text reflow and
the theme editor. The CI images are pinned to registry manifest digests; update
them deliberately after reviewing upstream security patches.

`.woodpecker/security.yaml` audits the committed npm lockfiles of the optional
Lit example and framework benchmark against high/critical advisories on PRs,
main pushes and manual runs. This is **not** a claim that all optional examples
are covered: the Astro, Tailwind, and React adapters must gain committed locks
or be audited separately before they become release artifacts. The CSS library
itself ships no npm runtime dependencies.

Configuring a pipeline is **not** proof that the Woodpecker repository is
activated or a pipeline executed. Require a real successful
run on the exact proposed commit before declaring CI green.

## Performance validation

Measure WebPageTest/Lighthouse in several regions and on mobile.
Track LCP, CLS, INP, transfer bytes, and first-load connection overhead.
Cloudflare reduces distance to content but does not fix CSS render costs.

For comparative measurement rules, see [performance validation](performance-validation.md).

## Safe immutable-release preflight

An unfrozen source candidate is **not** a published CDN release.
Run these read-only checks before preparing a release:

```sh
python3 scripts/build.py --check
python3 -m unittest discover -s tests -q
python3 scripts/freeze_site_release.py --check
python3 scripts/package_release.py /tmp/syntyr-release-candidate.zip
```

The freeze script defaults to **read-only preflight**. It verifies the
SHA-256 manifest of every previously published release, checks that generated
CSS matches the current source, and previews the exact public CSS distributions.
Non-allowlisted files in dist/ are excluded. It never tags or publishes.

**Only after manual release approval** (including accessibility evidence,
real browser and assistive-technology testing, naming clearance, and exact-head
CI), run `python3 scripts/freeze_site_release.py --apply`. This adds a
new immutable snapshot and manifest entry without replacing existing versions.
Then update installation links and version-specific tests, rebuild the static
site, and verify the new `/v/<version>/` URLs before announcing the release.

npm publication remains a **separate authenticated operation**; a frozen CDN
asset or locally packaged ZIP does not establish npm publication.
