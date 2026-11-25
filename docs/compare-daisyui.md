# Syntyr CSS vs daisyUI: standalone CSS or Tailwind plugin?

**daisyUI** provides named component styles as a Tailwind CSS plugin **or as standalone prebuilt CSS**; **Syntyr** provides independently distributed CSS modules and a scoped design system for native HTML. Both can style ordinary HTML without a dedicated JavaScript component runtime, so the meaningful difference is the styling workflow and ecosystem rather than a blanket "no JavaScript" claim.

**Release note:** Syntyr alpha.4 is published; additional alpha.5 source modules are **unreleased**. Check [distribution](distribution.md) before choosing a module.

## Syntyr and daisyUI compared

| Factor | Syntyr CSS | daisyUI |
| --- | --- | --- |
| Distribution | Prebuilt or self-hosted CSS assets | Tailwind plugin or standalone prebuilt CSS (full CDN stylesheet and individual component files) |
| Component API | `syn-*` names and scoped style tokens | Semantic classes such as `btn`, `card` and theme utilities |
| Runtime JavaScript | Not required for styles | Not required for styles |
| Themes | Published Grid, Noir and Studio; candidate themes in source | Extensive theme and semantic color conventions |
| Integration | Any HTML renderer; no Tailwind dependency | Tailwind integration recommended; standalone styles usable without Tailwind |
| Browser behavior | Native HTML or host-owned interactions | Native HTML or host-owned interactions |

## Choose Syntyr for standalone stylesheets

If your site uses server templates, static HTML or a platform where configuring Tailwind is inconvenient, compare both prebuilt CSS options: Syntyr can be self-hosted, and daisyUI 5 also offers standalone prebuilt CSS (including individual component files) without Tailwind. Scope it with `syn-root`, use explicit component classes and override documented `--syn-*` tokens. You can load optional modules only where needed.

This is primarily a scoping, design-token and workflow distinction—not proof that either library is faster or that daisyUI requires a build step. Verify the CSS files you actually load and, when using a Tailwind build, the CSS it produces.

## Choose daisyUI for an existing Tailwind workflow

daisyUI is especially convenient when your product already uses Tailwind and wants named component abstractions without giving up utility overrides. It offers a broad component and theme catalog, so teams already invested in that ecosystem may gain little from migrating.

## Can you combine Syntyr and daisyUI?

Possibly, but don't layer duplicate component and reset styles over the same elements without a deliberate ownership plan. Check `@layer`, order, theme variables, accessibility and responsive layouts. Migrate a small view first.

See the [comparison index](compare.md), [Syntyr FAQ](faq.md), [theme customization](theme-customization.md) and [official daisyUI 5 release notes](https://daisyui.com/docs/v5/).
