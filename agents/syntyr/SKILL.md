---
name: syntyr
description: Build accessible, semantic HTML interfaces using verified, version-pinned Syntyr CSS classes and themes; never invent a JavaScript component API.
---

# Syntyr CSS consumer skill

Use when creating, redesigning, or maintaining an interface **with Syntyr CSS**.
This Skill is portable: it also works when copied into a consumer project. No
Syntyr server, JavaScript runtime, npm installation, or network access is required.

## Discover the installed contract first

1. If the Syntyr source checkout is available, run `python3 scripts/syntyr_agent.py info --project /path/to/app --json` first. Its read-only JSON reports verified asset hashes, release status, installed stylesheet filenames, themes and agent reference paths. Exit 0 means healthy, 1 means invalid/degraded and 2 means unconfigured. It does **not** verify that the host actually loads the CSS.
   Otherwise, if the project contains `syntyr.agent.json`, read it before generating markup. `release` is the explicit CSS version; `assets_dir` is the local CSS location; `stylesheets` is the list installed by the optional offline setup tool.
2. Read `references/api.json` next to this Skill if it exists. Its `classes`
   and curated `components` are verified against that version, not the latest
   unreleased source. The `themes` list is also version-specific.
3. Without either local file, **do not assume** the latest source candidate is
   installed. Determine the real CSS assets/imports first. The published immutable
   `0.3.0-alpha.4` supports `studio`, `grid`, `noir`; `0.3.0-alpha.5` is an
   *unreleased source candidate* and has additional APIs.
4. For detailed public guidance, consult the [AI quickstart](https://syntyr-css.pages.dev/docs/ai-quickstart.md),
   [component guide](https://syntyr-css.pages.dev/docs/components.md),
   [composition recipes](https://syntyr-css.pages.dev/docs/recipes.md) and
   [LLM documentation index](https://syntyr-css.pages.dev/llms.txt).
   Public docs may describe newer source-only APIs: always prefer the local
   version-pinned contract over an unpinned website example.

## Generate semantic, working application markup

- Scope styles inside `.syn-root`; set `data-syn-theme` to a theme in the
  installed contract. Default to `studio` for professional SaaS applications.
- Use only selectors supported by the **installed** release and stylesheet.
  If necessary, add clearly identified application CSS instead of inventing
  `syn-*` classes. Syntyr's optional stylesheet modules must be loaded before
  their classes can style anything. Never duplicate `syntyr.all.css` with modules.
- Prefer native HTML semantics: `<a href>` for navigation, `<button>` for
  actions, explicitly associated labels, accurate ARIA, real form handlers,
  visible focus and responsive layouts. Avoid placeholder interactions.
- In React use `className` and `htmlFor`; in HTMX/Datastar/server templates
  retain functional URLs and server behavior. Syntyr supplies CSS styling,
  not React components, authentication, sorting, data fetching, state
  management, chart geometry, or keyboard interaction logic for comboboxes.
- Use an appropriate behavioral library for advanced interactions. Verify
  keyboard operation, reflow, focus, and contrast in a browser.

## Verify before reporting success

If the Syntyr source checkout is available, run:

```sh
python3 scripts/syntyr_agent.py check --project /path/to/project --json path/to/page.html
```

The optional checker verifies pinned CSS integrity and **literal `.html`**
selectors and state values. Exit code 1 means errors; 2 means validation is
incomplete (such as JSX/TSX), not success. Without the source checkout, use
`references/api.json` and the actual installed CSS to verify selectors.
React/Vue/Svelte and dynamic templates require framework-aware lint and real
browser testing; no static Syntyr checker certifies WCAG compliance.
