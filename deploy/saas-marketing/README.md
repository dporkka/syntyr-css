# Deploy the Syntyr SaaS marketing starter

This is a **separate hosting project** for Syntyr's original three-page fictional
Waypoint site. Do not change the repository-root Vercel/Netlify projects; those
publish the different SaaS Admin Starter. No npm, runtime JavaScript, external
assets, API or secrets are required.

## Build and preview locally

Run from the Git repository root:

```sh
python3 scripts/build_saas_marketing_site.py
python3 scripts/build_saas_marketing_site.py --check
python3 -m http.server 8080 --directory deploy/saas-marketing/.public
```

Open http://localhost:8080/, http://localhost:8080/pricing/ and
http://localhost:8080/about/. This repeatable publisher uses the original
no-overwrite exporter under the hood, then writes exactly **nine allowlisted
files**: three HTML routes, two local CSS assets, README, LICENSE,
robots.txt and a SHA-256 build manifest. It refuses unrecognized directories,
dangling symlinks and publication to the repository root.

## Vercel: independent Git project

[Import GitHub repository](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fdporkka%2Fsyntyr-css&root-directory=deploy%2Fsaas-marketing)

1. Create a NEW Vercel project from dporkka/syntyr-css at branch main.
2. Set **Root Directory** to `deploy/saas-marketing`, not the repository root.
3. Enable **Include source files outside of the Root Directory in the Build Step**
   in the Root Directory settings. This is REQUIRED because the build script and
   source CSS live above the deployment package. Without it the build fails.
4. Choose Other / no framework. The scoped vercel.json specifies:
   Build Command: `python3 ../../scripts/build_saas_marketing_site.py`
   Output Directory: `.public`
   Install Command: no dependencies to install.
5. Check the provider preview URL and all three routes before attaching a domain.

## Netlify: independent Git site

[Import GitHub repository](https://app.netlify.com/integration/start/deploy?repository=https://github.com/dporkka/syntyr-css)

1. Create a NEW Netlify site from dporkka/syntyr-css at main.
2. Keep **Base directory** at repository root (blank, or / in the UI).
3. Set **Package directory** to `deploy/saas-marketing`. The package-level
   netlify.toml takes precedence over the repository-root admin config.
4. Verify these settings from that file:
   Build Command: `python3 scripts/build_saas_marketing_site.py`
   Publish Directory: `deploy/saas-marketing/.public`
   Python version: `3.12`.
5. Check that the build log does NOT mention build_saas_admin_starter.py, and
   inspect the preview before assigning a domain. If it does, correct Package
   directory; do not accidentally repoint the existing admin site.

## Render, Cloudflare, GitHub Pages and static servers

**Render Static Site**: link the Git repository at its root; build command
`python3 scripts/build_saas_marketing_site.py`; publish path
`deploy/saas-marketing/.public`. Select a Static Site, not a web service.

**Cloudflare Pages**: use a NEW project with repo-root build command
`python3 scripts/build_saas_marketing_site.py` and output directory
`deploy/saas-marketing/.public`, or Direct Upload the generated directory.
Do not overwrite Syntyr's existing documentation site.

**GitHub Pages**: publish only the files from .public at the root of a
separate gh-pages branch or repository and select that branch in Pages settings.
No GitHub Actions or JavaScript build is necessary.

**Any static server** (Caddy, Nginx, object storage/CDN): upload only .public,
serve index.html at /, pricing/index.html at /pricing/ and
about/index.html at /about/. No SPA fallback or backend is required.

## Before using the template for a real company

The example contains fictional names, prices and product claims. It intentionally
publishes a `noindex,follow` tag and a robots.txt with Disallow: / to prevent
the example from being indexed. **Remove both for a real public marketing site**,
after replacing demo content, metadata, product claims, navigation, legal pages
and any required consent information. Forms, checkout and authentication are not
implemented. This uses an **unreleased alpha.5 CSS source candidate**, not the
published alpha.4 release; validate changes before production use.
