## Unreleased — v0.3.0-alpha.5 candidate

- Keep classless native file inputs within 320px semantic fieldsets by using a shrinkable CSS Grid track and wrapping the native file-picker button; add cross-browser and enlarged-text reflow regression coverage.

- Make the PR progressive-enhancement browser gate independent of PyPI access by
  reusing the existing locked Node Playwright test infrastructure and the real
  Python stdlib HTTP fixture. All three browser engines still run with
  application JavaScript disabled; published CSS remains JS-free.

- Add five native interaction recipes (exclusive `details[name]` accordion, GET `search` form, modal `dialog` choice, `datalist` suggestions, and `meter`/`output`) to the standard copyable catalog, static example, and documentation without a JS runtime or new CSS component classes.
- Constrain classed dialogs and popovers to the physical viewport width/height (including anchored popovers), reserving the corner popover inset and margin even on very short viewports, with scrollable overflow for enlarged text and vertical writing modes; add script-disabled Chromium/Firefox keyboard and forced-colors regression checks.

- Improve opt-in semantic HTML: classless native form composition, accessible disclosure targets and captioned tables; restrict `aria-selected` row styling to real grid/treegrid roles, with `data-syn-state` for static visual selection.
- Add an optional stdlib `syntyr_check.py --semantic` lint pass, and extend the one-file zero-JS semantic starter with navigation and a named data table. Default lint behavior and published alpha.4 remain unchanged.

- Change classed data table cells to wrap prose by default; apply `.syn-cell--nowrap` for codes and identifiers, while `.syn-cell--numeric` remains non-wrapping. **Prerelease layout change:** update existing tables that depend on implicit no-wrap.
- Support `--syn-panel-cut-fill` for cut-corner panels on nested or tinted surfaces. Add browser and palette-contrast regression checks.
- Ensure `.syn-flow` stacks inline siblings and fully suppress the horizon fade under increased-contrast preferences.
- Improve CSS-native usability with balanced short headings, configurable vertical flow composition, semantic raised/overlay elevation, and entrance motion tokens; no runtime dependencies.
- Preserve primary-button hover contrast by default with a configurable hover background and contrasting border instead of unconditional color lightening.
- Respect `prefers-contrast: more` for nested themed and cinematic-intensity regions; remove forced WebKit font smoothing and extend native CSS browser regressions.


- Add opt-in system light/dark palette selection, composed from the existing Studio and Grid tokens without JavaScript.
- Add opt-in intrinsic Sidebar/Switcher layouts and fluid typography in recipes; improve native checkbox/radio label alignment in semantic mode.
- Publish a standalone minimalist HTML example and source/browser regression checks. No new CSS distribution or runtime dependency.

- Add four original opt-in palettes (Industrial, Terminal, Corporate and Minimal) for seven interchangeable SYNTYR themes.
- Add a standalone finite CSS-only utilities module and an MIT-licensed seven-theme comparison gallery.
- Validate nested theme foreground, native color-scheme and geometry inheritance, utility precedence, and keyboard/forced-colors presentation.
- Preserve the SYNTYR-only syn- API and published alpha.4 release. No compatibility selectors or files are reintroduced.

## v0.3.0-alpha.4 (2026-11-14)

- Standardize all project naming, CSS selectors and tokens on SYNTYR.
- Publish only `syntyr.*.css` modules and use the `syn-` namespace for
  classes, CSS variables, layers, theme and state data attributes.
- Remove obsolete CSS aliases, migration notes and historical naming drafts.
- No JavaScript or extra dependencies; commercial trademark clearance pending.

## v0.3.0-alpha.3 (2026-11-14)

- Rebrand the public project as **SYNTYR**, previously Syntyr CSS.
- Add new `syntyr.*.css` distribution paths and documented the updated interface styling API.
- Update website, documentation, downloadable archives, CLI copy and code examples.
- Record trademark-clearance caveats; premium launch remains gated.

## Unreleased

- Add a complete, static MIT SaaS workflow demonstration with search and filter form, responsive record table, linked pagination, preferences disclosures, skeletons and empty states. All backend actions are explicitly illustrative; core CSS and runtime JS remain unchanged.
- Publish the workflow demo and scoped example stylesheet in the Cloudflare site allowlist and gallery, with source and browser test contracts.

- Add original MIT-licensed semantic breadcrumbs, touch-sized pagination links and static skeleton loading placeholders to the core; preserve the CSS size budgets.
- Expand the component gallery and copy-paste recipes with real navigation, keyboard focus and accessible loading-state guidance.
- Add an optional, standalone JavaScript theme editor **for documentation only**: nested preview themes, color token overrides, contrast diagnostics and pasteable CSS; distributed CSS remains JavaScript-free.
- Add tests for new component contracts, internal documentation links and an isolated editor browser smoke suite; verify Chromium/Firefox gallery matrices and targeted WebKit gallery/editor smoke.
- Repair broken public documentation paths and remove obsolete legacy compatibility wording.

- Add an original MIT-licensed operations console example with responsive SaaS navigation, telemetry, capacity bars, deployment table, activity feed and terminal transcript; no runtime JavaScript.
- Add independent zero-runtime geometry CSS with five customizable frame treatments (bevel, notch, bracket, inset and circuit), including forced-colors fallbacks.
- Extend browser terminal recipes with static window chrome, command anatomy, output/readout colors and a non-blinking cursor.
- Remove CSS pointer-event suppression from ARIA-disabled buttons; applications enforce ARIA-disabled activation themselves.
- Add right-aligned tabular numeric cells and a free HTML geometry/terminal demo plus multi-browser regression checks.
- Preserve the existing explicit table emphasis API, core gzip budget and deterministic ZIP distribution.
- Address review findings: disabled hover/cursor semantics, inherited geometry tokens and the tracked standalone CSS release artifact.
- Fix 320px/2x text reflow by making stack tracks shrinkable and allowing long technical captions to wrap.
- Verify the frame-and-terminal gallery across Chromium, Firefox and WebKit; maintain a CSS-first implementation without requiring runtime JavaScript.

- Add an original MIT CSS-only opt-in Vertigo admin skin and standalone HTML preview; keep the existing Vertigo application unmodified.
- Build a separate Hugo v0.170.0 docs proof from canonical Markdown using filesystem mounts, with reproducible output/link checks.
- Document the Hugo versus Zola tradeoff; do not migrate the live GitHub Pages site yet.

## v0.3.0-alpha.2 (2026-11-14)

- Fix narrow and enlarged-text horizontal overflow in layouts, buttons, panels, badges and long headings.
- Add browser reflow regression suite and keep the MIT core free of runtime JavaScript.
- Add voluntary developer feedback calls and document preliminary Syntyr name-risk review.

- Verified WebKit in the official pinned Playwright Python container: 6 pages × 3 viewports; 54 checks total across Chromium/Firefox/WebKit.
- Documented zoom-test limitations and manual screen-reader follow-up.
- Prepared a ten-interview design-partner pilot without claiming buyer commitments.

- Add a free original Noir resource-index screen and theme-customization guide.
- Publish an honest $59 Console Kit concept and feedback entry point without taking payment.
- Fix duplicate gallery meta description and invalid ARIA on palette swatches; add browser-matrix and optional axe-core verification scripts.
- Add professional light Studio theme alongside existing Grid and Noir.
- Add separate, opt-in CSS recipes for SaaS application shells, business pages and browser terminals.
- Export ANSI 16-color palettes and a stdlib Python CLI example for native terminal apps (CSS itself cannot style terminals).
- Add original MIT demo pages for SaaS, business and terminal contexts, and explicit table status styling.
- Add optional static horizon/atmosphere effects and enhance the Grid/Noir demos without continuous animation.
- Fix nested Studio foreground inheritance, CLI ANSI contrast and Windows VT detection; expand browser and axe page coverage.
- Enlarge the documentation guide link target following an axe-core WCAG 2.2 automated finding.
- Give labeled telemetry and dashboard-preview groups explicit ARIA group semantics.
- Retain zero runtime JavaScript, CSS bundle budgets and semantic HTML contracts.

## v0.3.0-alpha.1 (2026-11-14)

- Publish static showcase and component gallery via GitHub Pages, without adding a runtime build toolchain.
- Add a prominent gallery link, copy-paste installation panel, and documentation links.
- Add a reproducible versioned CSS release ZIP and local static-link tests.
- Preserve MIT licensing, zero runtime JS, and separate future premium templates.

# Changelog

## v0.3-alpha — 2026-11-14

- CSS-native, framework-independent container query patterns for stats, split layouts, pricing and empty states.
- ARIA/data attribute button state styling and additional motion and status tokens.
- Original MIT-licensed Noir pricing page and copy-paste recipe documentation.
- Research notes distinguishing useful Tailwind CSS v4 engineering concepts from proprietary Tailwind Plus source and APIs.
- Proposed separately authored premium Console Kit specification; nothing in the core is commercially restricted.
- Regression checks for container-query layouts, responsive pricing, CSS host overrides, native controls and visual screenshots.

## v0.2-alpha

- Modular core, semantic and optional effects bundles; independent embedded root and page root.
- Free dashboard and landing examples; accessible focus and form states; deterministic dependency-free build.

## v0.1

- Initial Grid/Noir themed CSS and native HTML component gallery.
