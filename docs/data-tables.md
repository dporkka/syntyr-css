# Enterprise data tables with native HTML

Syntyr applies general design principles visible in permissively licensed
design systems such as GitHub Primer (MIT), IBM Carbon (Apache-2.0), and
PatternFly (MIT): semantic tables, readable density, opt-in visual states,
and keyboard focus. This is an original **MIT-licensed** implementation.
No third-party source code, brand assets, or artwork is incorporated.

See the [live no JavaScript example](../examples/data-tables.html).

## Import only what you use

Load the Syntyr core CSS, or use the individual components/tokens.css,
components/base.css, and components/data.css entrypoints in that order.
Do not combine both import approaches.

Three opt-in classes complement the existing syn-table class:

- **syn-table-wrap--scroll** on syn-table-wrap creates a bounded two-axis
  scroll region. Set --syn-table-scroll-height (default 24rem).
- **syn-table--sticky** keeps column headings visible in that scroll region,
  with an opaque theme-aware background and header separator.
- **syn-table--striped** highlights alternating body rows. Selected-row
  styling takes precedence over striping.
- **syn-table-sort** renders a decorative directional arrow when its header
  has aria-sort="ascending" or aria-sort="descending".

The browser still owns native table semantics. Do not use role="grid"
unless you implement and test the required grid keyboard interactions.

### Highlighting a record without inventing grid semantics

On a normal data `<table>`, visual emphasis uses
`<tr data-syn-state="selected">` (with a corresponding readable label or
selection checkbox for real user selection). Do **not** put
`aria-selected` on ordinary table rows just to change color. Syntyr's
`aria-selected="true"` row appearance is limited to a table carrying
`role="grid"` or `role="treegrid"`; the host must implement the full
interactive behavior before opting into those roles. This is an alpha.5
source-candidate correction; it does not retroactively alter published
alpha.4 CSS.

For authoring checks, the optional `python3 scripts/syntyr_check.py --semantic your-page.html`
emits advisory findings for ordinary table rows
using ARIA selection and headed data tables without a caption/name.

## Keyboard-scrollable table example

    <section class="syn-root" data-syn-theme="studio" data-syn-density="compact">
      <div class="syn-table-wrap syn-table-wrap--scroll"
           role="region" aria-label="Quarterly revenue table" tabindex="0">
        <table class="syn-table syn-table--sticky syn-table--striped">
          <caption>Revenue by account, sorted by account</caption>
          <thead><tr>
            <th scope="col" aria-sort="ascending"><span class="syn-table-sort">Account</span></th>
            <th scope="col">Revenue</th>
          </tr></thead>
          <tbody>
            <tr><th scope="row">Acme</th><td>$12,000</td></tr>
            <tr><th scope="row">Beta</th><td>$7,000</td></tr>
          </tbody>
        </table>
      </div>
    </section>

The focusable region makes keyboard scrolling discoverable when overflow
exists. Provide a real caption, column headings with scope="col", row
headings with scope="row", and meaningful status text. Do not rely on
stripe color, status color, or pseudo-element arrows as the only signal.

## Sorting is owned by GET and the server

The sorted state must reflect actual data order. When a server-rendered
application supports sorting, it can render a real link:

    <th scope="col" aria-sort="ascending">
      <a class="syn-table-sort" href="/invoices?sort=account&amp;direction=desc">Account</a>
    </th>

The **server** must validate sort and direction against an allowlist,
sort records, generate the next link, and render truthful aria-sort
on only the currently sorted column. CSS cannot sort, filter,
paginate, virtualize, or change selection. The static example
intentionally shows a sorted snapshot without a nonfunctional sorting
control.

## Accessibility, performance, and themes

The styles are scoped to syn-root and inherit the nearest theme and
density tokens. An application may override --syn-table-sticky-offset
for a local scrolling layout. Multi-row headers need individual offset
testing.

The sticky heading retains a visible border in forced-colors mode.
Verify 200% and 400% reflow, keyboard scroll and focus, and real screen
reader behavior in consuming applications. Do not confuse CSS-only
presentation with an accessible grid widget implementation. Large
datasets still need server pagination or selective delivery.
