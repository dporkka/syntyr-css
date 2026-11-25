# Dropdowns and selects

Syntyr supplies styling; native HTML owns ordinary behavior. Use the **native** primitive that matches the task rather than treating every popup as a menu.

## Choose the right primitive

| Need | Use | Keyboard | Runtime |
| --- | --- | --- | --- |
| Select one value in a form | `<select class="syn-select">` | Native select keys | None |
| Open a set of ordinary links/buttons | `[popover].syn-popover.syn-dropdown` | Tab and Escape | None |
| Show expandable information | `<details class="syn-details">` | Native disclosure keys | None |
| Desktop-style application menu | Optional `enhanceMenu()` adapter | ArrowDown, ArrowUp, Home, End, typeahead | Explicit opt-in module |
| Select several values in a form | `<select class="syn-select" multiple name="regions">` | Native multi-select keys | None |
| Autocomplete or hierarchical menu | Use an accessible, tested application widget | Full ARIA pattern | App-owned |

The no-JS example is [examples/dropdowns.html](https://syntyr-css.pages.dev/examples/dropdowns.html). The native Popover API provides light dismissal and Escape behavior in supporting browsers. Older browsers need an alternative if the actions are essential.

## Scriptless action panel

```html
<button type="button" class="syn-button" popovertarget="record-actions">Actions</button>
<div id="record-actions" popover class="syn-popover syn-popover--anchored syn-dropdown">
  <p class="syn-dropdown__group-label">Record</p>
  <a class="syn-dropdown__item" href="/records/123">View record</a>
  <button type="button" class="syn-dropdown__item" popovertarget="record-actions"
          popovertargetaction="hide">Close</button>
</div>
```

**Do not add `role="menu"` to this pattern.** The browser's normal Tab navigation is intentional. Use buttons for actions and links for navigation. `aria-disabled="true"` alone does not suppress navigation or handlers; use real `disabled` buttons or enforce the disabled condition in the application.

The dropdown CSS supplies compact rows, dividers, group headings, optional keyboard shortcut labels, selected and danger visual treatments, max-block-size scrolling, and a viewport-positioned fallback when anchor positioning is unsupported. Show shortcut hints only for real, implemented keybindings; use `aria-hidden="true"` for redundant decorative key glyphs.

## Customizable native select (experimental)

```html
<label class="syn-label" for="region">Region
  <select id="region" name="region" class="syn-select syn-select--enhanced">
    <option value="north">North</option><option value="south">South</option>
  </select>
</label>
```

The opt-in `base-select` appearance and `::picker(select)` styles are wrapped in `@supports (appearance: base-select)`. They do not replace the element or its value/submission semantics. Test the actual browser/OS/version you support; custom picker rendering is not uniform across engines. Do not expect arbitrary option markup to work everywhere.

## Optional application menu adapter

Only enable this if an application needs WAI-ARIA menu keyboard interactions. This module is **not loaded by the CSS**, and importing it does not auto-initialize menus.

```html
<button type="button" class="syn-button" popovertarget="editor-menu">Editor actions</button>
<div id="editor-menu" popover data-syn-menu aria-label="Editor actions"
     class="syn-popover syn-popover--anchored syn-dropdown">
  <button type="button" class="syn-dropdown__item" data-syn-menu-item>Rename</button>
  <button type="button" class="syn-dropdown__item" data-syn-menu-item>Duplicate</button>
  <button type="button" class="syn-dropdown__item" data-syn-menu-item disabled>Archive</button>
</div>
<script type="module">
  // Copy the exported menu.mjs to your public/assets directory.
  import { enhanceMenu } from '/assets/syntyr-menu.mjs';
  const dispose = enhanceMenu(document.getElementById('editor-menu'));
  // Call dispose() if the host framework unmounts this menu.
</script>
```

The browser-resolvable URL above assumes you have copied the exported
integrations/dropdown/menu.mjs to /assets/syntyr-menu.mjs in your application.
When using a bundler instead, import from the package subpath
@syntyr/css/menu.mjs. Neither path is automatically installed as a public
URL by the CSS framework. The adapter rejects popover="manual" because
manual popovers do not natively dismiss on Escape.

The adapter sets and restores the trigger's `aria-haspopup`, `aria-controls`, and `aria-expanded` attributes. It enables `role="menu"`, menuitem semantics, ArrowDown/ArrowUp navigation, Home/End, typeahead, and initial focus only after it starts. Without JavaScript, the same markup remains a normal set of tabbable controls. Escape uses native popover dismissal. Checkboxes, radio groups, nested submenus and searchable comboboxes are **not** provided; don't use their ARIA roles without implementing and testing their full behavior.

## QA checklist

Test at 320px and 400% zoom, with long translated labels, RTL direction, touch, keyboard-only Tab / Shift+Tab / Escape, and screen reader announcements (NVDA/Firefox, VoiceOver/Safari, or Orca/Firefox). Check selected/disabled items, forced colors, reduced motion, multiple simultaneous menus, and near-viewport-edge anchor placement. Automated assertions are necessary but not a substitute for manual screen reader review.
