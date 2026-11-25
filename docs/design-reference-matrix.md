# Web design reference matrix and Syntyr benchmark applications

Research rubric for the **unreleased alpha.5 source candidate**, not a statement about the published alpha.4 package. Updated 2026-11-18. This matrix identifies what to *study*, not assets to redistribute. Design inspiration and design principles are not licenses.

For a browsable public catalog with descriptions and direct links, see the [Syntyr web design resources directory](design-resources.html). This matrix adds Syntyr-specific adoption criteria and reproducible benchmarks, rather than duplicating the directory.

## Ranked reference matrix

| Priority | Reference and source | Study | Syntyr application / acceptance criterion | Boundary |
| --- | --- | --- | --- | --- |
| P0 | [Open Props](https://open-props.style/) | Reusable custom properties, color and motion scales | Keep coherent `--syn-*` token roles, isolate theme overrides, verify in nested roots | Study token strategy; do not import source unchanged without license review |
| P0 | [Every Layout](https://every-layout.dev/) | Intrinsic layout primitives | Reduce bespoke media queries and test reflow at 320 CSS px and 200% zoom | Concepts only; examples may have separate licenses |
| P0 | [SmolCSS](https://smolcss.dev/) | Small responsive recipes | Keep CSS composition independent of JS and build tools | Attribute source when adapting; review per-recipe terms |
| P0 | [W3C ARIA APG](https://www.w3.org/WAI/ARIA/apg/) | Native keyboard and focus interaction guidance | Validate labels, focus order, and dynamic semantics in actual browser tests | ARIA guidance does not provide interactive behavior |
| P0 | [web.dev Learn CSS](https://web.dev/learn/css/) | Cascade, modern CSS, progressive enhancement | Test forced colors, reduced motion, and unsupported CSS fallback | Verify browser targets before depending on newer primitives |
| P1 | [GitHub Primer](https://primer.style/) | Accessible states, density, documented tokens | Compare data tables, responsive navigation, error/help states | Do not copy GitHub branding |
| P1 | [PatternFly](https://www.patternfly.org/) | Complex B2B admin workflows | Cover multi-column CRM records, search, status and overflow handling | Framework implementation not a runtime dependency |
| P1 | [IBM Carbon](https://carbondesignsystem.com/) | Data-rich UX patterns and hierarchy | Verify content density, long labels, tables, status without color alone | Don't transplant proprietary assets |
| P1 | [React Aria](https://react-aria.adobe.com/) | Interaction states and accessibility contracts | Test keyboard sequences, focus and touch behavior for any optional interactive adapter | Patterns are guidance; CSS alone cannot implement interactions |
| P1 | [Base UI](https://base-ui.com/) | Unstyled, composable primitive anatomy | Audit semantic markup and state hooks without adding a mandatory React runtime | Do not assume framework components are drop-in native HTML |
| P1 | [Atlassian Design System](https://atlassian.design/) | Dense work-management navigation and status | Check task tables, contextual actions, labels and long-name overflow | Do not reuse brand assets or proprietary components |
| P1 | [shadcn/ui](https://ui.shadcn.com/) | Copyable component composition and developer ergonomics | Compare documentation clarity, component examples and style customization | Borrow ideas, not framework or Tailwind dependencies |
| P1 | [GOV.UK Design System](https://design-system.service.gov.uk/) | Error summaries, labels and validation patterns | Include real labels and meaningful help/error copy in future interactive examples | Not a guarantee of full WCAG conformance |
| P1 | [CUBE CSS](https://cube.fyi/) | Composition, utilities, blocks, exceptions | Prefer scoped low-specificity CSS over application-level override wars | Pattern inspiration rather than imported code |
| P1 | [Utopia](https://utopia.fyi/) | Fluid type and spacing | Prefer `clamp()` and intrinsic sizing where they improve readability | Verify min/max type sizes for zoom and content |
| P2 | [Mobbin](https://mobbin.com/) | Real product navigation, onboarding and forms | Benchmark authentic information architecture, not just isolated cards | Commercial screenshots are references only |
| P2 | [Refero](https://refero.design/) | SaaS dashboard and marketing layout patterns | Build practical composition samples with independent original copy | Do not copy screenshots/templates |
| P2 | [SaaSFrame](https://www.saasframe.io/) | B2B SaaS workflows, pages and hierarchy | Check onboarding, empty states and page-level navigation in the CRM benchmark | Screenshots and Figma assets are reference material, not source code |
| P2 | [Landbook](https://land-book.com/) | Marketing hierarchy and landing-page structure | Compare small-screen CTA order, readable typography and pricing clarity | Create original layouts, text and artwork; do not replicate submissions |
| P2 | [Lapa Ninja](https://www.lapa.ninja/) | Hero and product-marketing sections | Compare section variety and responsive information hierarchy | Templates and screenshots need independent usage rights |
| P2 | [Refactoring UI](https://refactoringui.com/) | Visual hierarchy, spacing and typography | Validate deliberate size and spacing scales instead of arbitrary one-off values | Paid instructional material is not redistributable |
| P2 | [Codrops](https://tympanus.net/codrops/) | Expressive CSS, typography, subtle motion | Keep futuristic effects opt-in, accessible and motion-reducible | Review each demo's license; no direct copying |
| P2 | [Tailwind Plus](https://tailwindcss.com/plus) | Commercial template packaging and support | Keep MIT CSS fundamentals free; monetize original complete templates | Commercial examples are **not** MIT source assets |

## Decision framework

- **Core first:** native controls, semantic tokens, keyboard focus, responsive layouts and table reflow.
- **Optional recipes:** dashboard shell, marketing hero, code documentation, navigation. Import only needed modules.
- **Commercial boundary:** Free MIT token/component contract; original full-page themes, design files and templates can be sold separately. Avoid creating a feature paywall around accessibility.
- **Do not copy** competitor screenshots, proprietary HTML/CSS, logos, fonts, graphics or exact visual compositions into the repository. A public webpage is not necessarily an open-source asset.
- **Not implemented by CSS:** authentication, filtering, CRUD, stored settings, asynchronous loading, real time charts, server actions. Demo content is fictional and static.

## Benchmark applications

Three intentionally independent, static Syntyr sample interfaces:

1. [Marketing website](../examples/design-benchmarks/marketing.html) — product navigation, hero, feature pricing, CTA and content hierarchy.
2. [CRM dashboard](../examples/design-benchmarks/crm.html) — sidebar navigation, KPIs, captioned data table, GET search form and status text.
3. [Documentation website](../examples/design-benchmarks/documentation.html) — table of contents, inline code, sample command, version caveats and disclosure.

The application pages use `syntyr.core.css` and the optional `syntyr.recipes.css`. Their shared **original** composition stylesheet is `examples/design-benchmarks/benchmark.css`; no font CDN, icon CDN or runtime JavaScript is required. This benchmark tests three *Syntyr adoption scenarios*, not a controlled side-by-side comparison against other CSS frameworks. For comparative framework measurements see `scripts/perf_framework_fixtures.py`.

### Reproduce offline measurements

From a checkout with distribution files built:

```sh
python3 scripts/build.py --check
python3 scripts/design_reference_audit.py
python3 scripts/design_reference_audit.py --json
python3 -m unittest discover -s tests -p test_design_reference_benchmarks.py -v
```

The audit reports real HTML bytes; local Syntyr stylesheet bytes and gzip bytes; **linked** custom CSS (`custom_css_bytes` and `custom_css_gzip_bytes`); **inline** CSS from `<style>` blocks and `style` attributes (`inline_css_bytes` and `inline_css_gzip_bytes`); combined logical custom CSS totals (`custom_css_total_bytes` and `custom_css_total_gzip_bytes`); unique declared `--syn-*` tokens excluding CSS comments and strings; and script plus recognized inline event-handler JavaScript bytes. Inline CSS gzip compresses all inline CSS fragments joined by one newline in document order, once per page, using deterministic `mtime=0`. Linked stylesheet gzip bytes remain the sum of each distinct local CSS file compressed separately, with unchanged linked-only fields. Inline CSS bytes are **already part of HTML markup bytes**, so these analytical totals are not additive network-transfer measurements. The metrics do **not** claim real-world LCP, CLS, browser-interaction latency, color contrast, or full WCAG conformance. Playwright and axe can detect some accessibility problems, but cannot certify WCAG conformance; a complete assessment also requires human review of keyboard operation, screen readers, zoom/reflow, forced colors, and other applicable success criteria. Source checkout and published alpha.4 differ.

### Follow-up quality gates

- Compare the three designs at 320, 375, 768, 1280 CSS pixels, 200% zoom, and with long translated strings.
- Test keyboard-only navigation, high contrast / forced colors and reduced-motion preferences in Chromium, Firefox and WebKit.
- Profile with and without warm CSS caches; capture LCP, CLS, INP and visual screenshots before changing the core.
- Track Syntyr-specific CSS overrides over time, minimizing them when reusable primitives can replace them safely.
