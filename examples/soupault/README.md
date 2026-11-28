# Syntyr + Soupault (optional HTML processor)

An existing, handwritten two-page HTML site uses the unreleased alpha.5
candidate's scoped semantic bundle. Soupault inserts a local stylesheet
link into each document head by selector, without changing the page's
content or requiring any client JavaScript. The author explicitly opts in
with `syn-root syn-semantic` on the desired region.

Install Soupault from its [official releases](https://soupault.net/install/).
From the repository root:

```sh
python3 scripts/build.py --check
cd examples/soupault
mkdir -p site/assets
cp ../../dist/syntyr.semantic-bundle.css site/assets/
soupault
python3 ../../scripts/verify_static_generators.py build --base-path /syntyr-soupault/
```

Serve the `build/` directory at the declared `/syntyr-soupault/` mount
(including nested routes); change the stylesheet prefix in soupault.toml and
the verification argument together for another mount. This example is a
trusted local configuration, not a generic HTML sanitizer or rewrite service.
Soupault is optional build-time tooling and is not used by the CSS core, the
documentation site build, or consumer browsers.
