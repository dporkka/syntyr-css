# Moving from Pico.css to Syntyr

**Syntyr is not a drop-in Pico replacement.** Both can style native HTML without
browser JavaScript, but they deliberately use different scoping, tokens and APIs.
Choose Syntyr for a scoped semantic mode that can grow into more elaborate SaaS
interfaces. Keep Pico (or use a compatible continuation) if globally classless
markup or exact Pico token compatibility is more important.

## Try a plain HTML page

In the **unreleased alpha.5 source candidate**, copy
`dist/syntyr.semantic-bundle.css` into your application's public CSS directory:

```html
<link rel="stylesheet" href="/css/syntyr.semantic-bundle.css">
<body class="syn-root syn-page syn-semantic" data-syn-theme="studio">
  <main class="syn-shell">
    <article>
      <h1>Project settings</h1>
      <form action="/settings" method="post">
        <label for="title">Title <input id="title" name="title" required></label>
        <button type="submit">Save settings</button>
      </form>
    </article>
  </main>
</body>
```

The `/settings` action above is illustrative: your application must implement
its own backend, CSRF handling and persistence. For a fully static, runnable
example, see [the single-file starter](../examples/semantic-starter.html).

The current **published alpha.4** does not include the one-file semantic bundle.
For alpha.4, load `syntyr.core.css` followed by `syntyr.semantic.css` instead.
Do not combine either of those with the new one-file bundle: this duplicates CSS.

## Key differences

| Concern | Pico-style usage | Syntyr usage |
| --- | --- | --- |
| Native HTML | Unclassed elements typically styled page-wide | `.syn-semantic` opt-in inside `.syn-root` |
| Page width | Conventional global container styles | `.syn-shell` on your layout container |
| Components | Small semantic-oriented API | Explicit `syn-*` classes when more control is needed |
| Themes | Pico's theme and palette variables | `data-syn-theme` and documented `--syn-*` tokens |
| Existing application CSS | Global rules can overlap | Scoped Syntyr selectors; check host/global resets |
| Interactions | HTML and application JavaScript | Native HTML and application JavaScript; no Syntyr widget runtime |

### Migration sequence

1. Choose a **small page or region**. Remove Pico's global stylesheet from
   that page where feasible, or carefully isolate the two frameworks.
2. Load the pinned Syntyr stylesheet and opt into `.syn-root.syn-semantic`.
   Without these classes, no Syntyr semantic styling is applied.
3. Keep real form labels, methods, actions, buttons, table headers, `details`
   and other native elements. Classless `form` and `fieldset` gain useful
   vertical layout in semantic mode; use `.syn-form` for the explicit class API.
   Add `.syn-shell` where a page-width constraint is useful.
4. Translate existing `--pico-*` customizations **by design role**, not by
   search-and-replace. Syntyr's `--syn-*` tokens are not one-to-one aliases.
5. If HTMX or another library adds temporary classes to formerly unclassed
   elements, prefer explicit `syn-*` component classes on published alpha.4.
   The `data-syn-semantic` marker is an **alpha.5-only** selector enhancement
   for retaining semantic styling through transient class changes; do not use
   it as an alpha.4 compatibility guarantee.
6. Run the optional `python3 scripts/syntyr_check.py --semantic your-page.html`
   checker on literal HTML to catch labeling, reference and table-state mistakes.
   Dynamic templates still need rendered-page checks.
7. Test keyboard navigation, light/dark behavior, small screens, 200%/400%
   browser zoom, forced colors, and screen readers in the actual application.

## When not to migrate

Do not switch solely because Syntyr's stylesheet is small or has no JavaScript:
Pico, Tailwind-generated CSS, and other alternatives may have similarly low
browser runtime overhead. Syntyr's alpha status, unverified manual accessibility
gates, and different public API carry real migration costs. No measured
cross-framework performance advantage has been established.

See [distribution](distribution.md), [component contract](components.md),
[framework integrations](framework-integrations.md), and
[performance validation](performance-validation.md).
