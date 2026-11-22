# MIT-licensed composition recipes

For copyable input groups, labeled fields, container-responsive settings forms and optional headless UI styling, see [form composition recipes](component-recipes.md) and the [Radix adapter](radix-integration.md). For layered depth, incident-detail layouts, command presentation, timelines, and editorial product sections, see [premium compositions](premium-compositions.md).

For native file uploads, multi-action forms, and nested resource navigation, see [native business workflows](native-workflows.md) and the [script-free example](../examples/native-workflows.html). These compose the existing error-summary and detail-layout patterns without introducing a JavaScript dependency.

These original Syntyr recipes are free to copy, edit, commercialize, and distribute under MIT. No Tailwind Plus source or premium assets were copied. For live examples see [the gallery](index.html), the [Grid console](../examples/console.html), and the [Noir pricing layout](../examples/pricing.html).

## Optional vertical flow

Use `.syn-flow` from `syntyr.recipes.css` on a content group to add
consistent gaps between adjacent **direct children**. The flex-column
composition stacks both inline and block elements, without overriding a
child component's own display. It does not globally reset margins or modify
unwrapped host markup. When children already have vertical margins, adjust
them at the application level to avoid unexpectedly large combined spacing.
For prose with heading rhythm, prefer the existing `.syn-prose` class.

```html
<section class="syn-root" data-syn-theme="studio">
  <div class="syn-flow" style="--syn-flow-gap: 1.5rem">
    <h2 class="syn-section-heading">A native-first design system</h2>
    <p>Readable content with consistent configurable vertical rhythm.</p>
    <a href="/documentation">Read the documentation</a>
  </div>
</section>
```

`.syn-flow` is an opt-in composition, not part of the minimal core.
All spacing remains controlled by ordinary CSS custom properties.

## 1. Responsive telemetry cards

The `.syn-region` element establishes a **named inline-size container**. Unlike media queries, the cards respond to the width of the enclosing widget/sidebar. This is a native browser feature; no JavaScript observer is needed.

```html
<section class="syn-root syn-region" data-syn-theme="grid" aria-label="Network telemetry">
  <div class="syn-stats">
    <article class="syn-stat"><span class="syn-stat-label">UPTIME</span><p class="syn-stat-value">99.8%</p></article>
    <article class="syn-stat"><span class="syn-stat-label">NODES</span><p class="syn-stat-value">24</p></article>
    <article class="syn-stat"><span class="syn-stat-label">ALERTS</span><p class="syn-stat-value">02</p></article>
  </div>
</section>
```

## 2. Accessible empty state

```html
<section class="syn-empty" aria-labelledby="empty-heading">
  <p class="syn-eyebrow">QUEUE / EMPTY</p>
  <h2 id="empty-heading">No pending actions</h2>
  <p class="syn-muted">New items appear here once submitted.</p>
  <a class="syn-button syn-button--primary" href="/new">Create an item</a>
</section>
```

This is a *visual composition*, not a live queue implementation. Preserve real links, meaningful labels, and server-side behavior.

## 3. Three-card pricing display

```html
<section class="syn-root syn-region" data-syn-theme="noir" aria-label="Illustrative plans">
  <div class="syn-pricing">
    <article class="syn-price-card">
      <h2>Personal</h2>
      <p class="syn-price-value">$19<small> / month</small></p>
      <ul class="syn-feature-list"><li>One project</li><li>Basic support</li></ul>
      <a class="syn-button" href="/contact">Contact us</a>
    </article>
    <article class="syn-price-card" data-syn-featured>
      <h2>Studio</h2>
      <p class="syn-price-value">$49<small> / month</small></p>
      <ul class="syn-feature-list"><li>Unlimited projects</li><li>Team seats</li></ul>
      <a class="syn-button syn-button--primary" href="/contact">Contact us</a>
    </article>
    <article class="syn-price-card">
      <h2>Enterprise</h2>
      <p class="syn-price-value">Custom</p>
      <ul class="syn-feature-list"><li>Security review</li><li>Dedicated support</li></ul>
      <a class="syn-button" href="/contact">Contact us</a>
    </article>
  </div>
</section>
```

## 4. Stateful native button (host controlled)

```html
<button type="button" class="syn-button" aria-pressed="true">Grid view</button>
<button type="button" class="syn-button" aria-busy="true">Syncing status</button>
```

`aria-pressed="true"` conveys a real toggle state to accessibility APIs; set it only when a toggle actually is pressed. `aria-busy` signals that updates are in progress; it **does not** disable a button or create loading logic. The UI state must come from your application/server. If a state is only decorative, use `data-syn-state="active"` instead of misusing ARIA.

## Token-only custom theme

```css
/* Unlayered application CSS intentionally overrides Syntyr's layered tokens. */
.syn-root[data-syn-theme="custom"] {
  --syn-bg: #0b1019;
  --syn-surface: #192333;
  --syn-accent: #82f9d1;
  --syn-on-accent: #09120e;
  --syn-text: #eefbf7;
  --syn-muted: #bbd4ce;
  --syn-frame: #496b68;
}
```

For custom themes, test *every* textual token pairing and important state for WCAG contrast. The example overrides only a subset of the available color tokens and is not an accessibility certification.

## CRM and vertical SaaS patterns (alpha.5 source candidate)

Load `syntyr.core.css` and then optional `syntyr.recipes.css`. See the [complete CRM example](../examples/crm.html), which uses ordinary HTML and requires no JavaScript.

- **Filter bar:** `.syn-filter-bar` arranges labelled `.syn-filter-field` controls and a wrapping `.syn-filter-actions` group. Use `.syn-filter-field--query` for a wider search field. A `method="get"` form remains usable without JavaScript; the application must apply filters and preserve query values.
- **Pipeline:** `.syn-pipeline` contains named `section.syn-pipeline-lane` columns; each lane contains a semantic `ul.syn-pipeline-list` of `li.syn-pipeline-card`. Set `tabindex="0"` and an accessible name on the scrollable board so keyboard users can reach overflow. Links inside cards remain ordinary links. Drag-and-drop, permissions, saved filters, counts, and stage transitions must be implemented by the host application.
- **Record metadata:** `dl.syn-record-fields` groups each `dt` and `dd` in a direct child `div` for readable, responsive key/value pairs. Use a real `time` element for dates. **Subgrid** aligns labels and values across rows when supported. A named inline-size `container` on the `dl` stacks each pair below **24rem**, independently of viewport size; older browsers retain the original intrinsic two-column/wrapping **fallback**. No extra classes, media breakpoints, or JavaScript are required.
- **Density:** `data-syn-density="compact"` compresses control, row and card spacing without shrinking type. `data-syn-density="comfortable"` restores default metrics inside compact ancestors. `data-syn-density="spacious"` provides larger controls and rows for review-heavy screens. These attributes may be on `.syn-root` or nested elements. `comfortable` is the default when density is unspecified.

```html
<section class="syn-root" data-syn-theme="studio" data-syn-density="compact">
  <form class="syn-filter-bar" method="get" action="/opportunities">
    <label class="syn-label syn-filter-field syn-filter-field--query" for="crm-query">
      Search
      <input class="syn-input" id="crm-query" name="query" type="search">
    </label>
    <div class="syn-filter-actions">
      <button class="syn-button syn-button--primary" type="submit">Search</button>
    </div>
  </form>
  <div class="syn-pipeline" tabindex="0" aria-label="Opportunity stages">
    <section class="syn-pipeline-lane" aria-labelledby="crm-stage">
      <h2 id="crm-stage">Qualified</h2>
      <ul class="syn-pipeline-list">
        <li class="syn-pipeline-card"><a href="/opportunities/123">Example account</a></li>
      </ul>
    </section>
  </div>
  <section data-syn-density="spacious" aria-label="Opportunity details">
    <dl class="syn-record-fields">
      <div><dt>Owner</dt><dd>Account team</dd></div>
    </dl>
  </section>
</section>
```

The styles are layout primitives, not a grid widget or CRM engine. Keep keyboard focus visible, do not imply drag interactions, and render truthful stage counts. Preserve authorization and validate any user-controlled query parameters on the server.

## Resizable workspace (optional behavior)

The **Resizable workspace** composition is separate from the existing
`.syn-split` (which is simply a responsive two-column grid). Load
`syntyr.core.css` and `syntyr.recipes.css` for
`.syn-resizable-workspace`, `.syn-resizable-workspace__panes`,
`.syn-resizable-workspace__pane` and
`.syn-resizable-workspace__separator`. The `--syn-workspace-leading` CSS
property expresses the first pane's share. Without JavaScript the two panes
remain readable and the inert separator is hidden.

[Runnable example](../examples/resizable-workspace.html) includes a
**copy-owned, optional** module with pointer capture and keyboard support.
It enables the separator only after initialization and keeps
`aria-valuenow` synchronized with the visible split. Arrow Left/Right move
by 2 percentage points (Shift: 10), with Home/End for bounds (20–70).
The example respects RTL and stacks its panes when its **own container**
is narrow; the separator is hidden in the stacked layout. No storage,
network requests or global event listeners are required.

**Running the packaged interactive demo:** Extract the ZIP, change into its
top-level `syntyr-css-<version>` directory, and serve the local assets over
HTTP (not `file://`, which blocks relative module scripts in browsers):

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Open `http://127.0.0.1:8000/examples/resizable-workspace.html`.
A `file://` launch still shows the static two-pane fallback; drag and
keyboard resizing require the local module to load over HTTP. Stop the
server with Ctrl-C. No external network requests are needed.

The resize value and user preference are **application-owned**: persistence,
server rendering, saved layouts, authorization, and responsive restoration
belong to the consuming application. A live client must keep the
separator's ARIA bounds, visible panel sizes and keyboard/pointer behavior in
sync. The script is demonstrative, **not** part of the zero-JS CSS runtime.
Test real zoom, touch, forced colors, keyboard and screen-reader support
before production use.

## Operation feedback and record revisions (alpha.5 source candidate)

The optional `syntyr.recipes.css` provides **two presentation patterns**, not a
transaction state machine or history service. [View the static example](../examples/operation-revisions.html).

- **Operation feedback:** use `.syn-operation-feedback` and an actual
  `data-syn-state="unsaved|pending|saved|failed|conflict"`. All five states use
  explicit textual headings and supporting details, not color alone.
  `--syn-operation-edge` can be overridden per instance if the host's palette
  needs a different border; do not interpret these colors as business results.
- **Record revisions:** keep the existing `dl.syn-record-fields` and place
  `.syn-change-pair` inside a `dd`. Its optional `.syn-change-before` and
  `.syn-change-after` children wrap at narrow widths, including when embedded
  in a sidebar. Use visible "Previous", "Updated", "Added" or "Removed" labels
  with native `del`/`ins` elements. Omit the absent side for additions/removals;
  don't manufacture a previous value. The same pair may appear in a table cell
  or review panel; no duplicate definition-list component is needed.

At extreme user text sizes, the `syn-page-header` and `syn-app-card`
compositions allow long words and dates to wrap instead of expanding the viewport.
The optional developer-only browser smoke test (tests/operation_revisions_browser.js)
covers reflow, keyboard focus and forced colors in Playwright. Enlarging root
text is a stress test, **not** proof of native 400% browser zoom or a manual
screen-reader audit.

```html
<section class="syn-root" data-syn-theme="studio">
  <section class="syn-operation-feedback" data-syn-state="conflict"
       aria-labelledby="revision-conflict">
    <h2 id="revision-conflict">Someone updated this record</h2>
    <p>Review their changes before submitting a new version.</p>
  </section>
  <dl class="syn-record-fields">
    <div><dt>Campaign name</dt><dd><div class="syn-change-pair">
      <span class="syn-change-before"><small>Previous</small><del>Fall</del></span>
      <span class="syn-change-after"><small>Updated</small><ins>Winter</ins></span>
    </div></dd></div>
  </dl>
</section>
```

**Host behavior contract:** Render the state **only when it is true**. A pending
request requires the host to manage loading and submission controls; "saved"
requires a confirmed server response, not an optimistic assumption. On
failure preserve inputs; on conflict enforce record version checking
(e.g., ETag/If-Match or an optimistic lock), offer a real comparison/reload
path, and never overwrite concurrently edited data without policy checks.
Authorize mutations, protect against CSRF where applicable, and record audit
history on the server. For asynchronous updates, create a persistent
`role="status"` region before updating its content, and use `role="alert"`
only when immediate interruption is justified; **the static gallery does not
claim any live announcements**. CSS cannot retry requests, manage focus,
detect stale versions, or persist records. Test the integration at 320 CSS
pixels, 400% zoom, keyboard-only navigation, screen readers and forced colors.
## File selection and lifecycle presentation (alpha.5 source candidate)

Use the existing native file input (`.syn-input[type="file"]`) with a real
`label`, then load optional `syntyr.recipes.css` for an ordered
`ol.syn-file-queue` containing `li.syn-file-item` entries. An optional
`.syn-file-item-header` keeps names and textual status together without
forcing a fixed width. Use only one truthfully rendered state per entry:
`data-syn-state="queued|uploading|complete|failed"`.
Preserve `role="list"` on the ordered queue when removing visual markers:
Safari/VoiceOver can otherwise omit the list and its item count from
accessibility announcements outside a navigation landmark.

[Open the static file-lifecycle example](../examples/file-lifecycle.html).
This recipe is **presentation only**, not a drag-and-drop zone, upload engine,
retry handler, virus scanner, or file storage client. File choice works
natively without JavaScript, but choosing a file does not upload it.

```html
<section class="syn-root" data-syn-theme="studio">
  <label class="syn-label" for="attachments">Attachments</label>
  <input id="attachments" class="syn-input" type="file" multiple>
  <ol class="syn-file-queue" role="list">
    <li class="syn-file-item" data-syn-state="uploading">
      <div class="syn-file-item-header">
        <strong>report.pdf</strong><span>Uploading · 42%</span>
      </div>
      <progress class="syn-meter" value="42" max="100"
                aria-label="Report upload progress">42%</progress>
    </li>
  </ol>
</section>
```

**Host application contract:** Do not render completion until the server
confirms durable storage. Compute actual byte-based progress if available;
omit `value` on `<progress>` only when an upload is genuinely indeterminate.
Honor file size/type limits, authorization, CSRF protections when applicable,
safe filenames, cancellation, retries, and server-side scanning as required.
Retain selected files after recoverable errors when the browser permits,
and expose real error details with field associations. Create a persistent
live status region in the host if asynchronous changes require announcements;
CSS and a static snapshot cannot announce an update. No automatic drag/drop
or upload happens with these classes. Test responsive zoom, forced colors,
keyboard navigation, real upload failure and assistive technology in the host.


## Reusing recipes across stacks

- **Go / templ, PHP, Django, Rust templates:** Make recipes server-rendered partials and pass content as arguments.
- **HTMX / Datastar:** Use the same classes on server-returned fragments. Their JavaScript, if chosen, is outside the CSS library.
- **React / Vue / Astro:** Wrap the exact markup in framework components only when the host application calls for it.

Favor stable component classes and CSS variables over copying long lists of generated utilities. See [contract](components.md) and [Tailwind research](tailwind-research.md).

## Accessible navigation and loading placeholders

Breadcrumbs use a real ordered list inside a labeled navigation landmark. The separator is a CSS border rather than spoken punctuation:

```html
<nav class="syn-breadcrumbs" aria-label="Breadcrumb">
  <ol>
    <li><a href="/">Home</a></li>
    <li><span aria-current="page">Reports</span></li>
  </ol>
</nav>
```

Page controls are **real links**, not inert buttons. Match the selected page to the actual URL, and label any symbol-only links:

```html
<nav class="syn-pagination" aria-label="Results pages">
  <a class="syn-page-link" href="?page=1">1</a>
  <a class="syn-page-link" href="?page=2" aria-current="page">2</a>
  <a class="syn-page-link" href="?page=3">3</a>
</nav>
```

Skeletons are deliberately static. Hide the visual placeholder from assistive technology and announce loading outside it with application-owned state. Do not leave an infinite loading message or use fake progress values:

```html
<section aria-busy="true" aria-label="Reports">
  <p role="status">Loading reports…</p>
  <span class="syn-skeleton" aria-hidden="true"></span>
  <span class="syn-skeleton syn-skeleton--short" aria-hidden="true"></span>
</section>
```

When loading finishes, the application replaces the placeholders with content and clears `aria-busy`. The CSS library does not implement fetching or state changes.

## Server-rendered SaaS filter and settings patterns

The [SaaS workflow demonstration](../examples/saas-workflows.html) shows how to combine standard HTML search forms, a table, navigation landmarks, native settings disclosures and no-JavaScript placeholders. The page's data is illustrative and **is not filtered**; the following behavior belongs to the host application:

- Parse and validate `query`, `status`, `owner` and `page` on the server, apply authorization before filtering, paginate the results, and escape all rendered user input.
- Preserve submitted form values and `aria-current` based on the actual result page, and emit a truthful result count plus empty-state or error message.
- Persist preferences in the server's settings endpoint, with CSRF protection for changes; the static demo intentionally has no save button.
- When using HTMX, Datastar or another enhancement layer, keep GET filters, ordinary links and form labels working without client-side JavaScript.

The scoped `examples/saas-workflows.css` stylesheet contains layout glue only and is **not** added to the distributed core or all-in-one bundle.

## Composed operations workflows: progress, activity and decisions (alpha.5 source only)

The [live workflow-operations demonstration](../examples/workflow-operations.html)
shows three task-specific patterns inspired by operational and AI agent interfaces.
It deliberately **adds no new Syntyr component API or runtime dependency**.
The example consumes the unreleased source-candidate `syntyr.core.css` and
`syntyr.recipes.css`; it is **not included in published alpha.4**.
The example-specific stylesheet is layout glue and is not distributed as core CSS.

### 1. Progress: ordered list and authoritative state

```html
<section class="syn-root syn-region" data-syn-theme="studio">
  <h2>Deployment progress</h2>
  <ol class="syn-steps syn-steps--vertical" role="list" aria-label="Deployment progress">
    <li class="syn-step" data-syn-state="complete">
      <span class="syn-step-label">Checks complete</span>
    </li>
    <li class="syn-step" aria-current="step">
      <span class="syn-step-label">Approval pending (current)</span>
    </li>
    <li class="syn-step">
      <span class="syn-step-label">Publish (not started)</span>
    </li>
  </ol>
</section>
```

The server must decide which step is current and which are complete or failed.
Only one step has `aria-current="step"`; CSS never computes progress.
If there is no current step, remove `aria-current` rather than fabricating one.

### 2. Execution activity: event list and native disclosures

```html
<section class="syn-root" data-syn-theme="studio">
  <h2>Activity</h2>
  <ol class="syn-activity-timeline" role="list" aria-label="Execution events">
    <li>
      <strong>Validation succeeded</strong>
      <time datetime="2026-11-17T09:12:10-03:00">09:12:10</time>
      <details class="syn-details">
        <summary>View sanitized diagnostics</summary>
        <pre><code>18 checks passed</code></pre>
      </details>
    </li>
  </ol>
</section>
```

Server applications supply trusted status, duration and log content. Render
diagnostics as escaped **text**, never injected HTML; redact secrets and personal
data. For live updates, the application—not CSS—owns polling/streaming, retry,
completion announcements and `aria-busy` lifecycle. Do not announce an entire
rapidly updated event feed with `aria-live="assertive"`.

### 3. Approval: honest actions and durable outcomes

Compose an `article.syn-app-card`, a visible `syn-status` and ordinary native
buttons or forms. In a static preview, **disable mutation buttons**; do not show
fake approval confirmations. In a working application, bind each approval/rejection
to a real authenticated **POST** route. Verify role and object authorization,
CSRF protection, the decision's current revision and idempotency on the server.
Do not optimistically remove a request or claim success before the server commits
its decision. Surface rejected, expired, conflict and network-failure states,
and maintain an auditable record with actor and timestamp. Only expose actions
the current reviewer is permitted to take.

Prefer the existing `syn-steps`, `syn-activity-timeline`, `syn-details` and
`syn-app-card` compositions before adding variants, React widgets or extra
CSS modules. The demo uses them unchanged and works with server templates,
HTMX, or React. This is a **presentation example**, not a workflow engine.


## Intrinsic responsive layouts (optional recipes CSS)

Load `syntyr.core.css` plus `syntyr.recipes.css`. The layout primitives are
scoped to `.syn-root` and require no JavaScript, framework or viewport media
queries. Their children are ordinary semantic HTML.

```html
<section class="syn-root">
  <div class="syn-sidebar" style="--syn-sidebar-width: 14rem">
    <aside>Navigation or filters</aside>
    <main>Main content</main>
  </div>
  <div class="syn-switcher" style="--syn-switcher-threshold: 42rem">
    <article>First card</article>
    <article>Second card</article>
    <article>Third card</article>
  </div>
</section>
```

`.syn-sidebar` expects **exactly two** direct children: sidebar first,
content second. Defaults: sidebar 16rem, content minimum 28rem (capped at
100% of available width). In narrow containers they stack, and neither
child is forced wider than the container by the layout primitive. Content
with long unbreakable text should still use appropriate wrapping.

`.syn-switcher` treats all direct children uniformly. Above the 40rem
default threshold they share a row; below it every child stacks. Override
`--syn-switcher-threshold` per instance. This differs from `.syn-grid`,
which can display different numbers of columns at intermediate widths.

Use opt-in fluid type classes `.syn-fluid-display`, `.syn-fluid-lede` and
`.syn-reading`. The CSS custom properties `--syn-fluid-display-size`,
`--syn-type-lede` and `--syn-reading-width` can be overridden in plain
application CSS. Keep real document headings and reading order.

See [the working minimalist demo](../examples/minimalist-patterns.html).


## Collection workspaces and error recovery (source candidate)

The optional recipes stylesheet contains `.syn-collection-toolbar`, `.syn-collection-actions`,
`.syn-bulk-actions`, `.syn-table--compact`, `.syn-result-state` and
`.syn-error-summary`. They extend the existing `.syn-filter-bar`, `.syn-table`,
`.syn-detail-layout` and base form classes; they do not ship a JS data grid.

[Static resource and error example](../examples/resource-workspace.html) demonstrates:
- A native GET search form with named query parameters (disabled in the static demo so it cannot navigate to an unimplemented route). Implement `/resources` on your server; the static example route does not filter results.
- A titled table, an optional dense presentation, explicit result states, and disabled bulk-action preview. The backend must enforce selection, authorization, CSRF and idempotency for mutations.
- A server-rendered error summary with field-anchor links, `aria-invalid`, and an `aria-describedby` reference to a visible field error. Preserve entered values and ensure the server response moves keyboard focus to the error summary after a failed submission (or sends an equivalent heading-focused full-page response). Never claim client-side styling performs validation.
- Preserve search/filter/sort state in URL parameters. Announce actual result counts, not sample counts. Display no-result or service-error state only when it is true.

The example is illustrative, **not a configured server**. Avoid relying on color alone to convey status. Test with a keyboard, screen reader, 320 CSS-pixel viewport, text zoom and forced-colors mode.

For a **runnable, zero-JavaScript reference**, see the [Go resource workbench](https://github.com/dporkka/syntyr-css/tree/main/examples/go-resource-workbench). It composes the existing filter, table, bulk-action and inspector classes with real server-side GET filtering, status filters, sorting, column and theme settings, record links and read-only bulk-selection previews, and real previous/next pagination with preserved view state. Checked-row previews are limited to records on the current server-rendered page, whereas an explicit matching-scope preview spans all filtered pages. Unlike the static markup, the Go example actually constrains result sets. An empty checked selection never means all matching records: selecting the full matching set is an explicit separate link. The example additionally demonstrates a local-only native POST edit for owner and status with a signed CSRF form token, input validation and a safe redirect. Its in-memory changes reset on restart; the unauthenticated server refuses non-loopback binds. It has no accounts, tenant isolation, persistent records or durable authorization; production apps must supply those behaviors.

## Native query filters and record review (alpha.5 source candidate)

The [copy-owned filter and review composition](../examples/query-review.html)
reuses `.syn-filter-bar`, `.syn-filter-choices`, `.syn-chip`,
and `dl.syn-record-fields`. The example is a **static server-rendered snapshot**;
it does not filter results or perform edits without a host application.

- Submit labelled controls with a native `method="get"` form. The server must validate the query and re-render selected values, counts, and the matching results.
- Render each removable filter as a real link that drops exactly one encoded query parameter while preserving the others. Use descriptive accessible names, not icon-only removal affordances. The server must generate these URLs from validated state.
- Review record details as `dl` / `dt` / `dd` pairs and use Edit links to disabled example fields in this static snapshot; hosts must substitute real, authorized edit routes. Never style a static text value as a working editable field.
- Filtering, authorization, permissions, mutations, and persistence belong to the host. These composition classes add **no new core CSS or mandatory JavaScript**.

## Enterprise collection, sheet and evidence compositions (alpha.5 source candidate)

The optional `syntyr.recipes.css` also includes reusable patterns tested against
Adacavo-style resource workflows. They are original MIT-licensed presentation
recipes, **not a port of Adacavo's application code**. See the
[zero-JavaScript example](../examples/enterprise-compositions.html).

- `.syn-view-switcher` contains real links (`aria-current="page"`) for
  server-selected views, or host-controlled toggle buttons
  (`aria-pressed="true"`). A link doesn't implement filtering, and a button
  needs a real event handler; never claim a view switched solely from CSS.
- `.syn-sheet` and `.syn-sheet-header`, `.syn-sheet-body`,
  `.syn-sheet-footer` style a native **nonmodal** `[popover]` panel, or a
  native modal `<dialog>`. Native `popovertarget` works without JavaScript
  in supported browsers. A popover **does not** trap focus or make the rest of
  the page inert. For modal editing, call `showModal()` or use supported
  `commandfor`/`command="show-modal"` and retain a direct-page fallback.
  The `--syn-sheet-width` CSS property defaults to `30rem`; set it on the
  sheet to adjust width. When closed, neither element is forced visible by
  the grid display rules. At extreme text zoom or short viewport heights,
  the whole sheet scrolls so its footer actions remain reachable; the body
  retains a minimum scroll region. When the body can overflow independently,
  make that region keyboard-focusable (`tabindex="0"`) and name it with
  `aria-labelledby` referencing a visible heading, as the example does.
  Check both record details and each footer action at 320px and 400% text.
  Don't set `aria-modal="true"` on the nonmodal popover.
- `.syn-evidence-grid`, `.syn-evidence-card`, `.syn-evidence-media`,
  `.syn-evidence-body`, `.syn-evidence-meta` and `.syn-evidence-actions`
  present `figure`, `figcaption`, `dl` and `time` records. Use
  `.syn-evidence-media--placeholder` for text-only media fallbacks so
  enlarged text can expand vertically rather than being clipped. Reuse the
  existing `.syn-status` for server-validated textual status. Application
  code owns uploads, verification, EXIF/GPS, image fallbacks, and approvals.

All styles require a `.syn-root` ancestor, use semantic tokens, and are
excluded from `syntyr.core.css`. The illustration uses labeled placeholders,
not real customer evidence. Test keyboard and touch interactions, actual
screen-reader focus behavior, 400% zoom, forced colors, RTL, and lengthy
translated metadata in the consuming app before production use.

## Permission matrix — role/capability review

The [copy-owned permissions example](../examples/permission-matrix.html) combines
Syntyr core and recipes with a small application-local stylesheet. It takes
enterprise-table and accessible-form ideas from mature design systems without
adding a component to Syntyr's core or introducing JavaScript.

- Real \`table\`, \`caption\`, column/row headers and visible \`input type="checkbox"\`
  controls communicate the role/capability intersection to assistive technology.
  Every checkbox has an explicit, role-and-capability-specific label.
- A named, keyboard-focusable scroll region preserves the wide matrix at mobile
  widths and large zoom levels. Test scrolling with a keyboard and screen reader.
- Viewer/Editor inputs are an unsaved local demonstration. The disabled
  Administrator column demonstrates a system-fixed role, not a policy imposed
  by Syntyr. Browser-disabled fields will not submit in a real form.
- To make this a working settings page, render it from trusted server policy,
  wrap it in an authenticated mutation form with CSRF protection and a policy
  version, then validate every capability server-side before an atomic update.
  Audit the actor and changes; never trust a checked box or a hidden role field
  for authorization.
- Do not present a static demo as a live access-control feature, persist changes
  in browser storage, or claim accessibility compliance without manual testing.

The markup belongs to the host application; this is an integration pattern,
not a JavaScript permissions widget or a substitute for authorization.
