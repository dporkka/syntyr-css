# Native browser APIs in Syntyr

Syntyr is a styling system, **not** a browser API abstraction layer. It ships no runtime JavaScript or polyfill. Use the browser's built-in semantics and state before adding host-owned JavaScript. See the [scriptless integration demo](https://syntyr-css.pages.dev/examples/native-apis.html) (source: `examples/native-apis.html`).

For framework-free custom elements and server-rendered Shadow DOM, see the
[native Web Components fixture](https://github.com/dporkka/syntyr-css/tree/main/examples/web-components) and
[component-authoring contract](component-authoring.md). Syntyr still requires
no Custom Elements runtime for ordinary HTML components.

## Supported integrations

| Primitive | Syntyr integration | Fallback / requirement |
| --- | --- | --- |
| HTML Popover API | `.syn-popover` on `[popover]` with `popovertarget`/`popovertargetaction` controls | Native API requires modern browser; critical content should remain reachable another way for older browsers |
| Invoker Commands | `commandfor` and `command="show-modal"` on buttons targeting `.syn-dialog` | Older browsers may not support commands; give an ordinary link or `<details>` alternative |
| Native `<dialog>` | `.syn-dialog`, `form method="dialog"`, `closedby` or app-owned `requestClose()` | Never replace modal semantics with a popover; handle focus on open/close in real-app tests |
| CSS anchor positioning | `.syn-popover--anchored` alongside `.syn-popover` | With `position-area: bottom`, place near its invoking button; otherwise default to visible corner popover |
| Content-sized fields | `.syn-textarea--autosize` alongside `.syn-textarea` | `field-sizing: content` grows to a maximum height; normal resizable textarea remains functional without support |
| CSS scroll-driven animation | `.syn-reading-progress` in optional motion stylesheet | Decorative, hidden without support or with `prefers-reduced-motion: reduce` |
| Discrete overlay transitions | `.syn-popover--transition` in optional motion stylesheet | Uses `@starting-style` and `transition-behavior: allow-discrete`; no animation without support or when reduced motion is requested |
| Container queries | `.syn-region` with scoped layout patterns | Native responsive CSS replaces ResizeObserver for layout |
| Form constraint validation | `required`, native types, `:user-invalid` and optional `aria-invalid` | Application must provide meaningful feedback and accessible error text |

All new classes are **opt-in**. Core styles only add the anchor and textarea declarations; optional motion requires `syntyr.motion.css` (included in `syntyr.all.css`). Do not load `syntyr.all.css` alongside component files.

For practical scriptless action panels and an optional enhanced menu adapter, see [dropdown patterns](dropdowns.md).

## Example: popover near its invoker

```html
<link rel="stylesheet" href="syntyr.css">
<link rel="stylesheet" href="syntyr.motion.css">
<section class="syn-root" data-syn-theme="studio">
  <button type="button" class="syn-button" popovertarget="account-menu">Account</button>
  <div id="account-menu" popover class="syn-popover syn-popover--anchored syn-popover--transition">
    <a href="/profile">Profile</a>
    <button type="button" popovertarget="account-menu" popovertargetaction="hide">Close</button>
  </div>
</section>
```

The invoker creates an implicit CSS anchor. Do not apply `position-anchor: auto` to unrelated floating elements; supply an explicit anchor relationship or use normal document positioning. The default `.syn-popover` remains visible in browsers without anchor positioning. Make sure production menus have sensible keyboard navigation and screen-reader labeling.

## Example: a dialog without an event handler

```html
<section class="syn-root" data-syn-theme="studio">
  <button type="button" commandfor="confirm-dialog" command="show-modal">Review</button>
  <dialog id="confirm-dialog" class="syn-dialog" aria-labelledby="confirm-title">
    <h2 id="confirm-title">Review changes</h2>
    <form method="dialog"><button type="submit">Close</button></form>
  </dialog>
</section>
```

The HTML Invoker Commands API is progressively available; don't assume the opener works in legacy browsers. A normal link to a review page or a `<details>` fallback gives users an accessible path even without it. Use `dialog.requestClose()` from host JavaScript when a cancelable close request is needed; unlike `dialog.close()`, `requestClose()` fires `cancel` first.

## Application-owned JavaScript (optional)

The following browser APIs are **not** included as Syntyr runtime dependencies. Use them only for capabilities CSS and HTML cannot provide:

- **View Transition API**: for same-document updates, use `document.startViewTransition(updateDOM)` only if present and if reduced-motion is not preferred; otherwise run `updateDOM()` directly. Cross-document navigation requires explicit `@view-transition { navigation: auto; }` in *both* same-origin documents, not in a global Syntyr bundle. Preserve focus, history, and scrolling semantics during navigation.
- **Clipboard API**: `navigator.clipboard.writeText(text)` requires a secure context and permissions/user activation; catch rejections and provide a selectable text/link fallback.
- **Web Share API**: check `navigator.share`, invoke it from a click handler, catch cancellation or errors, and retain an ordinary shareable URL when unavailable. Do not assume mobile-only availability or guaranteed success.
- **ResizeObserver**: reserve for application logic that must know measured dimensions; use CSS container queries for styling. Avoid synchronous DOM changes from observers that trigger resize loops.
- **IntersectionObserver**: use to defer expensive application work, not for effects already supported by `animation-timeline: scroll(root block)`. Prefer native `loading="lazy"` for offscreen images and iframes.
- **Web Animations API**: suitable for interruptible, imperative application animations; use CSS transitions and scroll-driven animations for presentation-only changes and honor reduced motion.
- **Navigation API**: potentially helpful to app routers, but it changes navigation ownership. Do not add it to Syntyr just to style links; ordinary links work without it.

A safe view transition wrapper in application code, not the Syntyr library:

```js
function updateWithViewTransition(updateDOM) {
  if (!document.startViewTransition ||
      matchMedia('(prefers-reduced-motion: reduce)').matches) {
    updateDOM();
    return;
  }
  document.startViewTransition(updateDOM);
}
```


## Static semantic validation for native controls

The opt-in Syntyr checker can catch broken HTML relationships before browser testing:

```sh
python3 scripts/syntyr_check.py --semantic examples/native-apis.html
```

In complete, literal HTML documents it verifies explicit `<label for>` targets
are labelable, native `popovertarget`/`commandfor` targets exist, and
`input[list]` points to `<datalist>`. Built-in dialog commands must target
`<dialog>`. Popover command events may dispatch on HTML targets without a
`popover` attribute; unlike `popovertarget`, this is not an error. It also catches
`<summary>` outside a direct `<details>` parent and image submit controls
without an accessible name. These are **HTML correctness** checks; no Syntyr
class is necessary. The checker deliberately leaves references in fragments
and dynamic templates to the consuming application, and allows custom-element
commands without guessing their behavior.

This is not a full HTML, ARIA, accessibility, or browser-conformance validator.
Use the [WHATWG HTML Standard](https://html.spec.whatwg.org/), an HTML validator,
real browser keyboard and assistive-technology tests, and application-level
validation for server-rendered templates. For a popover, use the declarative
invoker rather than manually adding ARIA expansion state that the browser
already manages; for modal content, use `<dialog>` and a real accessible name.


## Browser-compatibility policy

Test Chromium, Firefox, and WebKit at narrow widths and 200%/400% zoom. CSS feature queries guard anchor placement and scroll-driven timelines. Without the advanced feature, the controls remain styled, dismissible, and operable **where the underlying HTML primitive is supported**. For genuinely older browsers that lack the HTML primitive entirely, provide an alternative interaction or a conditionally loaded host-app polyfill; Syntyr never silently installs one.

Always verify keyboard focus, Escape dismissal, forced-colors mode, native validation, and `prefers-reduced-motion`. Avoid animated content that conveys information unavailable as text. The scroll indicator uses `aria-hidden="true"` and must not replace a semantic progress bar for tasks.

Compatibility references: [Popover API](https://developer.mozilla.org/en-US/docs/Web/API/Popover_API), [Invoker Commands](https://developer.mozilla.org/en-US/docs/Web/API/Invoker_Commands_API), [CSS anchor positioning](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_anchor_positioning), [field-sizing](https://developer.mozilla.org/en-US/docs/Web/CSS/field-sizing), [scroll-driven animations](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_scroll-driven_animations), [View Transition API](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API).
