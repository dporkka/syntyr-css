# Optional framework-neutral copy interaction

Syntyr's copy interaction is **one opt-in native ESM module**, independent of
React, HTMX, Vue, Svelte, Tailwind and the CSS core. It uses the browser
Clipboard API; **no third-party dependencies, global listeners, auto-init,
legacy `execCommand`, or clipboard write on import**.

[Try the runnable demonstration](../examples/copy.html). The MIT CSS remains
fully usable without JavaScript. Only import this module for a real copy action.

## Plain HTML

```html
<link rel="stylesheet" href="/css/syntyr.core.css">
<style>[data-syn-copy-target][hidden] { display: none; }</style>
<section class="syn-root">
  <pre><code id="install-command">npm install @syntyr/css</code></pre>
  <button class="syn-button" type="button" hidden
          data-syn-copy-target="install-command"
          data-syn-copy-status="copy-result">Copy command</button>
  <p id="copy-result" role="status" aria-live="polite"></p>
</section>
<script type="module" src="/js/enable-copy.js"></script>
```

```js
// enable-copy.js (only when the optional module is explicitly imported)
// Copy dist/syntyr.copy.mjs to /js/syntyr.copy.mjs on your site.
import { enhanceCopyButtons } from '/js/syntyr.copy.mjs';
const detach = enhanceCopyButtons();
// In an SPA teardown or component unmount: detach().
```

For applications with a bundler, the same module is exported from the npm
package (once the release containing the optional module is published):

```js
import { enhanceCopyButtons } from '@syntyr/css/copy';
```

Copy buttons should start with `hidden` and the scoped guard above so older
component CSS cannot accidentally override the browser's hidden state. A blocked script or missing Clipboard
API never leaves a misleading, active copy button. The underlying content
remains readable and manually selectable. JavaScript only reveals valid
controls on secure contexts where `navigator.clipboard.writeText` is available.
Web browsers may still reject clipboard access: the module announces
failure without falsely claiming a successful copy.

Use an adjacent `role="status"` element for feedback **outside** the button.
The target is resolved by ID at click time, so a host can replace the contents
without copying stale values. `<input>` and `<textarea>` use their current
`value`; other elements use `textContent`, never `innerHTML`.
Keep copy sources and status targets in the **same document**.

## Framework and server integrations

In HTMX, call `enhanceCopyButtons(fragment)` after a swap and call its
returned cleanup function when you remove that fragment. In React or Vue,
call it in the component's mount lifecycle and detach on unmount.
It is idempotent on the same button: repeated calls cannot stack listeners.
The module does not observe mutations or own framework lifecycle.

For any clipboard action involving sensitive data, the host app must control
which content can be rendered and copied. This is presentation behavior, not
an authorization or data-fetching layer.

## Distribution and compatibility

Use `@syntyr/css/copy` only with a release that includes this optional export;
for source/checkouts use `dist/syntyr.copy.mjs`. The experimental alpha.5
candidate is **not** a claim of an already-published package update.
A HTTPS or localhost context is generally required for the Clipboard API.
Syntyr's base CSS and package default entrypoint import no JavaScript.
Browser support, CSP and user-activation behavior remain host concerns.
