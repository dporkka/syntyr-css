# Syntyr theme customization — copy, override, ship

Syntyr themes are **CSS custom properties**, not JavaScript configuration.
The MIT core already includes Grid and Noir palettes, responsive primitives,
accessible focus styling and semantic element options.

## 1. Choose a theme

Without a `data-syn-theme` attribute, `.syn-root` now uses Studio. Select Grid or Noir explicitly for technical/cinematic styles. This change is only in the unreleased alpha.5 candidate; version-pinned alpha.4 assets remain unchanged.

Load the published `syntyr.core.css` in your application and use regular HTML:

```html
<link rel="stylesheet" href="/css/syntyr.core.css">
<section class="syn-root" data-syn-theme="grid">
  <article class="syn-panel syn-panel--cut">
    <h2 class="syn-heading">Sector status</h2>
    <button class="syn-button syn-button--primary">Open</button>
  </article>
  <aside data-syn-theme="noir" class="syn-panel">
    Nested Noir preview
  </aside>
</section>
```

Use `data-syn-theme="noir"` for warm amber. Native HTML features
such as `details`, `dialog` and `popover` don't need framework JavaScript.

## Copyable theme presets (alpha.5 documentation tool)

The [theme editor](theme-editor.html) now previews independently selectable
theme, visual intensity, control density, and radius, and generates both CSS
overrides and a portable JSON preset. Copy the JSON into an application-owned
design configuration or use the CSS immediately. The JSON is declarative
metadata, not an executable preset installer, stylesheet, or published API.
For density/intensity, apply the indicated `data-syn-density` and
`data-syn-intensity` attributes on the Syntyr scope. A custom radius uses
`--syn-radius` and `--syn-panel-radius`; the default option preserves each
base theme's geometry. The editor also supports **site-wide color roles** (background, card surface,
primary/secondary text, accent, on-accent), three system-font typography
pairings (default, editorial, technical), and three spacing rhythms
(balanced, tight, airy). The page preview includes header, feature,
form and footer sections; it is a visual sample, not a live deployment.
Generated CSS uses only the existing `--syn-*` variables. The optional
JSON preset retains `schema_version: 1` and adds `typography` and
`spacing` metadata; older consumers may ignore these optional fields.
Typography uses locally available system fonts, not network-loaded files.

Color changes are scoped to the selected theme. Switching themes resets
the six color inputs to that palette's values but preserves your selected
typography, spacing, radius, intensity and density; the **Reset palette
colors** action does the same. The contrast indicators inspect button
foreground, body text on both background and surface, and muted text on
surface. They are advisory; other contrast combinations, graphics and focus
states require testing in the consuming application.

The documentation script and clipboard enhancement are
not included in Syntyr's distributed CSS. Test the resulting palette and
control contrast in the consuming application.

## 2. Override tokens using application CSS

Syntyr declares its defaults in named cascade layers. App CSS without a
layer takes precedence over layered author rules regardless of selector specificity.
Load application overrides **after** the Syntyr stylesheet to reduce surprises:

```css
/* app.css: original tokens, not copied from existing entertainment IP. */
.syn-root[data-syn-theme="grid"] {
  --syn-accent: #80dfef;
  --syn-on-accent: #07121a;
  --syn-accent-soft: rgb(128 223 239 / 10%);
  --syn-frame: #34576c;
}

/* Override one nested region without affecting the rest of the site. */
.my-warning-panel {
  --syn-surface: #1b232d;
  --syn-warning: #ffe2aa;
}
```

Important: `--syn-accent` is the most visible token, but `--syn-on-accent`
is the contrasting **foreground on primary buttons**. Change both when
necessary. Verify 4.5:1 contrast for body text and 3:1 for essential non-text
graphics; don't assume arbitrary overrides remain accessible.

Primary-button hover backgrounds default to the unchanged accent. On hover,
the border switches to the contrasting foreground for a visible affordance.
To customize the hover fill, set `--syn-primary-hover-bg` on the desired
theme/root and test its contrast with `--syn-on-accent` in both rest and hover
states. Syntyr does not automatically invent a contrast-safe hover color.

Use `.syn-panel--raised` for opt-in elevation. The `.syn-title`/`.syn-display`
and `.syn-section-heading` roles use native `text-wrap: balance` when
supported; unsupported browsers fall back to ordinary line wrapping.
Syntyr leaves platform font smoothing untouched.

Useful tokens:

| Token | Description |
| --- | --- |
| `--syn-bg` | Main background |
| `--syn-surface`, `--syn-surface-hi` | Cards and controls |
| `--syn-text`, `--syn-muted` | Main and secondary text |
| `--syn-accent`, `--syn-on-accent`, `--syn-accent-soft` | Brand accent, its foreground, soft fill |
| `--syn-frame`, `--syn-danger`, `--syn-success`, `--syn-warning` | Borders and status |
| `--syn-font`, `--syn-mono`, `--syn-font-ui`, `--syn-font-display` | Body, technical, control, and display typography |
| `--syn-type-xs`, `--syn-type-sm`, `--syn-type-base` | Typography sizes |
| `--syn-surface-recessed`, `--syn-surface-raised`, `--syn-border-subtle` | Derived surfaces and quiet separators |
| `--syn-text-subtle`, `--syn-border-default`, `--syn-border-hover`, `--syn-border-focus`, `--syn-focus-ring` | Semantic text, borders, and focus |
| `--syn-surface-interactive`, `--syn-surface-hover`, `--syn-surface-pressed` | Theme-aware interactive control states |
| `--syn-primary-hover-bg` | Primary-button hover background; defaults to the accent so foreground contrast does not regress |
| `--syn-shadow-sm`, `--syn-shadow-raised`, `--syn-shadow-overlay` | Semantic elevation (small surfaces, raised panels, floating overlays) |
| `--syn-type-display`, `--syn-type-section`, `--syn-type-heading`, `--syn-type-body`, `--syn-leading-body`, `--syn-tracking-display` | Composable typography roles |
| `--syn-row-padding-block`, `--syn-card-padding`, `--syn-control-padding-block` | Density-aware spacing |
| `--syn-space-1` … `--syn-space-5` | Spacing |
| `--syn-page-gutter`, `--syn-content-max` | Responsive `.syn-shell` and application workspace gutters |
| `--syn-content-gap`, `--syn-section-space` | Shared grid/form/section rhythm (local gap overrides still work) |
| `--syn-display-measure`, `--syn-section-heading-measure`, `--syn-site-heading-measure` | Optional heading line-length overrides without changing semantic type roles |
| `--syn-cut`, `--syn-radius`, `--syn-control-height` | Geometry |
| `--syn-duration-fast`, `--syn-duration-standard`, `--syn-ease`, `--syn-ease-enter` | Optional transitions |
| `--syn-panel-padding`, `--syn-panel-radius`, `--syn-panel-border-width` | Local panel customization |
| `--syn-button-padding-inline`, `--syn-button-border-width` | Local button customization |

### Page widths, stack rhythm, and density

Use the built-in `.syn-shell` for centered content. Its default maximum is
`72rem`, with fluid `--syn-page-gutter` (at least `1rem` per side). Set
`--syn-content-max` on a Syntyr scope for editorial pages, wide dashboards, or
embeds rather than copying a hard-coded width into every theme. Shared
`--syn-content-gap` is the fallback for `.syn-grid`, `.syn-layout`,
`.syn-feature-grid`, and `.syn-form`; the existing `--syn-grid-gap` and
`--syn-layout-gap` local overrides still take priority. `--syn-section-space`
controls site-hero vertical padding and can be overridden per page.

```html
<main class="syn-root syn-page" data-syn-theme="studio"
      style="--syn-content-max: 64rem; --syn-content-gap: 1.5rem">
  <div class="syn-shell">
    <section class="syn-stack" aria-labelledby="intro-title">
      <h1 id="intro-title" class="syn-display">An accessible interface</h1>
      <p class="syn-lede">Shared rhythm across every Syntyr palette.</p>
    </section>
  </div>
</main>
```

An intentional `.syn-stack` or `.syn-u-stack` owns its direct-child vertical
spacing: native heading and paragraph margins are suppressed, so they do not
add to the declared grid gap. Paragraphs *inside* `.syn-prose` retain their
reading rhythm; utilities and app CSS can still add explicit separation.
Do not globally reset margins in arbitrary host markup.

`data-syn-density="compact"` and `"spacious"` also change `.syn-panel`
padding; a nested `"comfortable"` region restores the regular fluid value.
Density never shrinks font sizes. At narrow widths, verify labels, controls,
and actions reflow without horizontal page scroll; do not infer accessibility
solely from a good desktop screenshot.

## 3. Independent visual intensity

Use `data-syn-intensity="quiet"` on a dense dashboard, the default `standard` for a balanced presentation, or `cinematic` on a limited hero region. Intensity controls only opt-in decoration in `syntyr.effects.css`; it does not alter palette, density, typography or control contrast. Nested regions can override an inherited value. See the [visual-intensity guide](visual-intensity.md) and [live comparison](../examples/intensity-geometry.html).

## 4. CSS component mode versus native semantic mode

Scoped component classes: `.syn-panel`, `.syn-button`, `.syn-table`.
They work with only `syntyr.core.css`.

For classless HTML resembling Pico CSS, load **both** files and opt in:

```html
<link rel="stylesheet" href="/css/syntyr.core.css">
<link rel="stylesheet" href="/css/syntyr.semantic.css">
<div class="syn-root syn-semantic" data-syn-theme="noir">
  <article>
    <h2>Operator access</h2>
    <label for="operator">Operator ID</label>
    <input id="operator" name="operator" required>
    <button>Continue</button>
  </article>
</div>
```

Unclassed controls outside `.syn-semantic` are not restyled.
If you need glows or static grid effects, add `syntyr.effects.css`
as a third optional file. Don't load `syntyr.all.css` **and** its
individual component files at the same time.

## 5. Responsive applications and accessibility

Use `.syn-region` as the parent for container-responsive patterns such as
`.syn-stats`, `.syn-split`, `.syn-pricing`; width comes from the container,
not the whole viewport. Use `.syn-page` only for a full-page experience.

Syntyr also honors `prefers-contrast: more` by strengthening tokenized borders
and suppressing nonessential decorative effects, including inside nested
themes and explicit cinematic-intensity regions. This is a preference-aware
visual enhancement, not a substitute for actual high-contrast/forced-colors,
zoom, and screen-reader testing.

Syntyr honors `prefers-reduced-motion: reduce`. Theme overrides
must not remove focus outlines, fake disabled states, or communicate state
only through color. Test keyboard navigation, 200%/400% browser zoom,
high-contrast/forced-colors, and relevant screen readers in the target app.

**No runtime JavaScript is required for styling.** Search, authentication,
live data, and server-side form handling are intentionally application
responsibilities; optional advanced widgets are outside the CSS core.

## Seven theme palettes (unreleased alpha.5 candidate)

The published alpha.4 tag offers Grid, Noir and Studio. This candidate adds Industrial, Terminal, Corporate and Minimal. Use the same HTML and change only the theme attribute:

- `data-syn-theme="grid"`
- `data-syn-theme="noir"`
- `data-syn-theme="studio"`
- `data-syn-theme="industrial"`
- `data-syn-theme="terminal"`
- `data-syn-theme="corporate"`
- `data-syn-theme="minimal"`

To use finite opt-in layout utilities, load `syntyr.utilities.css` after `syntyr.core.css` (or use the all bundle). Utilities include `.syn-u-flex`, `.syn-u-grid`, `.syn-u-between`, spacing helpers and a visually hidden helper. No compiler or runtime JavaScript is required.


## System palette, no JavaScript (experimental)

`data-syn-theme="auto"` on `.syn-root` or a nested themed region
uses Studio colors for light system preference and Grid colors for dark
system preference. It relies on native `color-scheme: light dark` and
CSS `light-dark()`, supported by current Chromium, Firefox and WebKit.
Older engines that lack `light-dark()` retain the inherited/default
palette. No preference is stored or read by Syntyr.

```html
<body class="syn-root syn-page" data-syn-theme="auto">
  <section data-syn-theme="noir">This remains Noir regardless of OS theme.</section>
</body>
```

Explicit palettes are unchanged. For sensitive applications, test nested
themes, native form controls, and contrast in both OS preference modes.
## Typography, density, and quiet surfaces

Control and navigation text uses `--syn-font-ui`. Display headings use
`--syn-font-display`, while code and CLI regions retain `--syn-mono`.
Grid and Terminal choose monospace UI explicitly; Studio is the implicit default; light themes and Noir use
system sans-serif controls. Replace the font variables if a product has its
own typeface, without introducing required external fonts.

The `--syn-surface-recessed`, `--syn-surface-raised`, and
`--syn-border-subtle` tokens derive from the active theme palette and
recompute in nested themed regions. Strong borders remain available for
focus and essential controls. Avoid treating subtle separators as a substitute
for accessible non-text contrast where boundaries are required.

To opt into compact operational layouts:

```html
<section class="syn-root" data-syn-theme="minimal" data-syn-density="compact">
  <table class="syn-table"><!-- ... semantic rows ... --></table>
</section>
```

Compact density reduces padding and control heights, **not font sizes**.
Use the default density for content-heavy business pages or touch-first forms.
For an optional editorial hero, combine `syn-site-heading--editorial` from
`syntyr.recipes.css` with `syn-gradient-wash` from `syntyr.effects.css`.
Both use local fonts and static CSS without runtime dependencies.


## Semantic roles, states, and content rhythm

Use `.syn-display` (also available as `.syn-title`), `.syn-section-heading` for section titles, `.syn-heading` for card headings,
`.syn-body`, `.syn-text-support`, and the opt-in `.syn-prose` content
container. Typography roles inherit theme fonts and allow applications to
override type scale without rewriting individual component selectors.

Semantic aliases are derived separately in each nested `data-syn-theme`
scope, so a Grid panel inside a Studio page retains Grid's own contrast and
control appearance. To override theme colors, prefer changing the primitive
palette (`--syn-accent`, `--syn-frame`, `--syn-surface`, etc.). Override a
semantic role only when the change is intentional and contrast has been checked.

Native `disabled`, `aria-invalid`, `aria-pressed`, `aria-busy`,
`:focus-visible`, and `:active` styles are presentation only. `aria-busy`
does not stop clicks or run a task. Use actual `disabled` for disabled form
controls; `aria-disabled` requires the application to suppress activation.
For errors, pair `aria-invalid="true"` with an associated error message
(`aria-describedby`); never rely on border color alone.

See [the live design-state example](../examples/design-states.html) for
semantic typography, nested themes, compact layout and form states.

## Component-local layouts without compilation (experimental alpha.5)

Modern CSS custom properties allow Syntyr to expose a small set of layout
adjustments without inventing more utility classes. The default styles remain
unchanged when you do not provide an override. Consumers need **no build step**,
Tailwind compiler or JavaScript: use a normal stylesheet and optional application
CSS, or put a local variable on a single component.

```html
<link rel="stylesheet" href="/css/syntyr.core.css">
<section class="syn-root" data-syn-theme="studio">
  <div class="syn-grid" style="--syn-grid-min: 14rem; --syn-grid-gap: 1.25rem">
    <article class="syn-panel">Summary</article>
    <article class="syn-panel">Campaigns</article>
    <article class="syn-panel">Revenue</article>
  </div>
</section>
```

Core layout hooks (each can also be set in application CSS):

| Component | Local token | Default |
| --- | --- | --- |
| `.syn-grid` | `--syn-grid-min` / `--syn-grid-gap` | `17rem` / `1rem` |
| `.syn-layout` | `--syn-layout-min` / `--syn-layout-gap` | `21rem` / `1.25rem` |
| `.syn-stack` | `--syn-stack-gap` | `--syn-space-3` |
| `.syn-inline` | `--syn-inline-gap` | `--syn-space-2` |

Optional `syntyr.recipes.css` adds `.syn-kpi-grid`
(`--syn-kpi-min`, `--syn-kpi-gap`), `.syn-filter-bar`
(`--syn-filter-gap`), `.syn-filter-field`
(`--syn-filter-field-min`, `--syn-filter-query-min` on query variants),
and the `.syn-detail-layout` shell (`--syn-detail-gap`,
`--syn-detail-main-basis`, `--syn-detail-main-min`,
`--syn-detail-aside-basis`, `--syn-detail-aside-min`).

```html
<form class="syn-filter-bar" action="/campaigns" method="get"
      style="--syn-filter-gap: 1rem; --syn-filter-field-min: 9rem">
  <label class="syn-filter-field">
    Status
    <select class="syn-select" name="status">
      <option value="">All statuses</option>
      <option>Active</option>
    </select>
  </label>
  <button class="syn-button" type="submit">Filter</button>
</form>
```

Intrinsic grids and wrapping filter/detail layouts respond to their available
width, including inside narrow application panels. An explicit named
`.syn-region` container remains the contract for components using
`@container syn-region`. Do not set implausible minimum widths or nonlength
values: a CSS variable with an invalid value can invalidate its entire
declaration despite the `var()` fallback.

## Native state styling and accessibility

The classed `.syn-field` adds a focus-within label cue. Its label switches to
the danger color when it contains an `aria-invalid="true"` control or a
user-invalid native control. `.syn-input-group` highlights its addon border
when a child receives focus. Core `.syn-panel[inert]` uses a dashed border and
recessed surface to indicate unavailability, while the browser supplies inert
interaction semantics. Use `inert` on the actual unavailable subtree, not as
a substitute for server authorization; when not native or when unsupported,
styling alone cannot disable behavior.

Always preserve real labels, associated error text and focus outlines. For
invalid fields, provide an error message and connect it with
`aria-describedby`. The styling does not perform validation, keyboard
management, popover activation or announcements, and accessibility requires
manual keyboard, zoom, forced-colors and assistive-technology testing.

## Experimental opt-in OKLCH mixing

Syntyr's seven palette primitives and text/foreground contrast pairs remain
unchanged. To compare perceptual color mixing on an individual theme region,
opt in to `data-syn-color-space="oklch"`:

```html
<section class="syn-root" data-syn-theme="studio"
         data-syn-color-space="oklch">
  <button class="syn-button">Perceptual surface hover</button>
  <aside data-syn-theme="grid" data-syn-color-space="oklch">
    Nested themes must opt in independently.
  </aside>
</section>
```

Only the **`--syn-surface-hover`** role uses OKLCH mixing in this experiment.
The default stays in sRGB. Browser engines lacking the required
`color-mix(in oklch, ...)` support retain the existing sRGB role. **Nested themes**
recompute their own tokens; add the opt-in attribute to each theme scope
you intentionally want to compare. Do not generalize this experiment to text
colors or primary buttons without a contrast audit, and check the resulting
hover backgrounds against text across all palettes and browser engines.
