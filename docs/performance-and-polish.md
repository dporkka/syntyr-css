# Syntyr performance and design guidance

Syntyr is a scoped, CSS-first visual library with no runtime JavaScript, no
fonts downloaded by default, and no required package manager. Optimize
**real browser behavior** rather than targeting an arbitrary gzip byte count.

## Inspect stylesheet sizes without blocking releases

```sh
python3 scripts/build.py --check
python3 scripts/asset_report.py
python3 scripts/asset_report.py --json > /tmp/syntyr-sizes.json
python3 scripts/asset_report.py --baseline /tmp/syntyr-sizes.json
```

The report shows deterministic raw and gzip transfer sizes for every actual
distribution. A prior JSON report can be supplied to show signed size deltas.
Both increasing and decreasing sizes are diagnostic: **there is no 5 KiB or
8 KiB pass/fail limit**. A useful feature should not fail merely because of
compressed bytes. Instead, investigate surprising jumps and measure real
LCP, CLS, INP, style recalculation, and paint cost in production-shaped pages.

For resource priority, LCP images, optional critical CSS experiments and
cold/warm loading comparisons, see the [progressive-loading guide](progressive-loading.md)
and [performance-first example](../examples/performance-first.html).

On the Syntyr Cloudflare documentation site, generated HTML uses
content-addressed immutable CSS copies for better repeat navigation caching;
the public `/dist/*` and versioned release URLs keep their existing
contracts. See [Cloudflare hosting](cloudflare-hosting.md).

Start with `syntyr.core.css` alone. Add `syntyr.recipes.css`,
`syntyr.semantic.css`, or effects only when the application uses them.
Do not include both `syntyr.all.css` and its individual modules. Prefer
same-origin, cacheable stylesheets to an extra CDN hostname in most apps.

## Zero-JS visual accents

Optional recipes add depth and a stronger visual hierarchy without extra DOM,
canvas, web fonts or animations:

```html
<link rel="stylesheet" href="/css/syntyr.core.css">
<link rel="stylesheet" href="/css/syntyr.recipes.css">
<section class="syn-root syn-region" data-syn-theme="studio">
  <article class="syn-app-card syn-surface--accent syn-surface--lift">
    <label class="syn-label" for="search">Find an account</label>
    <input class="syn-input" id="search" name="q" type="search">
  </article>
</section>
```

- `syn-surface--accent` adds a token-colored inset top rule and subtle surface
  tint. It can be used on panels, cards and other bordered surfaces.
- `syn-surface--lift` adds a modest hover/focus treatment on capable pointers,
  without transforms or persistent `will-change`. Use sparingly, mainly where
  cards contain interactive elements. It does not make a card clickable.
- The visual system adapts to any of the twelve theme palettes; forced-colors
  mode uses a visible border instead of relying on shadows.
- These are optional recipes, **not baseline component appearance changes**.

The original Grid/Noir aesthetic can remain technical; Studio/Corporate/Minimal
should feel restrained. Use typography hierarchy, consistent spacing and
purposeful accent color before adding glow, gradients or large shadows.

## Opt-in long-page render deferral

```html
<!-- Only below-the-fold sections of sufficiently long, dense pages. -->
<section class="syn-defer-section" style="--syn-defer-size: 42rem">
  <h2>Archive</h2>
  <!-- expensive table, logs or reporting visuals -->
</section>
```

`syn-defer-section` applies `content-visibility: auto` with a tunable
`contain-intrinsic-size` placeholder. The browser can skip layout and paint
for offscreen content until needed; actual benefit depends on DOM structure
and the browser. Printing restores full visibility. Choose an approximate
intrinsic block size based on actual content to reduce layout shifts.

**Do not** indiscriminately defer the hero/LCP content, small pages, open
dialogs, active focus targets, or containers whose height is critical to
navigation. It isn't virtualization and doesn't reduce network/DOM memory.
Measure on real pages before adopting it broadly.

## Repeatable, offline rendering benchmark

Syntyr ships a **developer-only** Playwright harness. It generates two
production-shaped synthetic layouts — a SaaS dashboard and a long-table page —
using the *same* core + recipes CSS and equivalent DOM. The only experimental
difference is whether independent, below-the-fold sections opt in to
`syn-defer-section`.

```sh
# Optional developer environment only; never required to consume Syntyr.
python3 -m venv /tmp/syntyr-playwright
/tmp/syntyr-playwright/bin/pip install playwright
/tmp/syntyr-playwright/bin/playwright install chromium firefox webkit

/tmp/syntyr-playwright/bin/python scripts/perf_benchmark.py \
  --browsers chromium,firefox,webkit --runs 3 --rows 1200 --sections 12 \
  --output /tmp/syntyr-browser-performance.json
```

The harness uses desktop (1365px) and **mobile-width** (390px) viewports,
a warm-up round, rotated variant ordering, and median timings. It measures
navigation, browser-reported FCP/LCP where exposed, non-input CLS where
supported, forced theme restyling, and a synthetic scroll reveal into a late
section. Chrome/Chromium also exposes CDP style-recalculation and layout
durations. **Paint duration is not available from the CDP metrics API used
here**, so `paint_ms` remains null; missing browser metrics are not reported
as zero. This does not measure real-user INP, network RTT, mobile device CPU
or field Web Vitals.

The script returns a nonzero status and records `blocked` when a requested
browser cannot launch. Firefox and WebKit must actually run to count as
covered; do not treat installed browser files as successful execution.
Cross-browser absolute timings are not comparable because their engines and
instrumentation differ. Compare only the standard/deferred pair on the same
engine, fixture, viewport and machine. Use a production-like CPU and data
volume before making release decisions.

**Trade-off:** faster first paint may defer work until the user scrolls.
Compare `scroll_reveal_ms` and `scroll_cls` as well as `navigation_ms`,
and tune `--syn-defer-size` to approximate real sections. Real-user
monitoring and mobile-device traces still take priority.

### Local result: November 14, 2026

Three measured rounds after one warm-up, 1,200 records, 12 regions, on one
Linux development machine. Versions: Chromium 156.0.8078.4, Firefox 159.0,
WebKit 27.2. Entries below are **median synthetic navigation times**, not
field Core Web Vitals. Lower is better.

| Engine / long-table viewport | Standard | Deferred | Change |
| --- | ---: | ---: | ---: |
| Chromium / 1365px | 75.0 ms | 55.9 ms | 26% faster |
| Chromium / 390px | 91.5 ms | 54.8 ms | 40% faster |
| Firefox / 1365px | 142.9 ms | 119.1 ms | 17% faster |
| Firefox / 390px | 144.2 ms | 107.7 ms | 25% faster |
| WebKit / 1365px | 254.0 ms | 196.3 ms | 23% faster |
| WebKit / 390px | 227.7 ms | 183.5 ms | 19% faster |

**Counterexample:** the Firefox desktop *dashboard* navigation median
was **132.1 ms standard versus 144.9 ms deferred** (10% slower), even while
its synthetic FCP improved. Do not assume that the opt-in hint helps every
page or every measurement.

In these runs, Chromium reported zero cumulative layout shift initially
and after the late-section scroll reveal, while Firefox and WebKit did not
expose the same layout-shift entries (reported as `null`, not zero).
Median synthetic scroll-reveal times were generally around 25–30 ms on
these local fixtures; some comparisons modestly favored the standard
variant. The text-only content can make synthetic LCP equal FCP; neither
captures image-heavy production pages. No claim is made about real-world
INP or paint duration.

**Decision:** retain render deferral as an opt-in tool for large independent
below-fold sections, not a default applied to all components. Benchmark
again with the consuming application's actual DOM and realistic viewport,
content sizes, network and CPU constraints.

## Developer-experience contract

- Native HTML first. Use existing `syn-*` classes and `--syn-*` tokens.
- Respect focus rings, disabled states, form semantics, reduced motion,
  color contrast, and forced colors.
- Keep framework-specific request/DOM logic in HTMX/React/Alpine/etc., not CSS.
- Use committed deterministic CSS; the stdlib Python build is for maintainers.
- Test actual browser rendering and zoom, not only compressed file size.

See [framework integrations](framework-integrations.md),
[theme customization](theme-customization.md) and
[component contract](components.md).
