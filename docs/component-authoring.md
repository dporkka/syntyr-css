# Syntyr component-authoring contract (experimental)

This document defines conventions for application-owned, framework-owned, and
future optional Syntyr-compatible Web Components. It does **not** introduce a
JavaScript API, runtime dependency, or widget package into `@syntyr/css`.

## Public styling contract

1. **Real HTML semantics first:** use `button` for actions, `a` for
   navigation, `label` and correctly associated form controls, native
   `details`/`dialog`/`popover` where supported. A styled generic element
   is not automatically a usable control.
2. **One styling namespace:** use Syntyr classes `.syn-*`, CSS custom
   properties `--syn-*`, and `data-syn-*` only for Syntyr-specific
   presentation state. Do not add a competing global reset or theme registry.
3. **Explicit scope:** document styles require an enclosing `.syn-root`;
   `.syn-semantic` is optional and applies only to its marked subtree.
   Shadow DOM internals must consume inherited tokens via their own styles,
   or explicitly load scoped Syntyr CSS internally.
4. **Theme independence:** components should work under every theme; prefer
   public semantic design tokens over hard-coded palettes and per-theme forks.
5. **State:** use native `disabled`, `checked`, `required`, `aria-pressed`,
   `aria-expanded`, `aria-invalid`, or `aria-busy` where semantically
   appropriate. Use `data-syn-state` only for supplemental visual state,
   and keep any ARIA state synchronized with real behavior.
6. **Events:** reuse standard DOM events when sufficient. If using
   `CustomEvent`, document its name, `detail` payload, dispatch source,
   bubbling and composed behavior. Use `bubbles: true` and `composed: true`
   for consumer-facing events intended to cross a Shadow DOM boundary.
7. **Properties and attributes:** prefer native properties and meaningful
   primitive attributes. Use documented defaults, avoid conflicting states,
   and only reflect state to attributes when useful for external consumers.
8. **Composition:** slots and `::part()` should expose deliberately supported
   customization surfaces, not all internal markup as a permanent API.
   Light DOM components can reuse existing `.syn-*` styles directly.
9. **Progressive enhancement:** preserve readable content and working native
   navigation/form fallbacks if JavaScript is blocked or fails. Interactivity,
   authorization, validation and persistence belong to the host application.
10. **Accessibility:** validate keyboard-only activation and focus order,
    visible `:focus-visible`, accessible names, announced status, motion
    preferences, forced colors, text contrast and zoom/reflow. Do not replace
    accessible native behaviors with untested ARIA patterns.

## Framework-free native Custom Elements

The [runnable native fixture](https://github.com/dporkka/syntyr-css/tree/main/examples/web-components) uses
`HTMLElement`, `customElements.define()`, `observedAttributes`,
`connectedCallback()`, `disconnectedCallback()`, and `CustomEvent`, with
no Lit dependency. Demo-only tags start with `syn-demo-`; they are **not**
a stable widget API or distributed as part of Syntyr CSS.

- Keep attribute/property defaults explicit; update the view in
  `attributeChangedCallback()` rather than maintaining a second state store.
- In `connectedCallback()`, attach listeners only once per connection.
  Cancel listeners with an `AbortController` in `disconnectedCallback()`.
  Reconnecting a host must not duplicate listeners, events, or markup.
- Assign untrusted strings using `textContent`, not template interpolation
  into `innerHTML` or other unsafe HTML sinks.
- Native events need a documented name, payload, and bubbling/composed contract.
  Retain real button keyboard semantics instead of inventing key handlers.
- `aria-busy` reports operational state, and `disabled` prevents activation.
  A custom CSS state is not a substitute for an accessible state or status text.
  Place a live status announcement **outside** a region with `aria-busy="true"`;
  assistive technologies may defer updates to busy descendants.
- Use `aria-pressed` only for an actual toggle button with a **stable accessible
  name** (for example, "Mute"). When the label instead names the changing
  action ("Mark online" / "Mark offline"), use a normal action button without
  `aria-pressed`. The native demonstration uses action-button semantics.

### Declarative Shadow DOM and progressive enhancement

Server rendering can supply `<template shadowrootmode="open">` inside
the custom-element host. When the browser creates that root, an upgrading
element must **reuse** the existing `shadowRoot` and its child nodes.
Calling `attachShadow({ mode: "open" })` again on a declarative root
can **clear the rendered server content**, even when it does not throw.
The [SSR example](https://github.com/dporkka/syntyr-css/blob/main/examples/web-components/ssr.html) verifies this
behavior in browser tests.

For an essential workflow, either provide meaningful static content
that is valid without JavaScript or provide an independent native form/link
fallback. Server-rendered text must match the initial attributes/state.
A JavaScript-only action rendered into Declarative Shadow DOM should begin
**disabled** and be enabled only after its event listener is installed, so a
failed module load does not leave a misleading, apparently working control.
Only rewrite a live region when its announced message actually changes,
not when unrelated attributes (such as a heading) change.
Do not claim that a JavaScript-only toggle provides a no-script mutation path.

### Custom state and form association (optional application concerns)

Prefer the built-in state/ARIA vocabulary when it already expresses the behavior.
For **internal-only**, CSS-observable boolean state, custom elements can use
`this.attachInternals().states.add("loading")` and style with
`:host(:state(loading))`. This avoids a redundant public attribute; it does
**not** replace `aria-busy`, `disabled`, or other accessibility semantics.
Use `ElementInternals` only for a concrete need; it is not required for
ordinary Syntyr components or presentation.

A truly custom, form-participating element must declare
`static formAssociated = true`, acquire `ElementInternals` using
`attachInternals()`, and call `setFormValue()` as its value changes.
If it supports validation, use `setValidity()` and expose accessible
labels, error text, and focus. Implement applicable
`formResetCallback()`, `formDisabledCallback()`, and
`formStateRestoreCallback()` lifecycle behavior. Test actual
`FormData`, reset, disabled fieldsets, and native validation in browsers.
**Ordinary `input`, `select`, `textarea`, and `button` should
remain the default**; Syntyr does not ship a custom form-control runtime.

The [form-associated integration fixture](https://github.com/dporkka/syntyr-css/blob/main/examples/web-components/form-associated.html)
demonstrates a justified narrow use case: two native inputs treated as a
single form-associated *range* with cross-field validity and a two-entry
`FormData` submission. With JavaScript disabled, the original named fields
remain usable. The enhancement removes those native `name` attributes so
`setFormValue(FormData, state)` remains the sole submission source. Test
`form.reset()`, ancestor `fieldset disabled`, direct host `disabled`,
`FormData` cardinality, restoration, reconnection and validation across
browsers. Server-side validation remains mandatory; this example is **not**
a distributed Syntyr component or a reason to replace ordinary controls.

References: [Custom elements](https://developer.mozilla.org/en-US/docs/Web/API/Web_components/Using_custom_elements),
[ElementInternals](https://developer.mozilla.org/en-US/docs/Web/API/ElementInternals),
[Declarative Shadow DOM](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/template#declarative_shadow_dom).

## Suggested review checklist

- Has an HTML-only fallback when the workflow requires it
- Does not require a particular frontend framework for presentation
- Documents all public tokens, attributes, and emitted custom events
- Works in nested Studio/Grid/Noir themes and a narrow embedded host
- Does not restyle the document outside `.syn-root`
- Maintains accessible state when disabled or busy
- Handles text content safely without raw-HTML interpolation
- Passes cross-engine tests and manual assistive-technology review

## Example boundaries

The optional [Syntyr + Lit sample](https://github.com/dporkka/syntyr-css/tree/main/examples/lit) provides
light-DOM class styling and Shadow DOM token + `::part()` styling. It
demonstrates a `CustomEvent` contract but uses only local demonstration
state. It is not a proposed production widget API.

For stable CSS selector/token guarantees see [API stability](api-stability.md).
For native HTML fallbacks see
[progressive enhancement](progressive-enhancement.md).
