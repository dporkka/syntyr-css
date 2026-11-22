# Intrinsic layout compositions: inline clusters and sidecars

Syntyr uses scoped native CSS, not a JavaScript layout engine. These patterns
are available in the **unreleased alpha.5 source candidate** under
`dist/syntyr.core.css`. No additional JavaScript or CSS modules are required.

[Open the no-JavaScript composition demo](../examples/composition-adoption.html).

## Use syn-inline for a wrapping cluster

An existing `.syn-inline` is the cluster primitive; Syntyr does **not** add an
identical `.syn-cluster` alias. It wraps naturally and now exposes optional
`--syn-inline-align`, `--syn-inline-justify`, and `--syn-inline-gap` custom
properties.

~~~html
<nav class="syn-inline" aria-label="Contact filters"
     style="--syn-inline-justify:space-between">
  <a href="/contacts?status=active">Active</a>
  <a href="/contacts?status=inactive">Inactive</a>
  <a href="/contacts">All contacts</a>
</nav>
~~~

Use a real `nav` for navigation and a real `form` for filtering inputs.
The class changes layout only; it never implies tab semantics or keyboard
behavior. Existing `.syn-inline` layouts retain their default center
alignment and start justification.

## Use syn-sidecar for an intrinsic main + aside

A two-child `.syn-sidecar` puts the **main content first** and the supplementary
aside second in document and focus order. It wraps on available container width
without viewport breakpoints, JavaScript, or an explicit container query.
A lone child remains the main region and keeps the min-size and
unbroken-text overflow protections.

~~~html
<div class="syn-root syn-sidecar" data-syn-theme="studio">
  <main class="syn-panel">
    <h1>Campaigns</h1>
    <p>The principal content remains first in the accessibility tree.</p>
  </main>
  <aside class="syn-panel" aria-label="Campaign insights">
    <h2>Insights</h2>
    <p>Supplementary context.</p>
  </aside>
</div>
~~~

Custom properties belong on the layout container:

| Property | Default | Effect |
| --- | --- | --- |
| `--syn-sidecar-gap` | `--syn-space-3` | Space between regions |
| `--syn-sidecar-main-min` | `28rem` | Minimum preferred size of the main area before wrapping |
| `--syn-sidecar-aside-width` | `16rem` | Preferred width of the supplementary area |
| `--syn-sidecar-align` | `start` | Cross-axis alignment |

Do not add absolute positioning or hide the aside on small screens. CSS intrinsic
wrapping responds to the *actual available width*, including embedded sidebars,
rather than guessing from the viewport. Content may still overflow if
application-defined children use fixed dimensions; make tables and code blocks
scrollable and keyboard reachable where necessary.

## Fluid spacing and a copyable intrinsic layout cookbook (unreleased alpha.5)

Core now provides four **opt-in** fluid spacing tokens. They grow smoothly
with the logical viewport inline size between adjacent fixed tokens; the
existing `--syn-space-1` through `--syn-space-5`, default component spacing,
and density settings do **not** change.

| Fluid token | Bounded by | Typical use |
| --- | --- | --- |
| `--syn-space-fluid-1` | `--syn-space-1` to `--syn-space-2` | Tight action and chip gaps |
| `--syn-space-fluid-2` | `--syn-space-2` to `--syn-space-3` | Toolbars and form groups |
| `--syn-space-fluid-3` | `--syn-space-3` to `--syn-space-4` | Cards and content stacks |
| `--syn-space-fluid-4` | `--syn-space-4` to `--syn-space-5` | Page sections and feature grids |

`clamp()` and `vi` are handled by CSS alone. When the browser lacks logical
viewport units, the feature-gated declarations use the lower fixed bound. The
tokens depend on the **viewport**, not an element's container size: combine
them with existing intrinsic-wrapping classes to handle embedded layouts.

### Vertical stack: article or onboarding steps

~~~html
<link rel="stylesheet" href="/dist/syntyr.core.css">
<section class="syn-root syn-stack" data-syn-theme="studio"
         style="--syn-stack-gap:var(--syn-space-fluid-3)">
  <h2>Launch checklist</h2>
  <p>Publish the landing page and review the results.</p>
  <a class="syn-button" href="/checklist">Open checklist</a>
</section>
~~~

### Wrapping navigation and filter actions

~~~html
<nav class="syn-root syn-inline" aria-label="Project filters"
     style="--syn-inline-gap:var(--syn-space-fluid-1)">
  <a href="/projects">All projects</a>
  <a href="/projects?status=active">Active</a>
  <a href="/projects?status=archived">Archived</a>
</nav>
~~~

Use actual GET forms for input filters; ordinary navigation links do not need
tab roles or application-owned keyboard handlers.

### Responsive main content and complementary aside

~~~html
<div class="syn-root syn-sidecar" data-syn-theme="studio"
     style="--syn-sidecar-gap:var(--syn-space-fluid-3)">
  <main class="syn-panel">
    <h1>Project overview</h1>
    <p>Core information stays first in document and keyboard order.</p>
  </main>
  <aside class="syn-panel" aria-label="Project activity">
    <h2>Recent activity</h2>
    <p>Three updates this week.</p>
  </aside>
</div>
~~~

### Responsive feature and pricing grid

~~~html
<section class="syn-root" data-syn-theme="studio" aria-labelledby="features-title">
  <h2 id="features-title">Features</h2>
  <div class="syn-grid"
       style="--syn-grid-gap:var(--syn-space-fluid-4); --syn-grid-min:16rem">
    <article class="syn-panel"><h3>Accessible</h3><p>Real HTML controls.</p></article>
    <article class="syn-panel"><h3>Portable</h3><p>No runtime framework.</p></article>
    <article class="syn-panel"><h3>Responsive</h3><p>Intrinsic CSS grid.</p></article>
  </div>
</section>
~~~

### Optional all-or-nothing card switcher

The `syn-switcher` class is in **optional** `syntyr.recipes.css`, *not*
`syntyr.core.css`; load recipes after core to use it:

~~~html
<link rel="stylesheet" href="/dist/syntyr.core.css">
<link rel="stylesheet" href="/dist/syntyr.recipes.css">
<div class="syn-root syn-switcher" data-syn-theme="studio"
     style="--syn-switcher-threshold:42rem; gap:var(--syn-space-fluid-2)">
  <article class="syn-panel"><h2>Starter</h2><p>For small teams.</p></article>
  <article class="syn-panel"><h2>Growth</h2><p>For busy teams.</p></article>
  <article class="syn-panel"><h2>Scale</h2><p>For large teams.</p></article>
</div>
~~~

These snippets are original MIT examples. They work with no JavaScript and
can be reordered in source; moving blocks in the DOM also changes reading and focus
order. Use semantic headings, named navigation, descriptive link text, and
visible focus indicators. Content with fixed widths, long tables, or code may
need separate overflow handling. Test zoom, RTL, and embedded widths before
shipping. CSS does not fetch data, virtualize cards, or implement infinite
loading.

## Import only what you need

For no-build consumers, the preferred option is one self-hosted
`syntyr.core.css` stylesheet. For selective component loading, use the
prebuilt CSS files in order: `components/tokens.css`,
`components/base.css`, then `components/layout.css` and any additional
components. Do not load core and these component files together. The
`form-composition` module also needs `forms`.

The `--syn-inline-*` and `--syn-sidecar-*` properties are public
customization points; they do not require an app-side CSS compiler.
Syntyr's optional [selective builder](selective-builds.md) can assemble
a single stylesheet without scanning templates or purging dynamic classes.

See the [Go server-rendered starter](https://github.com/dporkka/syntyr-css/tree/main/examples/go-htmx) for a
working app whose native GET route can optionally return HTMX fragments.
Application state, accessibility behavior and data authorization always
belong to the host, not to these layout classes.

For optional browser verification, run `python3 tests/composition_adoption_browser.py`
from a checkout with Playwright and browser engines installed. It checks
wide, narrow, and embedded widths; WebKit needs its native system dependencies.
The release CSS and the example itself do not require Playwright.
