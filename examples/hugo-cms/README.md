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
python3 scripts/build_hugo_cms_starter.py --hugo hugo --output /tmp/syntyr-hugo-site
python3 -m http.server 8080 --directory /tmp
```

The fixture intentionally uses `https://example.com/syntyr-hugo/` to test
non-root deployments. To preview it properly, serve the **output directory**
under `/syntyr-hugo/` (or copy the site to a project hosted at that path).
The builder verifies generated HTML, self-hosted stylesheets, correct
deployment-base links, and absence of browser JavaScript.

For a different deployment prefix, pass your actual public base URL:

```sh
python3 scripts/build_hugo_cms_starter.py \
  --base-url https://example.com/my-site/ \
  --output /tmp/syntyr-hugo-site
```

The build stages the Hugo templates, copies the **local built** Syntyr core
and recipes stylesheets, validates the CMS JSON and copies it to Hugo's
`data/home.json` before starting Hugo. That staging directory is temporary.
The resulting output contains no editor dashboard, CMS credentials, or
unprocessed content JSON. No generator or CMS dependency is added to
`@syntyr/css`.

To use this in a standalone Hugo repository, keep the `layouts/`, `content/`
and `hugo.toml` files, copy the JSON as `data/home.json`, and vendor a
**pinned release** of `syntyr.core.css` and `syntyr.recipes.css` under
`static/assets/`. Run the portable JSON validator before building when the
content is supplied by an editor. The builder script here automates that for
the Syntyr monorepo.

## Editing content

Use one of the Git-backed editors configured in
[the CMS starter](../cms-starter/README.md). Changes to
`content/pages/home.json` trigger a new build through your hosting provider's
Git deployment pipeline; the CMS does not deploy the site. The `id` of every
section must remain unique and stable, and the first section is the page hero.

**Important:** `0.3.0-alpha.5` is not published. This starter uses source-built
CSS. Do not imply that an npm install supplies the unpublished candidate.

The implementation is tested at Hugo v0.170.0 and should be reverified when
upgrading Hugo. This is a developer starter, not a hosted production site or
an authenticated CMS deployment.
