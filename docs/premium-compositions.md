# Premium compositions: restrained SaaS, command UI, and product storytelling

Syntyr borrows *design principles*, not layouts or proprietary assets, from polished developer tools. The Syntyr implementations are original MIT-licensed, **opt-in CSS-only recipes**. Load `syntyr.core.css` first and then `syntyr.recipes.css`:

```html
<link rel="stylesheet" href="/css/syntyr.core.css">
<link rel="stylesheet" href="/css/syntyr.recipes.css">
```

[View the working HTML example](../examples/premium-compositions.html) (illustrative data; no live services). No new runtime package, JavaScript, web font, icon set, or theme is required.

## 1. Depth roles — use the least emphasis that works

| Class | Semantic purpose | Tokenized treatment |
| --- | --- | --- |
| `.syn-surface--recessed` | Background well, sidebar, filter region | `--syn-surface-recessed` and subtle border |
| Existing `.syn-panel` / `.syn-app-card` | Ordinary content | `--syn-surface` |
| `.syn-surface--raised` | Inspector, important contextual card | `--syn-surface-raised` and `--syn-shadow-raised` |
| `.syn-surface--floating` | Opt-in floating surface, non-native overlay presentation | `--syn-surface-floating`, `--syn-border-floating`, and `--syn-shadow-overlay` |

All surface tokens recompute in nested `data-syn-theme` contexts; they do not hardcode individual brand colors. Floating is *not* position: fixed and does not create an actual overlay or dialog. Use HTML `<dialog>` or `popover` where corresponding browser behavior is needed. Avoid combining multiple `syn-surface--*` depth classes on the same element.

## 2. Page anatomy and detail inspector

```html
<section class="syn-root" data-syn-theme="studio">
  <header class="syn-page-header">
    <div><h1>Incident detail</h1><p>Application-generated status</p></div>
    <div class="syn-page-header__actions"><a href="/incidents">All incidents</a></div>
  </header>
  <div class="syn-detail-layout">
    <section class="syn-detail-main">Incident analysis and tables</section>
    <aside class="syn-detail-aside syn-surface--raised" aria-label="Incident metadata">
      Status, owner and relevant links
    </aside>
  </div>
</section>
```

Use `.syn-page-header__meta` to group quiet metadata. The shell wraps with native flexbox rather than assuming the entire viewport width; it remains useful inside an already constrained application region. Follow normal HTML landmark rules: one main landmark per page, not nested main landmarks in a page that already has a `<main>`. Replace the inner `<main>` in this standalone snippet with a `<section>` if integrating inside an existing main.

## 3. Search and command presentation (Raycast-inspired restraint)

A [working, progressively enhanced command launcher](../examples/command-launcher.html)
reuses these classes without introducing a second visual API. It offers real
destination links as a **no-JavaScript fallback**; a small, copy-owned optional
module activates a native `dialog`, Ctrl/⌘ + K, safe text filtering and Escape
dismissal. This is **navigation**, not a general action executor or ARIA
combobox: keyboard users Tab through real links. Host applications must own
authorization, remote search, and mutations. No required Syntyr runtime is added.

`.syn-command-panel`, `.syn-command-group`, `.syn-command-group-label`, `.syn-command-row`, `.syn-command-key`, and `.syn-command-description` are strictly visual.

Use a real `<search>` containing a labeled native GET form for search that works without JavaScript. Use real anchors for navigable destinations, and `<kbd>` for *informational* keyboard shortcut labels. The CSS deliberately does **not** register keyboard shortcuts, implement arrow navigation, filter results, or claim focus trapping. Shortcut activation, a live command index, aria-activedescendant/listbox navigation, dialog focus management, and authorization are **application** responsibilities.

If the application implements a custom keyboard-controlled command list, choose the correct ARIA semantics and provide mouse, touch, and keyboard input parity. Do not add `role="option"` or `aria-selected` to ordinary navigation links without implementing the matching listbox model. The recipe highlights `aria-current="true"` for a genuinely current destination link; it is not a substitute for actual selection state.

## 4. Activity timeline and marketing showcase

`<ol class="syn-activity-timeline">` with text and `<time datetime="...">` provides an ordered, screen-reader-readable event stream. The rail and circles are decorative. Treat severity/status with adjacent text rather than relying on marker color.

`.syn-showcase`, `.syn-showcase-copy`, and `.syn-showcase-visual` compose a marketing section using flex wrapping and native gradient paint. Supply your own text, semantic card markup and optional screenshot assets. Syntyr does not bundle fonts, photographs, animations, canvas or JavaScript effects.

## Progressive enhancement and accessibility

- Begin with semantic server-rendered HTML. A plain GET form and links are always usable; HTMX or application JavaScript may progressively enhance them.
- Keep keyboard focus styling visible, ensure accessible labels, and do not fake loading states or actual shortcut handling with CSS.
- Test screen readers, zoom/reflow at 200% and 400%, narrow containers, forced colors, nested light/dark themes, and `prefers-reduced-motion`.
- Never interpret CSS-selected rows as authorization, active search results, or live operational data; the application must supply those truths.
- Try `data-syn-intensity="quiet"` for production dashboards and reserve cinematic decoration for small promotional areas.
- Use `syn-*` namespaced classes and the existing tokens; avoid adding brand-specific lookalike themes or required external assets.

## Browser validation (developer-only)

Syntyr consumers do not need browsers, a JavaScript runtime, or an axe-core
dependency. Maintainers can run the optional Playwright regression test after
installing the browser engines in a separate development environment:

```sh
python3 tests/premium_compositions_browser.py \
  --browsers chromium firefox webkit \
  --axe-file /path/to/local/axe.min.js
```

The test covers the 320px, 390px and 1280px viewports, 200% text-size stress
at narrow widths, keyboard focus and skip-link navigation, focus outlines,
forced colors, reduced motion, and automated WCAG-tagged axe rules. At a
1280px desktop baseline, a 320px CSS viewport also tests the content width
available at 400% browser zoom (a reflow approximation, not a claim that a
browser zoom control was exercised). The repository's regular
`tests/reflow_test.py`, `tests/browser_matrix.py`, and
`tests/axe_audit.py` include this page as well.

**Manual checks remain essential:** use a real screen reader (such as NVDA,
VoiceOver or Orca), verify reading order and form labels, inspect actual
browser zoom and touch interaction, and confirm real data/permissions in the
consuming application. Axe-core cannot certify WCAG conformance on its own.
WebKit tests need its native system dependencies; a missing browser is
reported as blocked, never silently passed.

## Implementation provenance

The refinements borrow general ideas: precise information hierarchy (Linear), keyboard discoverability (Raycast), layered material roles (Vercel), useful operational metadata (Sentry), and restrained editorial presentation (Stripe and Resend). They do **not** reproduce any company's branded UI or assets.
