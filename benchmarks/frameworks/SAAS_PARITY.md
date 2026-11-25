# Controlled SaaS dashboard benchmark (development tools only)

This is a **reproducible, controlled visual-and-functional parity scenario** for
Syntyr, Tailwind CSS v4, Tailwind v4 + daisyUI v5, and handwritten plain CSS.
It extends the existing Syntyr framework-fixture generator, source-size
inspector, CSS bundler, and Playwright metrics collection. No library files or
consumer entrypoints acquire JavaScript, Python, npm, browser, or network
runtime dependencies.

**Do not describe the outcome as “Syntyr faster than Tailwind.”** This
experiment normalizes presentation using one **shared supplemental CSS reference
sheet** (saas-parity.css) for all variants. This is useful for comparing
stylesheet overhead, markup verbosity and rendering under equalized layout,
but it suppresses differences in the frameworks' native visual styling.
It is not evidence of the best default look or fastest developer workflow.

## Repeatable setup

Run from the Syntyr repository root. The npm dependencies are locked in
benchmarks/frameworks/package-lock.json and are **benchmark-only**.

~~~sh
# The existing UnoCSS command also needs its original source fixtures.
python3 scripts/perf_framework_fixtures.py --rows 32

# Four identical semantic pages and the shared reference stylesheet.
python3 scripts/perf_saas_parity.py --prepare --rows 32

# Compile real, pinned Tailwind v4 and daisyUI CSS.
(cd benchmarks/frameworks && npm ci --ignore-scripts --no-audit --no-fund && npm run build)

# Assemble genuine Syntyr, Tailwind, daisyUI and plain CSS artifacts.
python3 scripts/perf_saas_parity.py --finalize-css

# Playwright is developer-only, never shipped to CSS consumers.
python3 -m venv /tmp/syntyr-parity-venv
/tmp/syntyr-parity-venv/bin/python -m pip install 'playwright==1.65.2'
/tmp/syntyr-parity-venv/bin/python -m playwright install chromium firefox webkit

# Use a trusted, pinned axe-core 4.11.2 copy at /path/to/axe.min.js.
/tmp/syntyr-parity-venv/bin/python scripts/perf_saas_parity.py \
  --rows 32 --runs 10 \
  --browsers chromium,firefox,webkit --viewports mobile,desktop \
  --axe /path/to/axe.min.js \
  --screenshots /tmp/syntyr-parity-shots \
  --output /tmp/syntyr-parity-report.json
~~~

A local Linux WebKit install may require system libraries or an official
Playwright image. The optional --webkit-executable PATH flag selects a
developer-supplied test-only browser wrapper for such hosts. Never silently
skip a browser and claim a three-engine pass.

For a quick smoke test use --runs 1 --browsers chromium --viewports mobile.
The --axe path may be omitted for smoke testing; the JSON then explicitly
reports accessibility as **not-run**, and the complete-gate indicator is false.
A one-run smoke test cannot justify competitive performance conclusions.

## Visual and functional parity guarantees

- One source-generated HTML tag tree, text, IDs, labels, form semantics,
  attributes, table contents and accessible live status across all four
  variants. Only styling classes and the framework CSS link differ.
- Four KPI cards, primary navigation, 32 fictional customer rows, real GET
  search, result count and a no-results state.
- One shared Python standard-library server performs case-insensitive filtering
  and escapes search text for all four variants. It is benchmark infrastructure,
  not a product backend.
- Browser checks confirm default records, keyboard Enter form submission,
  correct filtered rows, the no-results state, valid labels/landmarks, and
  absence of root horizontal overflow. The data table scrolls within its own
  named keyboard-focusable region.
- The same dev-only reference CSS normalizes spacing, typography, colors,
  controls, cards, responsive breakpoints and table sizing.
- Header, metric grid, search form and table dimensions must agree with the
  plain CSS reference within 5%; computed font size and background must match
  exactly. Missing anchors are failures. Screenshots are retained for manual
  visual inspection: this is **not pixel-by-pixel screenshot equivalence**.
- axe-core checks WCAG 2 A/AA, 2.1 A/AA, and 2.2 AA tags. Both confirmed
  violations and inconclusive results are reported separately. Manual
  keyboard, real zoom, forced colors, Safari and assistive technology review
  remain necessary.

The runner fails closed if generated pages are stale for the requested row
count or any authentic framework stylesheet is missing. It does not silently
substitute hand-authored CSS for Tailwind or daisyUI.

## What is measured

The JSON records browser versions, host environment, source fingerprints,
raw/gzip/Brotli CSS sizes, HTML bytes, total/distinct class occurrences,
class-attribute bytes, cold/warm timing medians and p75, optional Chromium
CDP style/layout metrics, visual anchor differences, overflow, and automated
accessibility findings.

**Productivity proxies** measure markup and build complexity only. Whether a
compiler is needed for the chosen distribution is recorded. Actual developer
minutes, agent tokens and maintenance-edit time are deliberately **null**.
A valid productivity study needs randomized comparable developer/agent tasks,
actual elapsed time, regression quality gates, and repeated independent trials.

**Limitations:** Tailwind and daisyUI output is tree-shaken by pinned compilers;
Syntyr uses the existing non-purged core + recipes convenience bundle. A
smaller Tailwind output therefore does not imply less authoring effort, and
a larger Syntyr bundle does not prove slower real-world navigation.
The shared reference CSS dominates many rendered styling decisions, so this
experiment does **not** compare default framework aesthetics. Localhost
serves assets uncompressed: gzip counts are *not* measured HTTP transfer size.
No external images, remote fonts, real network delays, authentic data, INP,
field Core Web Vitals, production server load or backend differences are tested.
Chromium CDP timing is unavailable in other browser engines.

Interpret performance results only after checking the gate outcome,
screenshot appearance, browser-version provenance and at least 10 repeated
trials. Zero automated axe findings do not certify WCAG conformance.

## Dependency security boundary and advisory monitoring (November 2026)

The optional development and benchmark compiler dependencies in
`benchmarks/frameworks/package-lock.json` are isolated development tools and
are not runtime dependencies of `@syntyr/css`.

**Advisory status & residual risk:** [GHSA-fc5q-39xc-vjpf](https://github.com/advisories/GHSA-fc5q-39xc-vjpf) /
[CVE-2026-112366](https://nvd.nist.gov/vuln/detail/CVE-2026-112366) originally reported
a ReDoS in `picomatch` (`<= 4.0.7`), pulled transitively by `@tailwindcss/cli`, `@unocss/cli`,
`tinyglobby`, and `@parcel/watcher`. GitHub withdrew the advisory on **November 18, 2026**.
However, withdrawal alone does not validate processing arbitrary or untrusted glob patterns;
the original affected-version report remains documented for upstream provenance.

**Bounded exposure:**
- The benchmark compiler runs strictly on controlled local repository HTML/CSS inputs.
- It is never executed against untrusted user-supplied glob patterns or in a privileged network context.
- Withdrawal is not treated as a license for unvalidated glob parsing.
- Production Syntyr CSS runtime has zero npm dependencies and is unaffected.

**Monitoring plan:**
- Track upstream `picomatch`, `@tailwindcss/cli`, and `unocss` releases and advisory state beyond passive waiting.
- Avoid forcing breaking downgrades or unverified transitive replacements that compromise lockfile integrity or parity compiler output.
- Re-run `npm audit` and benchmark visual/size parity tests as ecosystem dependencies publish updates.

## Repeatable source checks

~~~sh
python3 -m unittest discover -s tests -p 'test_saas_parity_benchmark.py' -v
python3 -m unittest discover -s tests -p 'test_framework_performance.py' -v
python3 -m unittest discover -s tests -v
python3 scripts/build.py --check
~~~
