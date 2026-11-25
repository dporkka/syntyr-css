# Syntyr + Eleventy (optional static-site fixture)

This example uses Eleventy 3 at **build time only**. No dependency is added
to Syntyr itself, and the generated site contains no client JavaScript.

From the repository root, first verify the prebuilt CSS with
`python3 scripts/build.py --check`. Then:

```sh
cd examples/eleventy
npm install
npm run build
npm run verify
```

The config directly copies `../../dist/syntyr.core.css` into the output
`assets/` folder; no npm version of `@syntyr/css` is required. The Nunjucks
`url` filter and `pathPrefix` exercise a GitHub Pages-style subpath
(`/syntyr-eleventy/`). Change the prefix for your deployment, or use `/`
for a root deployment. Serve `_site/` under that prefix and ensure the CSS
is present. To test locally at the root, set `pathPrefix: "/"` in the config
and rebuild. Also update the --base-path argument in the package.json verify
script to match the new pathPrefix (including / for root deployment).
Never add Syntyr's bundle and its core stylesheet together.

The local example is not a Syntyr documentation-site migration and is not
included in the published CSS package.
