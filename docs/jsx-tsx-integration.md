# JSX and TSX without framework lock-in

**Status:** Source-only alpha.5 integration guide. The optional CSS npm package
(`@syntyr/css`) is **not yet published**. These examples use local `file:`
package references; do not assume the package name is available on npm.

Syntyr's public contract is **CSS**, not a JSX component API. React, Preact,
Solid and plain HTML can render the **same** `.syn-root`, `syn-*` classes,
`--syn-*` tokens and `data-syn-*` attributes without a Syntyr runtime,
provider, compiler plugin, generated types or duplicated CSS implementations.
The experimental `@syntyr/react` package is optional, not required.

## Copy-owned patterns

Import the CSS exactly **once** in the application's entry point (Vite) or
root layout (Next.js App Router):

```tsx
import "@syntyr/css/core.css";
```

If using a copied CSS file instead of the unpublished npm package, replace
this import with the correct local stylesheet path. Keep a stable `.syn-root`
above the content and place all theme attributes on it or on a descendant.
Use ordinary DOM elements and native HTML semantics:

### React TSX (also works in Next.js Server Components)

```tsx
export function ProjectSearch() {
  return (
    <main className="syn-root" data-syn-theme="studio">
      <form className="syn-panel" action="/projects" method="get">
        <label className="syn-label" htmlFor="project">Project</label>
        <input className="syn-input" id="project" name="project" required />
        <button className="syn-button syn-button--primary" type="submit">
          Search
        </button>
      </form>
    </main>
  );
}
```

No `"use client"` is needed here: standard form submission works without
hydration. Add a client component only when adding React event handlers or
other client-side interactivity. For a working React TSX counter, see
[`NativeRecipe.tsx`](../examples/react-vite/src/NativeRecipe.tsx), used in
[`App.tsx`](../examples/react-vite/src/App.tsx). It uses no React adapter.

### Preact JSX

```jsx
export function ProjectSearch() {
  return (
    <main class="syn-root" data-syn-theme="studio">
      <form class="syn-panel" action="/projects" method="get">
        <label class="syn-label" for="project">Project</label>
        <input class="syn-input" id="project" name="project" required />
        <button class="syn-button syn-button--primary" type="submit">Search</button>
      </form>
    </main>
  );
}
```

A Preact/Vite project can use `esbuild: { jsx: "automatic", jsxImportSource:
"preact" }`, as in [`examples/preact-jsx`](../examples/preact-jsx/).
There is no need for `preact/compat` or React-specific wrappers just to use CSS.

### Solid TSX

```tsx
export function ProjectSearch() {
  return (
    <main class="syn-root" data-syn-theme="studio">
      <form class="syn-panel" action="/projects" method="get">
        <label class="syn-label" for="project">Project</label>
        <input class="syn-input" id="project" name="project" required />
        <button class="syn-button syn-button--primary" type="submit">Search</button>
      </form>
    </main>
  );
}
```

Solid uses `jsx: "preserve"` and `jsxImportSource: "solid-js"`, alongside
`vite-plugin-solid` in the Vite build. See
[`examples/solid-tsx`](../examples/solid-tsx/). Solid's signals and event
handlers are Solid's responsibility, not Syntyr's.

## Attribute and accessibility conventions

| Purpose | React JSX/TSX | Preact JSX / Solid TSX |
| --- | --- | --- |
| CSS classes | `className="syn-button"` | `class="syn-button"` |
| Form label | `htmlFor="project"` | `for="project"` |
| Theme / density | `data-syn-theme`, `data-syn-density` | Same |
| Disabled / required | Native DOM attributes | Same |
| Accessibility state | `aria-*`, HTML semantics | Same |

Prefer native `<button>`, `<form>`, `<label>`, `<input>` and `<dialog>` to
custom widgets when possible. A Syntyr CSS class cannot provide keyboard
interaction, focus management, filtering or ARIA behavior on its own.
Use your framework's headless behavioral library for complex widgets. Avoid
passing component-only props such as `variant="primary"` to native HTML
buttons; use `className`/`class` or `data-*` selectors explicitly instead.
Keep server and client theme attributes identical to avoid hydration mismatch.

## Real build and browser checks

From this repository root, with Node.js 20.9+ and npm:

```sh
python3 scripts/test_js_adoption.py --install
```

This builds the optional React wrapper, React/Vite TSX, **Preact JSX**,
**Solid TSX** (including strict TypeScript checking), Next.js App Router and
Express fixtures. Subsequent runs can omit `--install`. The independent
Woodpecker `js-adoption` lane runs the equivalent production builds without
adding Node to the CSS core's standard Python-only quality gate.

The optional real Chromium browser smoke also covers React, Preact, Solid and
Next.js, checking rendered CSS, native buttons, client interaction, mobile
layout and JavaScript/console errors. Follow the setup in
[the Node/React/Next guide](node-react-next-integration.md) and run:

```sh
python3 tests/js_adoption_browser.py
```

Next.js provides SSR/client-island coverage; the Preact and Solid fixtures
are **client-rendered** build/browser checks, not claims of SSR verification.
Browser/screen-reader accessibility review remains separate.
