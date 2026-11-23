# Syntyr CSS component and token contract

Status: **experimental v0.3-alpha**, not yet released to a package registry. All CSS and markup are original to this repository; no upstream source code was copied.

Native elements such as `search`, `figure`, `figcaption`, `kbd`, `mark`, `output`, `meter`, and `pre` are styled only in the optional semantic mode. Native classless forms receive vertical spacing, fieldsets group controls, tables can use real `caption` elements, and disclosure summaries retain browser markers and comfortable pointer targets. See [the no-JS native example](../examples/native-elements.html). New [semantic HTML composition recipes](semantic-components.md) show article metadata, native citations, change history, ruby annotations, and table footers, with a [live gallery](../examples/semantic-compositions.html). The regular component-class API and HTML outside `.syn-root` are unchanged.

## Loading and scoping

For the explicitly classed API (no automatic unclassed element styles):

```html
<link rel="stylesheet" href="syntyr.core.css">
<body class="syn-root syn-page" data-syn-theme="grid">
  <button class="syn-button syn-button--primary">Run</button>
</body>
```

For Pico-like semantic markup, add the optional file **after** core and mark the subtree. Unclassed elements style automatically; opt in class-changing elements with `data-syn-semantic`:

```html
<link rel="stylesheet" href="syntyr.core.css">
<link rel="stylesheet" href="syntyr.semantic.css">
<section class="syn-root syn-semantic" data-syn-theme="studio">
  <article>
    <label for="id">Operator <input id="id" name="id" required></label>
    <button data-syn-semantic>Continue</button>
  </article>
</section>
```

Use `article` only for genuinely self-contained content; to draw a visual
card around a generic region use `.syn-panel` on the appropriate native
element. Use `fieldset` + `legend` to name control groups. In semantic mode
the default form layout applies to *unclassed* `form` (or explicit
`data-syn-semantic`), while `.syn-form` and application-owned classes retain
their separate styling contract. Use `label` rather than placeholders to name
inputs, and always give buttons a deliberate `type`.

Class-based components, recipes, effects, and geometry apply only to elements
inside a Syntyr root, including classes attached directly to the root itself.
A bare Syntyr class on an unrelated host element is deliberately ignored, so
framework-owned components and existing application CSS are not restyled.
The root boundary is enforced through modern native CSS nesting with
a zero-specificity selector rather than a global reset. Checkboxes and
radio controls using the explicit styling API retain a minimum 24 CSS px box;
the surrounding label should provide additional activation area.

For optional effects, load `syntyr.effects.css`. `syntyr.css` is the convenient core + effects entry point. `syntyr.all.css` combines everything (semantic styling still requires `.syn-semantic`). `syn-root` should wrap any themed subtree; nested `data-syn-theme` overrides color tokens. The separate `data-syn-intensity="quiet|standard|cinematic"` attribute controls decorative strength on a root or nested region. Load `syntyr.geometry.css` for a `.syn-frame` with one shape and optional `.syn-frame--accent`. See the [visual-intensity guide](visual-intensity.md).

## Components

| Area | CSS API | Semantic alternative |
| --- | --- | --- |
| Buttons | `.syn-button`, `.syn-button--primary`, `.syn-button--outline`, `.syn-button--danger`, `.syn-button--small`, `.syn-button--ghost` | unclassed `button` |
| Panels | `.syn-panel`, `.syn-panel--cut` | unclassed `article` |
| Layout | `.syn-page` (viewport-height opt-in), `.syn-shell`, `.syn-header`, `.syn-grid`, `.syn-layout`, `.syn-inline`, `.syn-sidecar`, `.syn-stack` | normal CSS layout |
| Typography | `.syn-logo`, `.syn-eyebrow`, `.syn-title`, `.syn-section-heading`, `.syn-heading`, `.syn-lede`, `.syn-mono`, `.syn-caption`, `.syn-muted` | native heading/text |
| Content lists | `.syn-list`, optional `.syn-list--compact` and `.syn-list--accent` | unclassed `ul` / `ol` in semantic mode |
| Status | `.syn-badge`, `.syn-badge--accent`, `.syn-status` and semantic variants, `.syn-alert`, `.syn-alert--danger`, `.syn-meter` on `progress` | native `progress` |
| Forms | `.syn-form`, `.syn-label`, `.syn-input`, `.syn-select`, `.syn-textarea`, `.syn-check`, `.syn-fieldset`, `.syn-help`, `.syn-error` | unclassed form controls |
| Email UI (optional) | `.syn-email-signup`, `.syn-email-inbox`, `.syn-email-message`, `.syn-email-compose`, `.syn-email-preferences` | Native forms and mailbox navigation; see [email components](email-components.md) |
| Form compositions | `.syn-field`, `.syn-field-row`, `.syn-field-body`, `.syn-input-group`, `.syn-input-addon` | native `form`, `label`, `input`, `button` |
| Overlays | `.syn-popover` on `[popover]`, `.syn-dialog` on `dialog`, `.syn-details` on `details` | browser defaults |
| Dropdowns | `.syn-dropdown` on `.syn-popover`, `.syn-dropdown__item`, `.syn-dropdown__group-label`, `.syn-dropdown__separator`, `.syn-dropdown__shortcut`, optional `.syn-select--enhanced` | Native select / disclosure / popover |
| Data | `.syn-table-wrap`, `.syn-table`, `.syn-cell--wrap`, `.syn-cell--nowrap`, `.syn-cell--numeric` | unclassed `table` |
| Navigation | `.syn-breadcrumbs`, `.syn-pagination`, `.syn-page-link` | native `<nav>`, `<ol>`, links and `aria-current` |
| Workflow (unreleased) | `.syn-steps`, `.syn-step`, `.syn-steps--vertical` | ordered `<ol>` and `aria-current="step"` |
| Loading | `.syn-skeleton`, `.syn-skeleton--short` | decorative placeholders; announce status separately |
| Effects (optional) | `.syn-grid-effect`, `.syn-glow`, `.syn-scanlines` | none |

For layout composition, the shell defaults to a maximum width of 72rem and a total inline inset of 2rem (normally 1rem per side). Set `--syn-shell-max` and `--syn-shell-inline-inset` on the shell to customize these dimensions. The header supports `--syn-header-gap` and `--syn-header-padding-block`; navigation supports `--syn-nav-gap`. All controls are optional and preserve existing defaults.


For wrapping action/filter clusters, use existing `.syn-inline` with optional
`--syn-inline-align`, `--syn-inline-justify` and `--syn-inline-gap`.
For a main region followed by an aside, `.syn-sidecar` wraps intrinsically
with `--syn-sidecar-main-min`, `--syn-sidecar-aside-width`,
`--syn-sidecar-gap` and `--syn-sidecar-align`. See the
[intrinsic composition guide](composition-adoption.md).

### Optional composition utilities and component overrides

Load `syntyr.utilities.css` in addition to core to use finite helpers:
`syn-u-w-full`, `syn-u-max-reading`, `syn-u-overflow-auto`,
`syn-u-text-center`, `syn-u-min-w-0` and `syn-u-wrap`. These classes
work only inside `.syn-root` and do not require a class generator.
The existing flex/grid/spacing helpers are unchanged. Load the optional
module only when it is needed.

Customize individual components with custom properties rather than a new
set of modifiers:

```html
<article class="syn-panel"
         style="--syn-panel-padding:1.5rem; --syn-panel-radius:.75rem;
                --syn-panel-border-width:2px">
  <button class="syn-button"
          style="--syn-button-padding-inline:1.25rem;
                 --syn-button-border-width:2px">Open</button>
</article>
```

Defaults preserve the previous appearance: fluid panel padding, square
panel corners, and 1px borders; button inline padding defaults to 1rem.
When `.syn-panel--cut` sits on a tinted or nested surface, set
`--syn-panel-cut-fill` to the **background behind the panel** so its cut
corner does not show the page-level `--syn-bg` by mistake. The default
remains `var(--syn-bg)` for existing flat page layouts.
These values are local CSS custom properties, not compile-time settings.
Inspect `metadata/syntyr-api.json` for the machine-readable API index,
or use the [editor integration instructions](editor-integration.md).

Optional native browser integrations: `.syn-popover--anchored` for invoker-relative popovers, `.syn-textarea--autosize` for `field-sizing: content`, and (with the optional `syntyr.motion.css` stylesheet) `.syn-popover--transition` and `.syn-reading-progress`. See the [browser API guide](native-browser-apis.md) for compatibility and fallbacks.

See [dropdown and native select patterns](dropdowns.md) for scriptless action panels, customizable selects, and the separately opt-in ARIA menu adapter.

Use native button `popovertarget="id"` to control a popover and `commandfor="id" command="show-modal"` to open a dialog in supporting browsers. This last native dialog invoker API has newer browser support; provide alternate ways to reach important content where needed. Do not build custom ARIA dialog/tab/combobox patterns unless they are tested and necessary.

For component-level package imports and optional native UI recipes, see
[native patterns](native-patterns.md).

### Content lists and grouped rows (alpha.5 source candidate)

Use an ordinary `<ul>` or `<ol>` inside `.syn-semantic` for native list
spacing, nesting and markers. When loading **core only**, opt into the same
scoped list presentation with `.syn-list`. It preserves native bullet shapes,
ordered numbering (`start`, `reversed`, `value`), writing direction and
screen-reader list semantics. `.syn-list--compact` reduces vertical item gaps
and `.syn-list--accent` colors the top-level markers; both are optional.
Set `--syn-list-item-gap` locally to override the item rhythm.

```html
<ul class="syn-list syn-list--accent">
  <li>Accessible headings</li>
  <li>Native nested lists
    <ul><li>First detail</li><li>Second detail</li></ul>
  </li>
</ul>
<ol class="syn-list syn-list--compact" start="9">
  <li>Review</li><li>Publish</li>
</ol>
```

`.syn-feature-list` is a legible, accent-marked list intended for pricing and
features; override its row gap with `--syn-feature-list-gap`. The distinct
`.syn-list-group` is for markerless grouped navigation or collection rows.
Customize row density by setting `--syn-list-row-padding` on a containing
`.syn-list-group` rather than creating a new component. When removing markers
with `list-style: none`, Safari/VoiceOver may not expose the list as a list;
add `role="list"` to the native `ul` or `ol` if list semantics are intended.
Do **not** apply a global marker reset or use fake list text in place of
semantic list markup.

## Standard low-entropy component inventory

**Standard does not mean a CSS class for every HTML element.** Use
`syntyr.core.css` for explicitly classed components and
`syntyr.semantic.css` with `.syn-semantic` for native, unclassed elements.
Both are standard supported surfaces in the alpha.5 source candidate;
the semantic file is intentionally optional to avoid restyling host apps.
The browser supplies state/validation/focus behavior. This is the baseline
inventory of everyday UI needs, not an assertion that CSS implements
application-specific interactions.

| Need | Standard native-first implementation | Delivery |
| --- | --- | --- |
| Text and search | Labeled `input` (`text`, `search`, `email`, `password`, `tel`, `url`, `number`), `textarea`, `datalist` | `.syn-input`, `.syn-textarea`, `.syn-field`; native `datalist` |
| Date and time | Native `date`, `time`, `datetime-local`, `month`, `week` inputs | `.syn-input`; system picker remains browser-owned |
| Choice controls | Native `select`/`optgroup`, multiple select, checkbox, radio; `fieldset` + `legend` | `.syn-select`, `.syn-check`, `.syn-fieldset`; no custom select implementation |
| Range | Native `input type="range"` | `.syn-input` with browser thumb and `accent-color` |
| File upload | Native `input type="file"` | `.syn-input` with native file-selector button |
| Color picker | Native `input type="color"` | `.syn-input` with browser color chooser |
| Buttons and actions | `button`, `a`, submit/reset, `aria-pressed` when application-managed | `.syn-button`, `.syn-button-group`, `.syn-chip` |
| Data and progress | `table` with headers/caption, `progress`, `meter`, `output`, `dl` | `.syn-table`, `.syn-meter` on `progress`; native `meter`/`output` in semantic mode |
| Disclosure and overlays | `details`/`summary`, `dialog`, `[popover]`, native invoker attributes | `.syn-details`, `.syn-dialog`, `.syn-popover` |
| Navigation | `nav`, anchor links, ordered breadcrumbs, pagination, page-link tabs | `.syn-breadcrumbs`, `.syn-pagination`, `.syn-nav-tabs`, `.syn-list-group` |
| Feedback and loading | Textual alerts/status, native `progress`, static skeleton, empty state | `.syn-alert`, `.syn-status`, `.syn-skeleton`, `.syn-empty` |
| Media and content | `figure`/`figcaption`, `picture`/`img`, `video`/`audio`, `pre`/`code`, `kbd`, lists, `hr` | Native semantic mode; `.syn-code`, `.syn-rule`, `.syn-divider-label` |
| Layout and composition | Semantic landmarks, `section`, `article`, grid, stack, inline, toolbar, panel | `.syn-grid`, `.syn-stack`, `.syn-inline`, `.syn-toolbar`, `.syn-panel`, `.syn-sidecar` |

**Application-owned behavior:** A searchable combobox, ARIA tabpanel widget,
roving-focus menu, sortable/virtualized data grid, notifications queue and
drag-and-drop are **not** CSS components. Start with native `select`, links,
`details`, `dialog`, `popover` or a normal table; when the product really
needs behavior, use a small headless library or application code with keyboard,
focus, announcements and tests. Do not introduce a Syntyr JS runtime.
For native input examples, see [the component catalog](catalog.html). For exclusive accordions, search landmarks, confirmation dialogs,
datalist suggestions, and meter/output examples, use the
[native interaction recipes](native-patterns.html) and the
[script-free demo](https://syntyr-css.pages.dev/examples/native-interactions.html).

## Native choices, filters and rich list rows (alpha.5 source candidate)

These recipes adapt useful shadcn/ui and daisyUI ideas to **native HTML**, without
copying upstream implementations or requiring a JS widget runtime. They are
opt-in, scoped under `.syn-root`, and use the existing theme tokens. See the
[standalone demonstration](../examples/native-choice-filter-list.html).

### Choice cards

Use `<fieldset>` and `<legend>` to give radio/checkbox groups a name.
`.syn-choice-card` is a real `<label>`, not an ARIA radio substitute.
Compose a responsive layout with existing `.syn-grid`:

```html
<fieldset class="syn-fieldset">
  <legend>Choose a plan</legend>
  <div class="syn-grid">
    <label class="syn-choice-card">
      <input class="syn-input" type="radio" name="plan" value="starter" checked>
      <span><strong>Starter</strong><small>For a small team</small></span>
    </label>
    <label class="syn-choice-card">
      <input class="syn-input" type="radio" name="plan" value="growth">
      <span><strong>Growth</strong><small>For a growing team</small></span>
    </label>
  </div>
</fieldset>
```

Browser-owned `:checked`, `:focus-visible` and `:disabled` drive appearance.
Keep the actual radio visible and focusable. No manually synchronized
`aria-checked` or custom keyboard controller is needed.

### Validation (browser and server)

Native `:user-invalid` and explicit `aria-invalid="true"` already style
Syntyr inputs and their field label. A server can additionally render
`data-syn-state="error"` on `.syn-field` to style the field consistently
before user interaction, without changing browser validity or hiding the error:

```html
<div class="syn-field" data-syn-state="error">
  <label class="syn-label" for="email">Email</label>
  <input class="syn-input" id="email" name="email" type="email" required
         aria-invalid="true" aria-describedby="email-help email-error">
  <p class="syn-help" id="email-help">Use a work email.</p>
  <p class="syn-error" id="email-error">Enter a valid email address.</p>
</div>
```

The host must validate on the server, supply real error text, update
`aria-invalid`, and announce/focus a submission error summary when appropriate.
CSS does not create errors, switch ARIA states, or focus controls. Do not hide
all error text using CSS alone; accessible error content belongs to the host.
This pattern works without JavaScript.

### Native filter choices

Use `.syn-filter-choices` to display a group of `.syn-chip` labels backed by
real named radio/checkbox inputs. A wrapping filter group should be inside a
named fieldset in a normal GET form:

```html
<form action="/campaigns" method="get">
  <fieldset class="syn-fieldset">
    <legend>Campaign status</legend>
    <div class="syn-filter-choices">
      <label class="syn-chip"><input type="radio" name="status" value="all" checked> All</label>
      <label class="syn-chip"><input type="radio" name="status" value="active"> Active</label>
    </div>
  </fieldset>
  <button class="syn-button" type="submit">Apply filter</button>
</form>
```

The radio remains keyboard focusable and contributes to native form submission;
the filter choice composition visually conceals only its small input and
exposes `focus-visible` on the full chip. The server processes the query string.
HTMX or Datastar may optionally enhance submission, but should preserve the
HTML action/method fallback. Do not use these controls as faux ARIA tabs.

### Rich collection rows

Keep `.syn-list-group` and `.syn-list-row`. Optionally compose
`.syn-list-row__media`, `.syn-list-row__body` and `.syn-list-row__actions`
for an avatar, multiline description and an action cluster.
When a row contains multiple actions, use a **noninteractive** `<li>` wrapper
with independent links/buttons. Never nest interactive controls inside a row
that is itself an `<a>` or `<button>`. Actions wrap on narrow containers and
RTL follows logical margin properties.

All four patterns inherit theme and density tokens. Validate keyboard focus,
forced colors, mobile overflow, and actual server form behavior in consumers.


## Neutral-first visual styling

The implicit `.syn-root` palette is Studio (light and sans-serif). Explicit `data-syn-theme="grid"` and `data-syn-theme="terminal"` retain technical monospace presentation; other themes remain opt-in. `.syn-panel` and `.syn-stage` are flat by default; add `syn-surface--accent` from the optional recipes CSS for emphasis, or the effects stylesheet for cinematic treatments. `.syn-badge` is a neutral label; use `.syn-status` with readable status text for meaningful state, or `.syn-badge--accent` to emphasize a badge.

Use `.syn-section-heading` between `.syn-heading` and `.syn-display`. Table content wraps by default for better readability in narrow regions, including long text. Apply `.syn-cell--nowrap` to identifiers or short labels that must stay on one line; `.syn-cell--numeric` also preserves no-wrap numeric alignment. `.syn-cell--wrap` remains available to limit a descriptive cell to 38ch. Keep genuinely wide tables inside `.syn-table-wrap` with an accessible caption; for keyboard scrolling where needed, make the wrapper focusable with `tabindex="0"`, an accessible label and a visible focus ring. Selected rows have a logical inline-start accent border in addition to their fill.

For large server-rendered tables, see the [enterprise tables guide](data-tables.html) and [static example](../examples/data-tables.html). Sorting and filtering remain application responsibilities.

## Native HTML elements (optional semantic mode)

Syntyr styles common HTML primitives within `.syn-root.syn-semantic` or a `.syn-semantic` subtree of `.syn-root`. Load `syntyr.semantic.css` **after** `syntyr.core.css`. Without the semantic stylesheet and scope, ordinary HTML remains untouched.

| Native elements | Included presentation |
| --- | --- |
| `ul`, `ol`, `menu`, `li`, `dl`, `dt`, `dd` | List spacing, preserved native markers, definition terms |
| `h5`, `h6`, `small`, `abbr[title]`, `address` | Heading depth, readable captions, abbreviations, contact text |
| `pre`, `code`, `kbd`, `samp`, `mark` | Scrollable code, keyboard hints, sample output, contrast-safe highlights |
| `figure`, `figcaption`, `img`, `video`, `audio` | Captions and width-constrained media; intrinsic image/video proportions |
| `table`, `caption`, `progress`, `meter`, `output` | Data captions and native browser indicators |
| `input[type=file]`, `input[type=color]` | Native chooser controls with theme-aware surfaces |
| `details`, `summary`, `dialog`, `[popover]` | Browser-owned disclosure, top-layer behavior and dismissal |

The selectors style **unclassed elements only**, or elements explicitly marked `data-syn-semantic`. A classed element is left to its own application styles by default; no global element reset is added. Syntyr does not emulate native dialog or popover activation, file inputs, meters or input validation.

For a copyable page covering the additions, see [native HTML element examples](../examples/native-elements.html). That example also shows labeled `datalist` suggestions, grouped `select`/`optgroup` options, and named `details` disclosures. Native suggestions do not validate accepted values; host applications validate them on the server. Named disclosures are exclusive-open in supporting browsers, with a usable ordinary-details fallback elsewhere. Semantic file/color inputs and fieldsets shrink at enlarged text sizes, while wide tables remain in labeled, keyboard-scrollable regions. The `commandfor` / `command="show-modal"` dialog button is progressively enhanced, not a guarantee for browsers that lack HTML invoker commands.

```html
<link rel="stylesheet" href="syntyr.core.css">
<link rel="stylesheet" href="syntyr.semantic.css">
<main class="syn-root syn-semantic">
  <dl><dt>Availability</dt><dd>12 active screens</dd></dl>
  <figure><img src="/assets/preview.svg" alt="Campaign preview">
    <figcaption>Proof-of-posting image</figcaption>
  </figure>
  <label for="fill">Capacity</label>
  <progress id="fill" value="12" max="20">12 of 20</progress>
</main>
```

## Additional common UI elements and semantic HTML

The optional `syntyr.semantic.css` now covers the presentation-relevant
`hgroup`, `time`, `data`, `cite`, `dfn`, `var`, `q`, `ins`, `del`,
`picture`, `iframe`, `canvas`, and `svg` elements, plus native
`select[multiple]` and `textarea` without a `rows` attribute.
These styles apply only to unclassed elements inside `.syn-semantic` or to
elements with `data-syn-semantic`. Existing semantics, quotes, change
markings, media aspect ratios, and browser controls remain intact.

Elements like `bdi`, `bdo`, `ruby`, `rt`, `rp`, `wbr`, `template`,
`slot`, `option`, and `datalist` deliberately use native browser behavior.
Structural landmarks, `script`, and metadata do not need cosmetic component
APIs. **Not every HTML element benefits from a CSS reset.**

The core CSS adds these intentionally small presentation compositions:

| CSS API | Use case | Behavior |
| --- | --- | --- |
| `.syn-avatar`, `--sm`, `--lg`, `.syn-avatar-stack` | User or organization identities | Image or initials; decorative stack labels need a separate accessible group label |
| `.syn-chip` | Filter/category labels | Static or native anchor/button; `data-syn-state="active"` only changes visuals |
| `.syn-nav-tabs` | Section navigation | Ordinary links with `aria-current="page"`; **not** JavaScript tabs or tabpanels |
| `.syn-list-group`, `.syn-list-row` | Settings, destinations, item lists | Native list semantics; rows may contain anchors; `aria-current="page"` for current destination |
| `.syn-button-group` | Adjacent actions | Flexbox composition of real links/buttons; no artificial event handling |
| `.syn-divider-label` | Labeled separator | Decorative rules before/after actual text |
| `.syn-alert--success`, `.syn-alert--warning` | Notices | Extend existing `.syn-alert`; always include readable status/warning text |

Try the [CSS-only common UI example](../examples/common-ui.html) and the
[existing native elements example](../examples/native-elements.html).

```html
<nav class="syn-nav-tabs" aria-label="Account sections">
  <ul>
    <li><a href="/settings" aria-current="page">Settings</a></li>
    <li><a href="/billing">Billing</a></li>
  </ul>
</nav>
<ul class="syn-list-group" aria-label="Team members">
  <li><span class="syn-list-row"><span class="syn-avatar" aria-hidden="true">JD</span>Jane Doe</span></li>
</ul>
<p class="syn-alert syn-alert--warning">Review changes before publishing.</p>
```

Choose `aria-current="page"` only for real navigation state; do not use
`role="tab"` without implementing the WAI-ARIA keyboard and panel behavior.
Use `role="status"` or `role="alert"` only for genuinely dynamic
announcements, not because a box has a particular color. More complex
interactions (autocomplete, rich text editor, sortable tables, custom menus,
toast lifecycles) belong to the host app, not a CSS runtime.

## Theme tokens

| Token | Purpose |
| --- | --- |
| `--syn-bg`, `--syn-surface`, `--syn-surface-hi` | Background surfaces |
| `--syn-text`, `--syn-muted` | Foreground text |
| `--syn-accent`, `--syn-on-accent`, `--syn-accent-soft` | Accent and contrast |
| `--syn-frame`, `--syn-danger` | Borders and warning states |
| `--syn-font`, `--syn-mono` | System typography |
| `--syn-space-1` ... `--syn-space-5` | Stable fixed spacing scale |
| `--syn-space-fluid-1` ... `--syn-space-fluid-4` | Optional fluid gaps and padding, bounded by adjacent fixed tokens (unreleased alpha.5) |
| `--syn-cut`, `--syn-radius`, `--syn-line`, `--syn-control-height` | Shape and layout |

Application CSS can override tokens:

```css
/* Unlayered CSS overrides the library's layered defaults. */
.my-surface { --syn-accent: #a9f890; }
```

## Optional charts and microvisualizations

Load `syntyr.viz.css` after core for seven-theme chart colors, figure/legend
styling, inline SVG sparklines, bar lists, status trackers and heatmap cells.
Syntyr only styles supplied HTML/SVG; it does not create chart geometry,
fetch data or require a renderer. Read [Syntyr Viz](viz.md) and open the
[static seven-theme gallery](../examples/viz.html).

## Accessibility and performance contracts

- Actual semantic HTML and associated labels; use `button` for actions and `a` for navigation.
- Visible `:focus-visible` outline; do not remove it with theme overrides.
- Contrast target: WCAG 2.2 AA for text; manually verify any customized tokens.
- Honor user preferences: `prefers-reduced-motion`, `forced-colors`; effects opt-in and static.
- Avoid relying on color alone for state; use labels or icons with text alternatives.
- Raw/gzip bundle sizes are reported by `python3 scripts/asset_report.py`, with no hard size ceilings; runtime JS: 0 bytes.
- Browser coverage: current Chromium, Firefox and WebKit. The included automated browser suite runs Chromium when installed and can be extended to other engines.
- Do not automatically treat the demo or contract tests as an accessibility certification: test screen readers, 200%/400% zoom, form errors, contrast, and actual products separately.

## Distribution behavior

The repository now includes an **optional CSS-only `package.json` for package-manager distribution**; there is still no Node runtime requirement, bundling dependency, or mandatory package manager. A standard Python 3 build script creates deterministic concatenated CSS and validates exact committed outputs (see [optional package-manager guide](package-managers.md)):

```sh
python3 scripts/build.py
python3 scripts/build.py --check
python3 -m unittest discover -s tests -v
```

## Licensing and provenance

MIT; this version is original work, not a fork or copy of Pico CSS, Chota or Open Props. If future work ports code from an upstream library, preserve that project's copyright and MIT notices and document the relevant files in `THIRD_PARTY_NOTICES.md`.


## Embedded versus full-page usage

`syn-root` provides a bounded styling context. Add `syn-page` **only for full-page experiences**. This separation prevents an embedded themed widget from unexpectedly forcing a viewport-height section.

```html
<section class="syn-root" data-syn-theme="noir">
  <div class="syn-panel">This can be embedded inside an existing application.</div>
</section>
```

For invalid form controls, associate error text through native labeling and `aria-describedby`, and set `aria-invalid="true"` for server-provided errors. `syn-error` changes text color; do not rely on color alone to communicate invalid state.

```html
<label class="syn-label" for="email">Email</label>
<input class="syn-input" id="email" type="email" aria-invalid="true" aria-describedby="email-error">
<p class="syn-error" id="email-error">Enter a valid email address.</p>
```

## v0.3 compositional patterns (no build step)

The following are ordinary CSS classes in `syntyr.core.css`:

| Class | Purpose |
| --- | --- |
| `.syn-region` | Named `syn-region` inline-size container for independent widget responsiveness |
| `.syn-split` | Stacked by default; two columns at container width >=43rem |
| `.syn-stats` | One/two/three columns at container widths <31rem, >=31rem, >=55rem |
| `.syn-stat`, `.syn-stat-label`, `.syn-stat-value` | Semantic telemetry card presentation |
| `.syn-empty` | Centered dashed-outline empty-state composition |
| `.syn-pricing`, `.syn-price-card` | One column until 43rem, then three equal columns |
| `.syn-price-card[data-syn-featured]` | Opt-in highlighted plan, purely visual, no ARIA claim |
| `.syn-price-value`, `.syn-feature-list` | Pricing typography and list styles |
| `.syn-toolbar` | Wrapping flex toolbar |

Attach `.syn-region` **on an ancestor** of the patterns. A region element isn't its own query container descendant; without a region ancestor the patterns remain readable one-column layouts. Nest separate regions for independently sized widgets. The `syn-region` name prevents unrelated page containers from changing their layouts.

Button state: `.syn-button[aria-pressed="true"]` is a pressed **toggle button**; `[data-syn-state="active"]` is decoration/host state; `[aria-busy="true"]` expresses in-progress updates but does not actually disable interactions. State changes and form handling are application responsibilities.

Additional inherited tokens: `--syn-ease`, `--syn-duration-fast`, `--syn-success`, `--syn-warning`. Extend themes with unlayered `.syn-root[data-syn-theme="custom"] { --syn-accent: ... }` CSS. Test contrast for your own values.

See [theme customization and token overrides](theme-customization.md), [MIT composition recipes](recipes.md) and [Tailwind architectural research](tailwind-research.md).

## Optional SaaS, business and CLI compositions (development branch)

Load `syntyr.core.css` first and `syntyr.recipes.css` second. The core remains separate from optional recipes; measure each bundle instead of enforcing a fixed byte cap.

| Context | Optional classes |
| --- | --- |
| SaaS | `.syn-app-shell`, `.syn-app-rail`, `.syn-app-nav`, `.syn-workspace`, `.syn-app-topbar`, `.syn-kpi-grid`, `.syn-app-card`, `.syn-activity-list` |
| CRM / vertical SaaS | `.syn-filter-bar`, `.syn-filter-field`, `.syn-filter-actions`, `.syn-pipeline`, `.syn-pipeline-lane`, `.syn-pipeline-list`, `.syn-pipeline-card`, `.syn-record-fields` |
| Business website | `.syn-site-hero`, `.syn-site-heading`, `.syn-feature-grid`, `.syn-feature-card`, `.syn-cta-band` |
| Browser terminal | `.syn-terminal`, `.syn-terminal-bar`, `.syn-terminal-body`, `.syn-terminal-line`, `.syn-terminal-prompt` |
| Surface design | `.syn-frame--precision`, `.syn-frame--industrial`, `.syn-frame--soft` |

Native disabled buttons cannot activate; aria-disabled does not block activation by itself. Host application code must suppress actions when ARIA-disabled and should preserve focus when appropriate. Syntyr does not disable click handlers via CSS.

Professional light mode: `data-syn-theme="studio"`. Colors and geometry are intentionally independent. Use `.syn-table-emphasis` for explicit cell highlighting instead of relying on last-column position; `.syn-status--success`, `--warning`, or `--danger` should always accompany readable status text.

Native terminal applications cannot render CSS. Use `terminal/palettes.json` as the portable color reference. See [usage and accessibility guidance](saas-cli-business.md). For bevel, notch, bracket, inset and circuit frame geometry, load the optional geometry stylesheet and follow [the frame guide](geometry-terminal.md). All new visual classes are optional and require no runtime JavaScript.


## Minimalist compositions (experimental)

`syntyr.recipes.css` also includes `.syn-sidebar` (two-column intrinsic
sidebar/content), `.syn-switcher` (all-or-nothing responsive card row),
fluid typography utilities `.syn-fluid-display` / `.syn-fluid-lede`,
and `.syn-reading`. These are not part of `syntyr.core.css`.
Classless checkbox and radio labels align their controls inline when
`syntyr.semantic.css` and `.syn-semantic` are enabled. See
[the recipe guide](recipes.md) and [live example](../examples/minimalist-patterns.html).

## Visual role examples

The optional [design-state example](../examples/design-states.html) exercises active, selected, disabled, and invalid presentation across nested light/dark themes. It contains no application state machine, backend operation, or runtime JavaScript.

## Progressive rendering extensions

System-aware `data-syn-theme="auto"` is built into core CSS. Use optional
`syntyr.print.css` for printable reports and the
[progressive-enhancement guide](progressive-enhancement.md) for fallbacks.

### Workflow steps (source candidate only)

Use the core CSS module with native ordered-list semantics. Wrap the list in a
`.syn-region` **ancestor** for a horizontal layout at wide *container* widths;
the narrow presentation is vertical. Use `.syn-steps--vertical` to keep a
vertical layout at every width.

```html
<section class="syn-root syn-region" data-syn-theme="studio">
  <h2>Workspace setup</h2>
  <ol class="syn-steps" role="list" aria-label="Workspace setup progress">
    <li class="syn-step" data-syn-state="complete">
      <span class="syn-step-label">Account created (complete)</span>
    </li>
    <li class="syn-step" aria-current="step">
      <span class="syn-step-label">Configure workspace (current step)</span>
    </li>
    <li class="syn-step"><span class="syn-step-label">Invite team (not started)</span></li>
  </ol>
</section>
```

Use `aria-current="step"` on exactly the current step. The application must
supply completed/error state text; `data-syn-state="complete|error"` is only a
presentation hook, not an ARIA state. Numbered circles and connectors are
decorative; the real ordered list and labels convey order and meaning. Preserve
`role="list"` for list semantics in Safari when CSS removes list markers.
Never use colors alone to communicate completion or failure. CSS cannot
implement step navigation, eligibility checks or server-side transitions.
Long step descriptions and translated text keep numbered markers aligned at the
block start so vertical connectors do not cross the marker or its numeral.

See [the zero-JavaScript example](../examples/workflow-steps.html) and the
[composed operations workflow gallery](../examples/workflow-operations.html), which
reuses these steps with existing activity timelines and approval surfaces.
These classes are not included in the published immutable alpha.4 release.
