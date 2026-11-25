# Optional accessible menus, comboboxes, data grids and notifications

Syntyr is a CSS presentation layer with **no runtime JavaScript**. Interactive
menu and combobox ARIA patterns require keyboard, focus, filtering and
selection logic; CSS cannot implement those.

The [opt-in headless adapter](../integrations/headless/interactions.css)
provides token-driven styling for explicit menu, combobox and toast classes.
It does NOT ship in the Syntyr core CSS, all.css or presets.

- Menus: `.syn-menu-surface`, `.syn-menu-item`, `.syn-menu-separator`.
  [Radix DropdownMenu](https://www.radix-ui.com/primitives/docs/components/dropdown-menu)
  owns ARIA roles, arrow navigation, typeahead, dismissal and focus.
- Comboboxes: `.syn-combobox`, `.syn-combobox-field`,
  `.syn-combobox-popover`, `.syn-combobox-listbox`,
  `.syn-combobox-option`. [React Aria ComboBox](https://react-aria.adobe.com/ComboBox)
  owns the filtered options, selection and accessible active focus.
- Sortable data grids: existing `.syn-table` and `.syn-table-sort` classes
  style a real [React Aria Table](https://react-aria.adobe.com/Table). React Aria
  owns the grid keyboard model, focus and sort announcements; the host
  actually sorts the rows and supplies accurate data. No extra CSS module
  or Syntyr JavaScript is required.
- Toasts: `.syn-toast-region`, `.syn-toast`, `.syn-toast-title`,
  `.syn-toast-description`. [Radix Toast](https://www.radix-ui.com/primitives/docs/components/toast)
  owns notification timing, focus, hover pauses, dismissals and live regions.

No styles target generic ARIA roles or library internals. The adapter only
matches Syntyr-named classes and documented state hooks such as
`[data-highlighted]`, `[data-focused]`, `[aria-selected="true"]`, and
`[data-disabled]`. Application semantics remain authoritative.

## Run the isolated React example

[Source](https://github.com/dporkka/syntyr-css/tree/main/examples/headless-react) provides actual React, Radix and React
Aria controls, not inert HTML copies. Its npm dependencies are optional
**application dependencies**. They are not dependencies of Syntyr itself.

~~~sh
cd examples/headless-react
npm ci
npm run build
npx playwright install chromium  # optional browser-test setup
npm test                      # eight Chromium keyboard/state smoke tests
npm run dev
~~~

The example imports both CSS files directly from the repository.
In your own application, include the core stylesheet before the optional
integration stylesheet:

~~~html
<link rel="stylesheet" href="/css/syntyr.core.css">
<link rel="stylesheet" href="/css/headless/interactions.css">
~~~

Or import `@syntyr/css/core.css` followed by
`@syntyr/css/headless.css` if the installed release includes this new export.
The example is *not* hosted as an executable React app in Syntyr's
static documentation site. The existing source branch may be newer than
the published release; always check your installed version.

**Portal scoping:** Radix and React Aria often portal menu/listbox/toast
content to `document.body`. The example uses `body.syn-root` so its portal
content inherits theme tokens and CSS rules. In other apps mount portals
within a stable styled `.syn-root`. Without this, unscoped portal content
will look unstyled. Keep root scope stable across updates.

## Choosing the behavior owner

| Need | Lowest-maintenance baseline | When to add headless behavior |
| --- | --- | --- |
| Choose from a short list | Labeled native `<select>` with built-in keyboard typeahead | Searchable, async, multi-select or rich-options combobox |
| Find an item by text | GET search form; `<datalist>` only when its browser limits are acceptable | Filtered suggestions with controlled selection, async results or IME support |
| Show optional actions | Native `popover` with links and buttons | ARIA menu with roving focus, typeahead and menu-item keyboard semantics |
| Sort a normal data table | Server-sorted HTML table with GET links and truthful `aria-sort` | Keyboard-navigable grid with selection, editing, resizing or complex sorting |
| Confirm destructive action | Native modal `<dialog>` (and a navigable fallback where needed) | An application-owned dialog abstraction with audited focus behavior |

**Contract:** Syntyr never infers behavior from a `syn-*` class and never
sets ARIA state on your behalf. A behavior owner must provide accessible
names, state transitions, focus/keyboard handling, IME, disabled/selection
rules, and asynchronous status announcements as required by its widget.
The host owns data fetching, permissions, persistence, server validation
and actual sort order. A visually styled grid is not a functioning grid.

The React Aria example includes an accessible sortable table with
`sortDescriptor` and `onSortChange`. Unlike a static table, it
intentionally opts into the grid keyboard model. For noninteractive tables,
prefer [native server-sortable tables](data-tables.md), and **do not**
apply `role="grid"` merely to activate visual styling.

## React Aria enterprise resource workflow (optional)

The [runnable React integration](https://github.com/dporkka/syntyr-css/blob/main/examples/headless-react/src/App.tsx) also
illustrates a small, real in-memory resource workspace: search by name,
keyboard- and pointer-operated multi-selection, an explicit **Select matching**
action, a non-mutating selection preview, and a read-only record-details panel.
It composes React Aria Table with existing Syntyr core and **optional recipes**
stylesheets; it is **not** a Syntyr CSS runtime dependency.

This fixture loads all three sample records locally. **Matching** means exactly
the currently loaded, filtered records, not every record in a server database.
Changing the filter clears the selection and detail view so hidden rows cannot
be acted on inadvertently. React Aria can emit an `all` selection key; the
fixture converts it to explicit local IDs instead of carrying a broad token.

For a real paginated/remote inventory, decide whether bulk selection means
visible page, filtered query, or explicitly selected IDs. Keep the scope and
count visible, require confirmation for destructive changes, authorize every
ID/scope server-side, and handle stale filters and result-set changes. Do not
reuse the local selection logic as a server-wide bulk action. The preview
button deliberately makes **no** persistent change.

## Native alternatives that need no headless dependencies

For a short list of links/actions, use HTML `popover` with regular
`<a>` and `<button>` controls. This is a *popover*, not an ARIA
application menu: Tab/Shift+Tab are expected rather than Arrow-key
menu interactions. For small suggestion lists, native `input[list]` and
`datalist` may be sufficient, though their presentation and accessibility
differ by browser and are not completely themeable.

A true ARIA menu needs Arrow navigation, typeahead, Escape, disabled state
and focus restoration. A rich combobox needs correct ARIA relations,
keyboard navigation and IME composition support. Do not recreate these
with hand-written CSS-only role attributes.

## Toast boundaries and accessibility

Toasts are for temporary, noncritical notifications. A confirmation or
irreversible decision must not auto-dismiss: use inline feedback or a dialog.
Do not indiscriminately apply `role="alert"` to every toast. The
host implementation owns announcements, queue limits, timing and
dismissal. The example deliberately labels its actions as demos rather
than claiming any backend persistence.

Test focus and announcements in real browsers and with a screen reader,
plus reduced-motion, forced-colors, high zoom and narrow viewports.
Syntyr's CSS contract tests are **not** accessibility certification.

See [Radix state adapter](radix-integration.md),
[framework integrations](framework-integrations.md) and
[native browser API guidance](native-browser-apis.md).
