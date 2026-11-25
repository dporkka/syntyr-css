# Syntyr CSS: AI-agent quickstart

Use this guide when creating an application **with** Syntyr. To modify Syntyr itself, also read the repository [AGENTS.md](https://github.com/dporkka/syntyr-css/blob/main/AGENTS.md). Syntyr supplies styles, **not** application logic or a JavaScript component system.

## 1. Choose the correct version

| Version | Status | Themes | Notes |
| --- | --- | --- | --- |
| `0.3.0-alpha.4` | Published immutable release | `grid`, `noir`, `studio` | Safe to pin for examples below |
| `0.3.0-alpha.5` | Unreleased source candidate | Seven themes including `industrial`, `terminal`, `corporate`, `minimal` | Do not cite as a downloadable tagged release |

For a production application, copy a tagged CSS release to your own origin and pin its version. The CDN URL below is suitable for an initial prototype:

```html
<link rel="stylesheet" href="https://syntyr-css.pages.dev/v/0.3.0-alpha.4/syntyr.core.css">
```

For page-level recipes, load the same **version** of the optional module after core:

```html
<link rel="stylesheet" href="https://syntyr-css.pages.dev/v/0.3.0-alpha.4/syntyr.core.css">
<link rel="stylesheet" href="https://syntyr-css.pages.dev/v/0.3.0-alpha.4/syntyr.recipes.css">
```

Do not combine `syntyr.all.css` with individual CSS modules; that loads duplicates. A stylesheet is not automatically installed by adding a `syn-*` class to markup.

### One-file semantic HTML (unreleased source only)

If testing alpha.5 from a local source checkout, `syntyr.semantic-bundle.css` includes both core and optional semantic rules. Do **not** point a production page at a nonexistent alpha.5 CDN release URL.

```html
<link rel="stylesheet" href="/css/syntyr.semantic-bundle.css">
<main class="syn-root syn-semantic" data-syn-theme="studio">
  <article><h1>Settings</h1><button type="button">Save</button></article>
</main>
```

Use `.syn-root` and `.syn-semantic` together; the bundle does not globally restyle arbitrary host HTML. Never load it alongside `core.css` or `semantic.css`, which would duplicate CSS. [Complete source demo](../examples/semantic-starter.html).

### Find a matching source example (unreleased candidate only)

For work against a verified alpha.5 **source checkout**, read the local
`metadata/component-gallery.v1.json` instead of inventing classes:
filter `examples[]` by `use_cases` (for example `saas-dashboard` or
`forms-workflow`), then verify `required_stylesheets` against what is
actually installed. Each example includes `html`, `catalog_url`,
`playground_url`, and `native_feature_requirements`; browser caveats
are in `native_browser_features`. The
[editor integration guide](editor-integration.md#select-html-examples-by-task-and-installed-css)
provides a standard-library Python selection example. Tags are
recommendations, not evidence of complete behavior or a compatibility
certificate. Do not copy unreleased examples into an alpha.4 application
without checking that the classes and files exist in that release.

## 2. Generate valid HTML

```html
<main class="syn-root syn-page" data-syn-theme="studio">
  <div class="syn-shell">
    <header class="syn-header">
      <a href="/" class="syn-logo">Acme</a>
      <nav aria-label="Primary navigation"><a href="/reports">Reports</a></nav>
    </header>
    <section class="syn-panel" aria-labelledby="reports-title">
      <h1 class="syn-heading" id="reports-title">Reports</h1>
      <p class="syn-muted">View recent activity.</p>
      <a class="syn-button syn-button--primary" href="/reports/new">New report</a>
    </section>
  </div>
</main>
```

All classes in this sample are available from published alpha.4 core. Use an `<a>` for navigation, a `<button>` for an action, and functional `href`/`action` values rather than dummy `#` placeholders.

## 3. Use responsive recipes only when their module is loaded

```html
<section class="syn-root syn-region" data-syn-theme="studio" aria-label="Operations overview">
  <div class="syn-stats">
    <article class="syn-stat">
      <p class="syn-stat-label">Open tickets</p>
      <p class="syn-stat-value">14</p>
    </article>
    <article class="syn-stat">
      <p class="syn-stat-label">Resolved today</p>
      <p class="syn-stat-value">8</p>
    </article>
  </div>
</section>
```

`syn-region` and `syn-stats` are core classes; they use native container queries. The containing region must be an ancestor of the responsive pattern. For application shells, `syn-app-shell` is in **recipes**, not core.

## 4. Optional scoped semantic mode

Load `syntyr.semantic.css` **after core**, then opt into `syn-semantic` in a `syn-root` subtree. Ordinary HTML outside that subtree is unaffected.

```html
<section class="syn-root syn-semantic" data-syn-theme="noir">
  <form action="/login" method="post">
    <label for="email">Email <input id="email" name="email" type="email" required></label>
    <button type="submit">Sign in</button>
  </form>
</section>
```

The form must have a real server handler. Syntyr does not provide authentication, CSRF protection, requests or validation logic.

## 5. Framework rules and accessibility

- **React/JSX:** use `className`, `htmlFor`, and normal framework event handlers. Syntyr styles HTML but does not expose React components.
- **HTMX/Datastar:** let the host library manage state and requests; preserve native form behavior. For transient class-changing elements inside semantic mode, see the [framework integration guide](framework-integrations.md) for `data-syn-semantic`.
- **Themes:** `data-syn-theme` belongs on `.syn-root` or a nested themed subtree. Prefer `studio` for professional SaaS, `grid`/`noir` for cinematic interfaces.
- **Accessibility:** preserve keyboard focus, form labels, descriptive error messages, link destinations and reduced-motion preferences. `aria-pressed` describes an actual pressed toggle; `aria-busy` alone does not perform loading.
- **Visualization:** `syntyr.viz.css` styles provided SVG and HTML. It **does not calculate chart geometry** or provide a renderer.
- **Custom theme:** override documented `--syn-*` variables in application CSS. Verify text/background and interactive contrast.

## 6. Verify generated output

1. Identify the installed Syntyr **version** and CSS modules.
2. Check every `syn-*` class against [components](components.md), [recipes](recipes.md), or the [validated curated manifest](../metadata/components.json).
3. Ensure the browser actually loads each required stylesheet, without duplicates.
4. Check interactive elements, keyboard navigation, high-zoom reflow and browser console.
5. Do not claim a static Syntyr example implements fetching, persistence, sorting, filtering or authentication.

See [agent integration](agent-integration.md) for reusable prompt instructions.
