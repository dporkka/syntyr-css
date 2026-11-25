# Syntyr + Lit: optional Web Components interoperability

Syntyr is a **CSS-first design system**, not a Lit or Web Components runtime.
For a zero-framework example using native `HTMLElement` and Declarative Shadow DOM,
see the [native Custom Elements fixture](https://github.com/dporkka/syntyr-css/tree/main/examples/web-components).
The Lit integration below remains optional and independent.
The Syntyr core has **zero required JavaScript**, no Node.js install requirement,
and no dependency on Lit. A consumer application may independently choose Lit
to implement behavior. This guide demonstrates the integration using real
Lit 3 components in [the opt-in example](https://github.com/dporkka/syntyr-css/tree/main/examples/lit).

## Choose the correct styling boundary

### Light DOM: use Syntyr component classes directly

A Lit component can opt out of Shadow DOM by overriding `createRenderRoot()`
to return `this`. The markup is rendered into the regular document, so
Syntyr's selectors work **if the component is inside `.syn-root`**:

```js
import { LitElement, html } from "lit";

class ExampleStatus extends LitElement {
  createRenderRoot() { return this; }
  render() {
    return html`<article class="syn-panel">
      <p class="syn-status syn-status--success">Online</p>
    </article>`;
  }
}
customElements.define("example-status", ExampleStatus);
```

The application loads `syntyr.core.css` **once** at document level. Keep the
`.syn-root` ancestor outside frequently re-rendered/swap regions, and let the
host application own data fetching, state changes, authorization, and events.
Do not use light DOM if strict styling encapsulation is required. Styles from
the host application may also affect light-DOM content.

For progressive enhancement, include readable fallback HTML **inside** the
custom element. The included demo removes its `data-lit-fallback` child on
upgrade, before Lit renders, so the fallback is not duplicated. Without
JavaScript, the fallback remains readable. Native links and forms should work
without hydration for important tasks; do not rely on an interactive demo
toggle as an alternative to a real server action.

### Shadow DOM: inherit tokens, not selectors

Lit renders into Shadow DOM by default. Document-level
`.syn-panel` and `.syn-button` selectors **do not match inside a shadow root**.
In contrast, inherited CSS custom properties such as `--syn-text`,
`--syn-surface`, and `--syn-accent` can cross the shadow boundary.

Define internal styles using Lit's `static styles = css` and public tokens:

```js
import { LitElement, html, css } from "lit";

class ExampleSignal extends LitElement {
  static styles = css`
    :host { display: block; color: var(--syn-text, CanvasText); }
    [part="panel"] {
      background: var(--syn-surface, Canvas);
      border: 1px solid var(--syn-frame, CanvasText);
    }
    button:focus-visible {
      outline: 2px solid var(--syn-focus-ring, currentColor);
    }
  `;
  render() {
    return html`<section part="panel">
      <button part="toggle" type="button">Inspect</button>
    </section>`;
  }
}
customElements.define("example-signal", ExampleSignal);
```

The host application can customize explicitly exposed
`::part()` surfaces, e.g. `example-signal::part(panel) { border-style: dashed; }`.
`::part()` is not an automatic portal for all Syntyr selectors: it only styles
the named exposed part. `::slotted()` has its own limitations for styling
slot content. If you need actual Syntyr class rules inside Shadow DOM, you must
explicitly load styles **inside** that shadow root and provide an appropriate
`.syn-root` scope there; do not assume document CSS penetrates it.

Theme tokens inherit from the nearest Syntyr theme scope, including nested
`data-syn-theme` regions. Check contrast after overriding colors and do not
overwrite an end user's explicit theme with a component-local default.

## Reactive state, accessibility and custom event conventions

- Prefer native `disabled`, `required`, `checked`, `aria-pressed`,
  `aria-invalid`, and `aria-busy` semantics. A CSS class alone cannot implement
  disabled behavior or keyboard handling.
- Use Lit reactive properties for behavior, with standard HTML attributes as
  appropriate. Reflect only properties whose attributes are a useful public
  contract. Use `data-syn-*` for Syntyr-specific presentation state, not to
  reproduce native state.
- For a custom event that must leave a shadow root, dispatch
  `new CustomEvent("my-event", { detail: { ... }, bubbles: true, composed: true })`.
  Document `detail` and the event's meaning. Do not assume composed events
  automatically confer accessible semantics.
- Real interactive controls must be operable with keyboard and assistive
  technology; test focus, labeling, activation, reduced motion, forced colors,
  200%/400% zoom, and status announcements.
- Support progressive enhancement: ship meaningful server-rendered text or
  native link/form fallbacks when custom element upgrades fail. Lit SSR/hydration
  is a separate optional application concern, not a Syntyr dependency.
- Never interpolate untrusted user text as raw HTML. Lit's text interpolation is
  escaped by default; HTML sinks and application data fetching remain the
  consumer's security responsibility.

See also the [component-authoring contract](component-authoring.md) and
[framework integrations](framework-integrations.md).

## Framework interoperability: React 19 and HTMX

These examples verify **consumers**, not new Syntyr components or runtime APIs:

- [React 19 source](https://github.com/dporkka/syntyr-css/blob/main/examples/lit/react-interop.html): React owns its state
  and subscribes to the Lit element's native `syn-demo-status-change` custom event
  through `onsyn-demo-status-change`. No Syntyr React adapter is involved.
- [HTMX source](https://github.com/dporkka/syntyr-css/blob/main/examples/lit/htmx-interop.html): a native
  `<form action="./htmx-result.html" method="get">` navigates to a readable,
  static result document without JavaScript. With HTMX, the same response
  replaces the `#htmx-result` subtree. The `.syn-root` stays outside the swap,
  and the new Lit custom element upgrades without a Syntyr lifecycle hook.

Both demos use pinned, locally bundled dependencies after `npm ci`. They perform
no third-party runtime network fetches. The HTMX fixture is a **static GET
demonstration** rather than a persistence or authenticated backend; applications
must provide their own data fetching, CSRF protection for mutations, authorization
and server-side validation. Avoid swapping *inside* Lit-managed light DOM,
because Lit owns its rendered children; replace the custom-element host or an
application-owned ancestor instead. Keep custom event listeners on stable
ancestors when those hosts may be replaced. The React demo itself needs
JavaScript; it shows an explanatory fallback without JavaScript rather than
pretending to supply working React interaction.

If your application needs a composable UI component, prefer light DOM plus
native Syntyr classes. Choose Shadow DOM when encapsulation is necessary and
reuse inherited public tokens and explicit CSS parts—not a parallel token
registry. Do not ship an `@syntyr/lit` package without repeated production
requirements that cannot be met by these patterns.

## Run and test the example

```sh
cd examples/lit
npm ci
npm run build
cd ../..
python3 -m http.server 8765 --bind 127.0.0.1
# visit http://127.0.0.1:8765/examples/lit/index.html
# optional: /examples/lit/react-interop.html and /examples/lit/htmx-interop.html
```

This example has an isolated `package.json` and lockfile. The build creates
`examples/lit/dist/demo.js` locally (gitignored), **not** a distributable
Syntyr runtime file. The Cloudflare site does not publish this demo by default;
the source stays available in the repository.

After building the example, optionally run the browser interoperability checks:

```sh
cd examples/lit && npm test
```

Playwright and browser engines are developer-only test tools. This isolated
Node-based test runner avoids Python package downloads in CI. A skipped,
uninstalled, or broken engine must be reported as unavailable, not as passing.

## Lit references

- [Shadow DOM](https://lit.dev/docs/components/shadow-dom/)
- [Styles and CSS custom properties](https://lit.dev/docs/components/styles/)
- [Reactive properties](https://lit.dev/docs/components/properties/)
- [Events](https://lit.dev/docs/components/events/)
- [Rendering](https://lit.dev/docs/components/rendering/)

The example is an original integration demonstration, **not** a fork or
redistribution of the Lit source code.
