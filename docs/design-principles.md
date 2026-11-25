# Design principles and conformance contract

Status: **unreleased alpha.5 source guidance**. Syntyr is a scoped, CSS-first
presentation system, not a JavaScript widget library. This guide distills
practices shared by mature design systems (Material, Fluent, Carbon, Spectrum,
Atlassian, Apple HIG and USWDS) into **portable rules** rather than borrowing
any brand's visual assets or platform-specific components.

**Priority order:** semantic meaning and accessibility > readable hierarchy and
feedback > predictable composition > optional aesthetics. When those conflict,
an ornamental effect or familiar-looking mockup must give way.

## Universal defaults

1. **Information hierarchy:** one clear page purpose, useful heading order,
   one primary action per decision area and subdued secondary actions. Use
   headings for structure, not to obtain a large font.
2. **Consistent spacing:** begin with `--syn-space-1` through
   `--syn-space-5`. Group related controls closely, separate different
   content regions deliberately. There is no universally correct 8px grid.
3. **Readable typography:** prefer `--syn-type-body`, `--syn-type-heading`,
   `--syn-type-section`, `--syn-type-display` and the shared body leading.
   Use legible text and avoid substituting tiny fonts for compact density.
4. **Semantic HTML and familiar behavior:** actions use buttons; navigation
   uses links; labeled inputs use native controls; tables have real headers.
   Prefer `details`, `dialog` and `popover` when their native behavior fits.
5. **Meaningful color roles:** use `--syn-bg`, `--syn-surface`, `--syn-text`,
   `--syn-muted`, `--syn-accent`, `--syn-on-accent`, and named
   success/warning/danger tokens. Color is never the only status cue.
6. **Accessible interaction:** visible `:focus-visible`, contrast, keyboard
   reachability, target size, label/description associations, readable error
   text, narrow-screen reflow, 200%/400% zoom and reduced motion.
   Target WCAG 2.2 AA in representative, *rendered* application flows.
7. **Responsive context:** adapt layouts to available space; prefer intrinsic
   layout and container queries for embedded regions. Never let dense tables
   silently clip important data; make overflow regions keyboard reachable.
8. **Feedback and recovery:** every mutation needs truthful pending, success
   and error feedback from its host application; invalid fields should explain
   correction and preserve input. CSS does not implement validation or alerts.
9. **Progressive disclosure:** defer uncommon settings inside clearly named
   native disclosures or separate screens. Do not hide essential actions.
10. **Independent customization:** theme, density, geometry, typography and
    intensity are separate axes. Customizations change semantic tokens; avoid
    per-theme component forks and `!important` escalation.

These are implementation principles, not proof that a particular page satisfies
accessibility law. See [DESIGN.md](../DESIGN.md), [architecture](../ARCHITECTURE.md)
and [the accessibility guide](accessibility.md).

## Component state contract

| Component family | Real semantics | Required presentation and verification |
| --- | --- | --- |
| Action buttons | `button type="button"` or `button type="submit"`; `a href` only for navigation | default, hover when meaningful, `:focus-visible`, pressed, true disabled; distinguish toggle `aria-pressed` from decoration |
| Inputs and form groups | paired `label` + `id`, `fieldset`/`legend`, optional `aria-describedby` | default, focus, disabled, `:user-invalid` or synchronized `aria-invalid`, explicit error text |
| Navigation | `nav`, real links, `aria-current` on current destination | visible keyboard focus, active destination, wrapping/overflow, short discernible names |
| Data tables | `caption`, `th scope`, numeric cells when helpful | row/cell hierarchy, legible density, focusable overflow region, optional `aria-sort` only when sorting exists |
| Native overlays | `details`/`summary`, `dialog`, or `popover` | open/closed, visible focus, Escape/dismissal according to browser API; host owns custom focus logic |
| Feedback and status | meaningful text, optionally `role="status"`/`role="alert"` | not color-only; convey busy, success, warning and errors truthfully |
| Loading | host-owned lifecycle and message; optional decorative `.syn-skeleton` | never use skeletons as the only status announcement; `aria-busy` does not disable a button |
| Panels and layouts | `main`, `section`, headings, labels | stable reading order, logical spacing, mobile reflow and no accidental nesting of landmarks |

A state that exists only visually is not a substitute for a corresponding native
or accessible semantic state. Avoid fabricating `aria-selected`, `aria-busy`
or `aria-disabled` to make a screenshot resemble a working application.
See [components](components.md), [component authoring](component-authoring.md)
and [form composition recipes](component-recipes.md).

## Composition examples

The following copy-owned patterns use **only `syntyr.core.css`**. The
backend/application is responsible for actual operations, authorization,
pending-state announcements, validation and persistence. Paths and records
are illustrative, not implemented service endpoints.

### 1. Responsive overview with sensible emphasis

```html
<main class="syn-root syn-page" data-syn-theme="studio"
      data-syn-density="comfortable">
  <header>
    <h1>Campaign overview</h1>
    <p class="syn-muted">Review active campaigns and recent changes.</p>
    <a class="syn-button syn-button--primary" href="/campaigns/new">New campaign</a>
  </header>
  <section class="syn-region" aria-labelledby="overview-heading">
    <h2 id="overview-heading">Current activity</h2>
    <div class="syn-stats">
      <article class="syn-stat">
        <h3 class="syn-stat-label">Active campaigns</h3>
        <p class="syn-stat-value">12</p>
      </article>
      <article class="syn-stat">
        <h3 class="syn-stat-label">Pending reviews</h3>
        <p class="syn-stat-value">3</p>
      </article>
    </div>
  </section>
</main>
```

Use `.syn-region` *outside* the responsive `.syn-stats` children so the
container query measures the available panel width, not the viewport.
Display real values from the application rather than assuming CSS can compute
metrics.

### 2. Native GET filter and accessible data table

```html
<section class="syn-root" data-syn-theme="studio" aria-labelledby="records-title">
  <h2 id="records-title">Accounts</h2>
  <form class="syn-form" method="get" action="/accounts">
    <label class="syn-label" for="account-query">Account name</label>
    <input class="syn-input" id="account-query" type="search" name="q">
    <div class="syn-actions">
      <button class="syn-button syn-button--primary" type="submit">Filter accounts</button>
      <a class="syn-button" href="/accounts">Clear filter</a>
    </div>
  </form>
  <div class="syn-table-wrap" role="region" aria-label="Accounts table"
       tabindex="0">
    <table class="syn-table">
      <caption>Account directory</caption>
      <thead>
        <tr><th scope="col">Account</th><th scope="col">Status</th></tr>
      </thead>
      <tbody>
        <tr><th scope="row">Northwind</th><td>Active</td></tr>
        <tr><th scope="row">Contoso</th><td>Review needed</td></tr>
      </tbody>
    </table>
  </div>
</section>
```

Avoid `role="grid"` unless the application implements grid keyboard
interaction. If the backend filters the table, preserve the user's query and
announce updated results appropriately. These CSS classes style the native
elements but never sort, search or persist data.

### 3. Labeled settings with progressive disclosure

```html
<main class="syn-root" data-syn-theme="studio">
  <h1>Organization settings</h1>
  <form class="syn-form" action="/settings" method="post">
    <fieldset class="syn-fieldset">
      <legend>Organization details</legend>
      <div class="syn-field">
        <label class="syn-label" for="org-name">Name</label>
        <input class="syn-input" id="org-name" name="name" required
               aria-describedby="org-hint">
        <p class="syn-help" id="org-hint">Shown to your teammates.</p>
      </div>
      <details class="syn-details">
        <summary>Advanced settings</summary>
        <label class="syn-label" for="timezone">Time zone</label>
        <select class="syn-select" id="timezone" name="timezone">
          <option value="UTC">UTC</option>
          <option value="America/Sao_Paulo">Brasília</option>
        </select>
      </details>
    </fieldset>
    <button class="syn-button syn-button--primary" type="submit">
      Save settings
    </button>
  </form>
</main>
```

A real POST handler must check CSRF, permissions and validity. On an error,
rerender entered values, set `aria-invalid="true"` for invalid fields,
associate the actual error text via `aria-describedby`, and provide a
perceivable status. The demo deliberately does not fake saved-state feedback.

For richer CRM, filter toolbar and enterprise layout compositions, reuse
[existing recipes](recipes.md), [data-table guidance](data-tables.md)
and [the static CRM example](../examples/crm.html). Do not create redundant
CSS classes solely to implement these HTML patterns.

## Deliberate non-defaults

**Never universalize** Material-style elevation, glass effects, a specific
border radius, an 8px-only grid, desktop-like density, animation, or a single
navigation pattern. These are product/platform choices. Studio's quiet neutral
presentation is the default; Grid, Noir, strong effects, geometry and
additional density are opt-in. Style must never reduce semantic or accessibility
quality. Respect `prefers-reduced-motion` and `forced-colors`.

## Automated check and review protocol

Run the source-level semantic palette check:

```sh
python3 scripts/design_conformance.py
python3 scripts/design_conformance.py --format json
python3 -m unittest discover -s tests -p 'test_design_conformance.py'
```

It evaluates **12 defined semantic foreground/background roles across seven
built-in palettes (84 pair checks)** and fails closed for missing or
nonliteral colors. Roles are explicit so design changes cannot silently skip a
required pairing. This checks static source colors, including the primary
button foreground, link/accent, statuses, visible focus/accent against surfaces,
and strong borders. It is included in the standard Python test suite.

## What automated checks do not prove

The tool **does not validate rendered contrast** involving gradients,
`color-mix()`, overlays, icon graphics, every hover/focus interaction,
user-defined palettes, `light-dark()` computed values, nested theme paint
compositing or transparent surfaces. Nor does it validate keyboard behavior,
screen-reader announcements, zoom/resize, actual touch targets, server errors,
or brand/legal accessibility certification.

For release approval, separately run the browser/reflow/axe matrices and
record genuine keyboard, screen-reader, 200%/400% browser zoom, real OS
high-contrast and manual color-contrast evidence. Inconclusive axe nodes stay
unresolved until checked on their *effective painted backgrounds*. See the
[alpha.5 review log](accessibility-alpha5-review.md). Do not claim WCAG
conformance from this palette report.
