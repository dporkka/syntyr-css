# SaaS Admin Starter

Four ready-to-copy pages using the **unreleased Syntyr alpha.5 source candidate**.
No runtime JavaScript, framework, remote assets, API, backend or payment processor.

Open [Overview](index.html), [Pipeline](pipeline.html), [Customers](customers.html)
and [Billing](billing.html). Each page is a complete HTML document with shared
navigation, responsive page-specific CSS, and Syntyr core/recipe styles.

## Reuse

Copy the four HTML files, styles.css, and README.md into your app so all internal
links, including "Implementation notes", remain valid. Update stylesheet paths
to the matching `dist/syntyr.core.css` and `dist/syntyr.recipes.css` release
candidate assets. The currently published alpha.4 package is **not** guaranteed
to contain the source-candidate APIs this template uses.

## Deploy the isolated template

From the Syntyr repository root, produce a self-contained, explicit allowlist:

```sh
python3 scripts/build_saas_admin_starter.py
python3 scripts/build_saas_admin_starter.py --check
python3 -m http.server 8080 --directory .saas-admin-public
```

Open http://localhost:8080. The publisher moves the CSS to `assets/` and
rewrites the four HTML stylesheet links. It includes only the template pages,
three CSS files, README, license, a robots rule and a build manifest. No repo-root
publishing, environment variables, business data, build-time secrets, JavaScript
dependencies, or service APIs. Generated output is gitignored, deterministic,
and safe against overwriting unrelated output directories.

### Git-connected deployment

- **Vercel**: [Deploy this repository](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fdporkka%2Fsyntyr-css) or import it through the Vercel dashboard. Set Root Directory to the **repository root**. Root `vercel.json` runs the build and publishes `.saas-admin-public`. Do not set the Root Directory to this example folder.
- **Netlify**: [Deploy this repository](https://app.netlify.com/integration/start/deploy?repository=https://github.com/dporkka/syntyr-css) or import it through the Netlify dashboard. Choose the **repository root**; `netlify.toml` uses the same Python build and publish path.
- **Render**: choose **New → Blueprint** on this repository. Root `render.yaml` defines a static site with the same build command and publish directory. Alternatively, create a Static Site and enter those values manually.

These root-level host configs publish **only the SaaS Admin Starter**. They do
not replace the existing Syntyr documentation site's Cloudflare release process.
The preview is explicitly non-indexable; remove that policy for your own
publicly indexable site only after reviewing your content and SEO metadata.

### Direct/static deployment

- **Cloudflare Pages**: run the build command above and upload the
  `.saas-admin-public` directory via Pages Direct Upload, or use:
  `npx wrangler pages deploy .saas-admin-public --project-name=YOUR_PROJECT`
  with an authorized Cloudflare account and your own Pages project. Do **not**
  overwrite Syntyr's existing public documentation project.
- **GitHub Pages**: publish the generated files at the root of a separate
  `gh-pages` branch/repository (and select that branch in Pages settings).
  The output contains real `.html` routes; no SPA fallback or GitHub Actions
  workflow is necessary. Never publish the source repository root.
- **Any static server** (Caddy, Nginx, object storage/CDN, S3-compatible host):
  upload only the generated `.saas-admin-public` files to the web root and
  serve `index.html` for `/`; keep normal `.html` routes. No SSR required.

## Integration contract

- All names, dates, metrics, money and statuses are fictional.
- Internal links work; data mutations, sign-in and invoice downloads do not exist.
- The Customers `GET` form sends query parameters to `customers.html`, but the
  static preview does **not** apply filters. On a server, validate/encode inputs,
  escape outputs, preserve form values, paginate and enforce tenant-scoped access.
- Pipeline status is read-only. Implement stage changes and audit trails in the host.
- Subscription management is disabled. Only enable after building authorized
  billing sessions, signature-checked idempotent webhooks and entitlement checks.
- Preserve skip links, captions, labels, keyboard scrolling, focus, reduced motion,
  forced-colors behavior, and zoom/reflow support.

Run `python3 -m unittest discover -s tests -p test_saas_admin_starter.py -v`
and `python3 -m unittest discover -s tests -p test_saas_admin_deploy.py -v`
to validate the template and deployment contract. MIT licensed.
