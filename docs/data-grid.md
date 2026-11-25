# Data-grid presentation (opt-in, CSS-only)

Syntyr styles **the presentation of an existing data grid**. It does not implement
virtualization, sorting, query execution, clipboard parsing, selection, row editing,
focus navigation, or authorized persistence. Apps such as Adacavo own those behaviors.

## Installation

Load `dist/syntyr.core.css` for tokens and then `dist/syntyr.data-grid.css`.
For an application with its own theme tokens, the standalone grid CSS can be used
without loading Syntyr core, provided the required `--syn-*` color, radius, and
font tokens are mapped inside a `.syn-root` subtree.

This module is not included in `syntyr.core.css` or `syntyr.css`; it is opt-in.
The all-in-one demo bundle includes it. There is **no JavaScript** dependency.

```html
<section class="syn-root" data-syn-theme="studio" data-syn-density="compact">
  <div class="syn-data-grid" role="grid" aria-label="Inventory"
       aria-rowcount="2" aria-colcount="1">
    <div class="syn-data-grid__viewport" role="region" tabindex="0"
         aria-label="Scrollable inventory">
      <div class="syn-data-grid__header" role="rowgroup">
        <div role="row" aria-rowindex="1" class="syn-data-grid__header-row">
          <div class="syn-data-grid__columnheader" role="columnheader"
               style="width:14rem">Inventory face</div>
        </div>
      </div>
      <div role="row" aria-rowindex="2" class="syn-data-grid__row"
           style="position:relative;height:2.5rem">
        <div role="gridcell" class="syn-data-grid__cell"
             style="width:14rem" tabindex="0" aria-readonly="true">
          <span class="syn-data-grid__cell-text">Face 102</span>
        </div>
      </div>
    </div>
    <footer class="syn-data-grid__footer">1 record</footer>
  </div>
</section>
```

## API and responsibilities

The host supplies these classes on the appropriate existing elements:
`syn-data-grid`, `syn-data-grid__viewport`, `syn-data-grid__header`,
`syn-data-grid__columnheader`, `syn-data-grid__row`, `syn-data-grid__cell`,
`syn-data-grid__cell--numeric`, `syn-data-grid__editor`,
`syn-data-grid__toolbar`, `syn-data-grid__status`,
`syn-data-grid__loading` and `syn-data-grid__footer`.

For ellipsis on long text, wrap cell text in a
`<span class="syn-data-grid__cell-text">`; ellipsis cannot reliably apply to
anonymous flex items. Keep the wrapper shrinkable. Editors and other interactive
controls remain application-owned and need their own layout/focus handling.

Nearest density scope wins: `compact`, `comfortable` (including resets), or
`spacious` on the grid itself or an ancestor. Match any virtualizer's row
measurement to the resulting computed `--syn-grid-row-block`.

The host also supplies true state through standard ARIA attributes
(`aria-selected`, `aria-invalid`, `aria-readonly`) and exposes
`data-syn-dirty="true"` and `data-syn-focused="true"` when applicable.
Do not derive permissions or errors from CSS.

Column headers and cells must be given **matching widths** by the host.
For virtualized rows, keep the virtualizer's measured/estimated row height
consistent with rendered CSS height. Keep the header inside the same horizontal
scroll container as the rows to prevent scroll drift.

Use `data-syn-density="compact"` only for visual spacing, not to change
virtualization row heights implicitly. For real grid widgets, the host must
implement a robust ARIA grid keyboard model and verify focus under virtualization,
including 400% zoom, forced colors, and screen reader behavior. Empty/loading and
paste error states need accessible descriptive text and focus management.

The optional CSS uses Syntyr's quiet operational surfaces by default; opt into
Grid/Noir palettes only when appropriate. Avoid glows or decorative motion
on data-heavy workspaces.
