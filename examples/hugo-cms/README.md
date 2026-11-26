# Syntyr + Hugo, driven by portable CMS content

This is a **runnable static-site starter**, separate from the existing
`experiments/hugo/` documentation-migration proof. The content source is
[the same validated JSON file](../cms-starter/content/pages/home.json)
used by Sveltia CMS, Pages CMS and the optional Decap CMS configuration.
There is no Hugo integration package, JavaScript runtime, or CMS dependency
in the published page.

## Build

From the repository root, with Python 3 and **Hugo 0.170.0** installed:

```sh
python3 scripts/build.py
python3 scripts/build_hugo_cms_starter.py --hugo hugo --output /tmp/syntyr-hugo
python3 -m http.server 8080 --directory /tmp
```

The fixture intentionally uses `https://example.com/syntyr-hugo/` to test
non-root deployments. The command above places the output under
`/tmp/syntyr-hugo/`, so open `http://localhost:8080/syntyr-hugo/`.
Use a new or empty output directory for each build. Hugo renders into a
private temporary directory. The builder verifies the generated HTML,
self-hosted stylesheets, deployment-base links, and absence of browser
JavaScript before moving the finished site into the requested directory.
For production, configure your hosting pipeline to switch to the new release
at the chosen deployment prefix only after the build succeeds. Keep the
previous release directory if you need to roll back.

For a different deployment prefix, pass your actual public base URL:

```sh
python3 scripts/build_hugo_cms_starter.py \
  --base-url https://example.com/my-site/ \
  --output /tmp/syntyr-hugo-site
```

The build stages the Hugo templates, copies the **local built** Syntyr core,
recipes and semantic stylesheets and their MIT license, validates the CMS JSON,
and copies it to Hugo's
`data/home.json` before starting Hugo. That staging directory is temporary.
The resulting output contains no editor dashboard, CMS credentials, or
unprocessed content JSON. No generator or CMS dependency is added to
`@syntyr/css`.

To use this in a standalone Hugo repository, export the default CMS preset:

```sh
python3 scripts/build_hugo_cms_starter.py --source-output /tmp/cms-source
cd /tmp/cms-source
sha256sum -c SHA256SUMS
hugo --minify --panicOnWarning
```

Supply a **pinned release** CSS directory with `--css-root` when deploying
the site independently of this source candidate. Run the portable JSON
validator before building when the content is supplied by an editor. The
builder script here automates validation for the Syntyr monorepo.

## Editing content

Use one of the Git-backed editors configured in
[the CMS starter](../cms-starter/README.md). Changes to
`content/pages/home.json` trigger a new build through your hosting provider's
Git deployment pipeline; the CMS does not deploy the site. The `id` of every
section must remain unique and stable, and the first section is the page hero.

**Important:** `0.3.0-alpha.5` is not published. This starter uses source-built
CSS. Do not imply that an npm install supplies the unpublished candidate.

The implementation is tested at Hugo v0.170.0 and v0.147.8. The
data-loading partial selects the accessor appropriate to the installed
Hugo version; builds treat warnings as errors. Keep the production
executable pinned and reverify when upgrading Hugo. This is a developer starter, not a hosted production site or
an authenticated CMS deployment.

## Durable Markdown presets

The same layouts also support three small, editable Markdown sites. The
original JSON-driven CMS remains the default; there is no editor or
JavaScript required for the Markdown presets.

| Preset | Pages |
| --- | --- |
| `personal` | About, projects and writing |
| `business` | Services and contact |
| `documentation` | Guide index and reference pages |

Export a self-contained source directory with vendored CSS (run
`python3 scripts/build.py` first if using source CSS):

```sh
python3 scripts/build_hugo_cms_starter.py --preset personal \
  --base-url https://example.org/portfolio/ --source-output /tmp/portfolio-source
cd /tmp/portfolio-source
sha256sum -c SHA256SUMS
hugo --minify --panicOnWarning
```

Use `--preset business` or `--preset documentation` for the other sites.
Use `--output /tmp/site-public` instead to stage, build and verify HTML,
local links, fragment targets, CSS, RSS, sitemap and robots output in one
step. All output modes reject nonempty existing destinations (source export
requires a completely new directory). No npm, Go modules, or framework
runtime are needed to build the exported source. Set your production
`baseURL` before deployment and use Hugo 0.170.0 as the tested version.

To run the optional no-JavaScript reflow, keyboard and navigation check
with developer-installed Playwright and Chromium:

```sh
HUGO_BIN=/path/to/hugo PLAYWRIGHT_CHROMIUM_EXECUTABLE=/path/to/chromium \
  python3 tests/hugo_starter_browser.py
```

Set `SYNTYR_HUGO_CSS_ROOT` to a local release CSS directory to test those
exact bytes. The browser tools are not required to build an exported site.

The exports use the selected local CSS bytes; `SHA256SUMS` records the
actual bytes (including the MIT license), not an asserted release version.
Standalone exports include a local README and ignore generated output;
the Syntyr license is retained in the published assets. To use an immutable release,
supply its matching, locally downloaded CSS files with `--css-root` and
verify their compatibility. The default source candidate is unpublished
alpha.5; do not represent these assets as the published alpha.4.

The Markdown preset home and section pages are implemented with native
Hugo templates. Add pages under `content/` and assign `menus: main` to
pages that should appear in the site navigation. The built-in RSS and
sitemap are enabled; a custom robots template references the canonical
sitemap. The presets include a 404 page and link metadata. Raw HTML in
Markdown is disabled by default.

For long-term preservation, keep the exported source, CSS checksums, the
exact Hugo executable and a static build archive together. For example,
on GNU/Linux from the source directory:

```sh
sha256sum -c SHA256SUMS
hugo --minify --panicOnWarning
tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner \
  -cf ../portfolio-static.tar -C public .
sha256sum ../portfolio-static.tar > ../portfolio-static.tar.sha256
```

This example archives deterministic file metadata; reproducibility still
depends on the exact Hugo version, content inputs and any time-dependent
template functions. Serve the result with any static HTTP server; links use
the configured deployment prefix, not a file:// path.
