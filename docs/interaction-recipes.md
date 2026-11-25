# Interaction recipes: native first, headless when necessary

**Version:** unreleased alpha.5 source candidate (0.3.0-alpha.5). The currently
published immutable alpha.4 release does not contain every candidate
adapter or document here. Verify availability in your installed release.

Syntyr styles interfaces; it does not implement widget state or keyboard
controllers. Start with HTML's own behavior and add **optional application
dependencies** for interactions that really require them.

This is a source-validated, machine-readable set of integration references;
the presence of regression tests does not certify accessibility, nor
does it claim that every browser or assistive technology has been tested.
The canonical data is [interaction-recipes.json](../metadata/interaction-recipes.json).

## Choose the lightest behavior owner

| Recipe | When to use | Behavior owner | Evidence |
| --- | --- | --- | --- |
| [Native single select and form submission](#native-single-select-and-form-submission) | Choose from a short fixed list without search or custom option content. | Browser controls; host receives and validates GET parameters | [test source](https://github.com/dporkka/syntyr-css/blob/main/tests/interaction_recipe_browser.py) |
| [Native action popover](#native-action-popover) | Provide ordinary links or buttons in a lightweight nonmodal overlay. | Browser Popover API, not ARIA menu-item arrow navigation | [test source](https://github.com/dporkka/syntyr-css/blob/main/tests/interaction_recipe_browser.py) |
| [Native modal dialog with disclosure fallback](#native-modal-dialog-with-disclosure-fallback) | Require a short modal confirmation or preview on browsers supporting invoker commands. | Browser dialog modal and focus behavior; application still owns side effects | [test source](https://github.com/dporkka/syntyr-css/blob/main/tests/interaction_recipe_browser.py) |
| [Semantic table with truthful static sort state](#semantic-table-with-truthful-static-sort-state) | Read data or display a server-sorted snapshot without interactive grid editing. | Browser table semantics; server must implement and validate real sorting | [test source](https://github.com/dporkka/syntyr-css/blob/main/tests/interaction_recipe_browser.py) |
| [Radix menu with real menu keyboard behavior](#radix-menu-with-real-menu-keyboard-behavior) | Need ARIA menu semantics, roving focus, arrow navigation and focus restoration. | Radix DropdownMenu; host owns action authorization | [test source](https://github.com/dporkka/syntyr-css/blob/main/examples/headless-react/tests/interactions.spec.ts) |
| [React Aria searchable combobox](#react-aria-searchable-combobox) | Need filtered selection, keyboard option navigation and accessible active focus. | React Aria ComboBox; host owns async fetching and persistence | [test source](https://github.com/dporkka/syntyr-css/blob/main/examples/headless-react/tests/interactions.spec.ts) |
| [React Aria sortable inventory grid](#react-aria-sortable-inventory-grid) | Need real keyboard grid interactions and client-side sortable columns. | React Aria Table for focus and ARIA; application sorts data | [test source](https://github.com/dporkka/syntyr-css/blob/main/examples/headless-react/tests/interactions.spec.ts) |
| [Radix noncritical notification](#radix-noncritical-notification) | Show transient noncritical feedback with a tested dismissal lifecycle. | Radix Toast; host owns notification semantics and timing | [test source](https://github.com/dporkka/syntyr-css/blob/main/examples/headless-react/tests/interactions.spec.ts) |

## Integration contracts


### Native single select and form submission

- **Type:** native — **behavior:** Browser controls; host receives and validates GET parameters.
- **Source:** [examples/semantic-starter.html](../examples/semantic-starter.html); [guide](progressive-enhancement.md).
- **CSS:** `dist/syntyr.semantic-bundle.css`.
- **Keyboard:** Native Tab, arrow keys, typeahead and form submission.
- **Fallback:** Keep the labeled native select; enhance only if requirements exceed it.
- **Regression source:** [tests/interaction_recipe_browser.py](https://github.com/dporkka/syntyr-css/blob/main/tests/interaction_recipe_browser.py).


### Native action popover

- **Type:** native — **behavior:** Browser Popover API, not ARIA menu-item arrow navigation.
- **Source:** [examples/native-apis.html](../examples/native-apis.html); [guide](native-browser-apis.md).
- **CSS:** `dist/syntyr.css + dist/syntyr.motion.css`.
- **Keyboard:** Tab through actual buttons and links; Escape dismisses.
- **Fallback:** Keep essential actions accessible through regular links or forms.
- **Regression source:** [tests/interaction_recipe_browser.py](https://github.com/dporkka/syntyr-css/blob/main/tests/interaction_recipe_browser.py).


### Native modal dialog with disclosure fallback

- **Type:** native — **behavior:** Browser dialog modal and focus behavior; application still owns side effects.
- **Source:** [examples/native-apis.html](../examples/native-apis.html); [guide](native-browser-apis.md).
- **CSS:** `dist/syntyr.css + dist/syntyr.motion.css`.
- **Keyboard:** Enter opens on supporting browsers, Escape closes, native modal focus management.
- **Fallback:** A real details disclosure in the example remains available if invoker commands fail.
- **Regression source:** [tests/interaction_recipe_browser.py](https://github.com/dporkka/syntyr-css/blob/main/tests/interaction_recipe_browser.py).


### Semantic table with truthful static sort state

- **Type:** native — **behavior:** Browser table semantics; server must implement and validate real sorting.
- **Source:** [examples/data-tables.html](../examples/data-tables.html); [guide](data-tables.md).
- **CSS:** `dist/syntyr.core.css`.
- **Keyboard:** Tab into the named scroll region; regular links when server sorting is provided.
- **Fallback:** Use actual GET sort links on a server endpoint; never fake interactive sorting with CSS.
- **Regression source:** [tests/interaction_recipe_browser.py](https://github.com/dporkka/syntyr-css/blob/main/tests/interaction_recipe_browser.py).


### Radix menu with real menu keyboard behavior

- **Type:** headless — **behavior:** Radix DropdownMenu; host owns action authorization.
- **Source:** [examples/headless-react/src/App.tsx](https://github.com/dporkka/syntyr-css/blob/main/examples/headless-react/src/App.tsx); [guide](headless-interactions.md).
- **CSS:** `dist/syntyr.core.css + integrations/headless/interactions.css`.
- **Keyboard:** Arrow keys, Enter or Space, Escape and focus restoration.
- **Fallback:** Use native popover with normal links and buttons when menu semantics are unnecessary.
- **Regression source:** [examples/headless-react/tests/interactions.spec.ts](https://github.com/dporkka/syntyr-css/blob/main/examples/headless-react/tests/interactions.spec.ts).


### React Aria searchable combobox

- **Type:** headless — **behavior:** React Aria ComboBox; host owns async fetching and persistence.
- **Source:** [examples/headless-react/src/App.tsx](https://github.com/dporkka/syntyr-css/blob/main/examples/headless-react/src/App.tsx); [guide](headless-interactions.md).
- **CSS:** `dist/syntyr.core.css + integrations/headless/interactions.css`.
- **Keyboard:** Typed filtering, arrow navigation, Enter selection and IME support from library.
- **Fallback:** Use a native select or GET search form if live suggestions are not necessary.
- **Regression source:** [examples/headless-react/tests/interactions.spec.ts](https://github.com/dporkka/syntyr-css/blob/main/examples/headless-react/tests/interactions.spec.ts).


### React Aria sortable inventory grid

- **Type:** headless — **behavior:** React Aria Table for focus and ARIA; application sorts data.
- **Source:** [examples/headless-react/src/App.tsx](https://github.com/dporkka/syntyr-css/blob/main/examples/headless-react/src/App.tsx); [guide](headless-interactions.md).
- **CSS:** `dist/syntyr.core.css`.
- **Keyboard:** Column-header activation, grid navigation, announced sort state and retained focus.
- **Fallback:** Use a plain table with server-side GET sorting unless grid keyboard behavior is needed.
- **Regression source:** [examples/headless-react/tests/interactions.spec.ts](https://github.com/dporkka/syntyr-css/blob/main/examples/headless-react/tests/interactions.spec.ts).


### Radix noncritical notification

- **Type:** headless — **behavior:** Radix Toast; host owns notification semantics and timing.
- **Source:** [examples/headless-react/src/App.tsx](https://github.com/dporkka/syntyr-css/blob/main/examples/headless-react/src/App.tsx); [guide](headless-interactions.md).
- **CSS:** `dist/syntyr.core.css + integrations/headless/interactions.css`.
- **Keyboard:** Focus, dismiss and nonblocking access provided by the toast primitive.
- **Fallback:** Keep critical or irreversible messages inline or in a real dialog; do not auto-dismiss them.
- **Regression source:** [examples/headless-react/tests/interactions.spec.ts](https://github.com/dporkka/syntyr-css/blob/main/examples/headless-react/tests/interactions.spec.ts).

## Run the regressions

For browser-native recipes (**No JavaScript** in the page):

```sh
python3 tests/interaction_recipe_browser.py --browsers chromium firefox
```

Install Playwright and the selected browser binaries in your **development**
environment. The script deliberately fails if an engine cannot launch.
Feature-dependent dialog behavior is tested with a visible fallback when
invoker commands are unavailable.

For the optional React Aria/Radix examples:

```sh
cd examples/headless-react
npm ci
npm run build
npm test
```

The React fixture includes genuine keyboard navigation, filtering,
selection, focus restoration, grid sorting, and notification dismissal.
The React dependencies do **not** ship in Syntyr's CSS core.

The zero-dependency manifest contract and documentation checks run with:

```sh
python3 -m unittest tests.test_interaction_recipe_catalog -v
python3 scripts/build_interaction_catalog.py --check
```

## Responsibilities that CSS cannot satisfy

- No CSS class implements ARIA semantics, roving focus, key handling,
  asynchronous selection, announcement timing, sorting, or persistence.
- For plain tables, preserve native HTML semantics; do not apply
  `role="grid"` without implementing the full keyboard model.
- A native popover with links is **not** an ARIA menu. It uses normal Tab
  navigation; use Radix only when menu semantics are genuinely required.
- Form submission, server-side validation, authorization and actual data
  sorting belong to the host application. The static sorted-table example
  is a truthful snapshot, not an interactive sorting implementation.
- Portal-mounted headless controls must remain inside a themed
  `.syn-root` or explicitly receive the corresponding theme scope.
- Before production adoption, test NVDA/VoiceOver, keyboard-only use,
  high zoom/reflow, forced colors, reduced motion, IME and mobile touch
  with your chosen browser versions. Automated results are not certification.

Use existing [native browser documentation](native-browser-apis.md),
[data-table guidance](data-tables.md) and
[headless interaction guidance](headless-interactions.md) for further details.
