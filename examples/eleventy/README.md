# Syntyr + Eleventy (optional static-site fixture)

Eleventy 3 renders the same portable CMS JSON landing page as the existing
Python, Hugo and Astro starters, with an independent Nunjucks template.
The build uses Syntyr's canonical, bounded UTF-8 JSON loader and page
validator before passing data to the template. Duplicate keys, non-finite
numbers, invalid Unicode and invalid page fields fail before templating. Nunjucks escapes
text and attributes; no raw CMS HTML is inserted.

From the repository root, verify the prebuilt CSS with
`python3 scripts/build.py --check`. Then:

```sh
cd examples/eleventy
npm ci
npm run build
npm run verify
```

The config copies the core and recipes CSS from `../../dist/` into
`_site/assets/`, without requiring an npm release of `@syntyr/css`. The example dependency
lockfile is maintainer-only; `npm ci` keeps the fixture reproducible.
The Nunjucks `url` filter and `pathPrefix` exercise project-pages subpaths
(`/syntyr-eleventy/`); the local CMS URL filter uses that same prefix.
Edit the prefix and the package.json verifier's `--base-path` together
for another deployment. Serve `_site/` under the configured prefix.

The verifier compares the actual generated document to the canonical CMS
renderer, including ordered blocks, text, native HTML, ARIA, class names
and deployment-aware links. It also checks local CSS and zero browser JS.
This is a candidate-only, optional fixture, not a documentation-site
migration, and is not included in the published CSS package.
