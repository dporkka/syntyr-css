# Deploy Syntyr sites to Cloudflare and prepare for Nulang Cloud

Syntyr's MIT CSS, themes, and static HTML stay **hosting-independent**.
This is an **experimental deployment adapter**, not a hosted website builder or
a production Nulang Cloud static-hosting service.

Syntyr currently provides two static-site preparation targets:

| Target | Output | Live deployment |
| --- | --- | --- |
| Cloudflare | Identical static directory, preserving `_headers` and `_redirects` | Continue using the existing Cloudflare Pages / Workers Static Assets deployment |
| Nulang Cloud (experimental) | Deterministic ZIP plus a SHA-256 file manifest | **Not supported yet**; no static-site ingestion API has been qualified |

Syntyr Premium and Studio assets are **not** included in the public-site
allowlist; licensing and private assets remain separate from hosting.

## Publish the Syntyr documentation site

The existing Cloudflare path is unchanged:

```sh
python3 scripts/build.py --check
python3 -m unittest discover -s tests -q
python3 scripts/build_cloudflare_site.py
python3 scripts/build_cloudflare_site.py --check
```

To stage those files for Cloudflare from an already-reviewed output directory:

```sh
python3 scripts/static_deploy.py \
  --provider cloudflare \
  --site-dir .cloudflare-public \
  --site-url https://syntyr-css.pages.dev \
  --output /tmp/syntyr-cloudflare-stage
```

This **only stages a directory**. Configure your existing host to publish the
result; it does not authenticate, upload, configure domains, or change DNS.

## Prepare an experimental Nulang Cloud bundle

Build a portable version of the **public Syntyr documentation website** with
the intended production HTTPS origin. The `--portable` switch omits
Cloudflare-only `_headers` (whose security rules would otherwise be lost on
another provider) and rewrites canonical, sitemap, and robots URLs.

```sh
python3 scripts/build_cloudflare_site.py \
  --portable \
  --site-url https://example.com \
  --output /tmp/syntyr-portable-public

python3 scripts/static_deploy.py \
  --provider nulang-cloud \
  --experimental-nulang-cloud \
  --site-dir /tmp/syntyr-portable-public \
  --site-url https://example.com \
  --output /tmp/syntyr-nulang-bundle.zip
```

This produces:

- `site/` containing the reviewed static files, without source-control metadata.
- `syntyr-deploy.json` with schema `syntyr.static-site.bundle/v1`, expected HTTPS origin, relative file paths, sizes, and SHA-256 digests.

The ZIP format is a **Syntyr-owned staging contract**, not an official Nulang
Cloud HTTP API. It does not grant deployment capability or assert that Nulang
Cloud can currently serve the bundle. There are no required dependencies,
tokens, network requests, VM provisioning, or deployment charges.

Atomic ZIP preparation requires an output filesystem supporting **hard links**.
Filesystems such as exFAT may not support this operation: create the ZIP on a
compatible local filesystem, verify the receipt, then copy the complete archive
to the intended destination. If cleanup of the temporary filename fails after
the hard link is created, the CLI still returns a successful preparation receipt
with a separate cleanup warning; remove the leftover temporary file manually.

For a **different Syntyr-based site**, point `--site-dir` at its reviewed
static build output (for example, a generated `dist/` containing
`index.html`), rather than at the Syntyr repository or an arbitrary source
tree. The adapter preserves the site's existing HTML and CSS. It does not
rewrite hardcoded absolute references in other people's builds.

## Safety and compatibility

- Source trees, symlinks, hidden files and sensitive key/credential filenames are rejected.
- Existing output paths are not overwritten, and writing output inside the site source is rejected.
- Site origin must be HTTPS with no path, fragment, userinfo or query.
- The Nulang adapter refuses Cloudflare-specific `_headers` and `_redirects` rather than silently dropping required security behavior.
- Nulang's live `--publish` operation intentionally fails closed; do not advertise this as one-click live hosting.

## Requirements before enabling live Nulang Cloud deployment

Nulang Cloud needs a separately implemented, authenticated, tenant-isolated
static asset ingestion contract, immutable versioning, content integrity
validation, safe cache headers, HTTPS/custom domains, rollback, quotas,
deployment receipts and operational recovery tests. The Syntyr adapter should
consume that existing platform API once qualified; it must not create its own
hosting control plane, force a Firecracker microVM onto each static website, or
couple the MIT CSS core to Nulang Cloud.

Until those requirements are met, **use Cloudflare for production websites**.
Keep Nulang Cloud hosting experimental and disabled by default.
