# Reproducible framework performance comparison (experimental)

This optional developer-only benchmark compares Syntyr, handwritten plain CSS,
Pure.css, Tailwind CSS v4, UnoCSS, and daisyUI 5 (built as a Tailwind v4 plugin). Syntyr consumers need none of these
npm/Python development tools.

**Not a fastest-framework ranking.** The variants preserve document structure,
text and application data, but use idiomatic CSS frameworks and are not
pixel-identical. Pure requires small layout styles because it does not supply a
complete dashboard system. Therefore style, layout and LCP comparisons are
confounded by visual differences. Inspect warnings and screenshots before
drawing conclusions; further visual parity is necessary for speed claims.

For a controlled **SaaS dashboard** comparison across Syntyr, Tailwind v4, Tailwind+daisyUI and plain CSS, including actual GET filtering, shared visual normalization, browser checks and optional axe-core, see [the dedicated parity benchmark](../benchmarks/frameworks/SAAS_PARITY.md). It makes different tradeoffs from the idiomatic styling benchmark below and cannot support a universal framework-speed ranking.

## Preparation

From the repository root:

~~~sh
# Standard-library fixture generation (no network or third-party dependencies).
python3 scripts/perf_framework_fixtures.py --rows 120

# Compiler dependencies are benchmark-only and pinned by package-lock.json.
cd benchmarks/frameworks
npm ci --no-audit --no-fund --ignore-scripts
npm run build
cd ../..

# Bundle actual vendor CSS. Missing dependencies fail explicitly.
python3 scripts/perf_framework_fixtures.py --css

# Install developer-only Python Playwright in a disposable environment.
python3 -m venv /tmp/syntyr-benchmark-venv
/tmp/syntyr-benchmark-venv/bin/pip install playwright
/tmp/syntyr-benchmark-venv/bin/playwright install chromium firefox webkit

/tmp/syntyr-benchmark-venv/bin/python scripts/perf_framework_compare.py \
  --runs 10 --browsers chromium,firefox,webkit \
  --viewports mobile,desktop --fixtures marketing,dashboard \
  --screenshots /tmp/syntyr-framework-shots \
  --output /tmp/syntyr-framework-report.json
~~~

For a quick smoke test, use --runs 2 --browsers chromium. A blocked browser
launch is a failure to validate that lane, not evidence of compatibility.

The benchmark-only `daisyui@5.8.0` dependency is pinned in the nested lockfile.
It is **not** installed by Syntyr core or included in browser-facing Syntyr
CSS. The compiler uses the actual daisyUI Tailwind 4 plugin with a single
light theme and the same HTML tags and content as all five other fixtures.

Generated CSS/HTML, node_modules and browser artifacts are not committed to
Syntyr or included in its release. Pure, Tailwind, Uno and daisyUI are independent
third-party frameworks; their source licenses remain with their authors.

## Measurements and methodological limits

- Two page shapes: marketing and a dashboard with four KPI cards, search
  form and a configurable campaign table.
- The exact same semantic tag tree, meaningful attributes and text for each
  variant. Styling classes and local stylesheet paths intentionally differ.
- Local HTTP caching of CSS and uncached HTML; cold means a fresh browser
  context and warm means a second navigation in that same context.
- Rotation of trial order, median and nearest-rank p75 across repeated runs
  for each browser, viewport, fixture and cache condition.
- Browser-reported FCP, LCP and CLS where supported (unavailable = null).
- Browser Resource Timing total transfer bytes (localhost CSS is not
  HTTP-compressed) and navigation wall time.
- Chromium CDP style recalculation and layout durations; Firefox and WebKit
  report null for these values. Paint is not measured.
- Raw/gzip CSS asset sizes and optional Brotli asset sizes if the Python
  brotli module is installed. These are not actual HTTP transfer sizes.
- Raw HTML byte length, literal class counts, unique classes, and bytes in
  `class` attribute values for each fixture/framework. These values measure
  source verbosity, **not** actual LLM tokens, agent correctness, or agent cost.
- Screenshot files and stable visual anchor bounding rectangles.
  geometry_warnings flags width/height differences exceeding 20% relative
  to the reference; absence of warnings does not imply pixel parity.

The Playwright measurement script injects instrumentation in test contexts;
the generated application pages themselves have no JavaScript. The fixture
uses no external assets, remote fonts, images, or icons. It does not model
production image loading or optional Grid/Noir cinematic effects.

## Interpretation requirements

1. Match the browser, viewport, CPU/network settings, assets and actual
   layout before inferring any comparative win. Document Syntyr commit,
   package lock, browser versions, host configuration and throttling.
2. Read geometry_warnings and screenshots first. Different visual spacing,
   controls and table row heights can alter rendering costs dramatically.
3. Use at least 10 runs and report median and p75, not the fastest run.
4. For paint/compositor work, capture separate Chrome/Firefox performance
   traces; style recalculation is not paint cost or real-user INP.
5. Never treat gzip sizes as real HTTP transfer bytes, or local synthetic
   LCP/CLS as real-world Core Web Vitals.
6. This is an apples-to-apples **semantic DOM** comparison, not a controlled
   experiment with separately prompted coding agents. Do not claim agent
   superiority without a task corpus, blinded model runs, actual framework
   compilations, accessibility scans, and repeated paired comparisons.
7. This is experimental comparison infrastructure, not a Syntyr runtime,
   compiler dependency or required release gate.

See [performance validation](performance-validation.md),
[render deferral](performance-and-polish.md) and
[progressive loading](progressive-loading.md) for complementary benchmarks.

## Verification

~~~sh
python3 -m unittest discover -s tests -p 'test_framework_performance.py' -v
python3 scripts/build.py --check
~~~

The contract tests check deterministic generation, semantic structure,
metric statistics, missing-compiler error handling and visual mismatch
reporting. Run the actual browsers to verify runtime behavior.
