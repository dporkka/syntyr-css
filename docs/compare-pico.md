# Syntyr CSS vs Pico CSS: semantic HTML with different scope

Both **Syntyr** and **Pico CSS** value semantic HTML and low JavaScript overhead, but they make a different tradeoff between out-of-the-box document styling and explicit application components. Pico's default and classless styles simplify conventional HTML pages. Syntyr uses a scoped `syn-root`, explicit component classes and optional semantic modes for larger interfaces.

**Version boundary:** Syntyr alpha.4 is the published release. Some one-file semantic bundles described in alpha.5 source documents are **unreleased**; see [distribution](distribution.md) before installing.

## Feature comparison

| Concern | Syntyr CSS | Pico CSS |
| --- | --- | --- |
| Typical start | Apply `syn-root` and classes to a region | Style native HTML with a small semantic API |
| Classless document styles | Optional scoped semantic mode | Dedicated classless distribution |
| Layouts | Explicit app shells and composable UI styles | Minimal, readable site layout conventions |
| Themes | `data-syn-theme` and `--syn-*` tokens | Pico theme variables and color scheme controls |
| JavaScript for styling | Not required | Not required |
| Migration | Map old selectors and tokens deliberately | Keep Pico if its global markup contract suits the project |

## Choose Pico for minimal websites

Pico is often the more direct option for readable blogs, text-focused sites and forms where styling native tags globally is acceptable. If you only need a few styled elements, a new component vocabulary adds maintenance rather than value.

## Choose Syntyr for bigger UI surfaces

Syntyr is aimed at repeated SaaS dashboards, sidebars, dense business layouts and scoped styling inside an existing host application. You can still use semantic HTML, but explicit classes make styling ownership clearer. CSS won't create app behavior or data logic.

## Is Syntyr a drop-in Pico replacement?

No. Classes, tokens, scope and defaults differ. Migrate incrementally, remove conflicting global selectors and test forms, tables, input states and reduced-motion modes. Follow the detailed [Pico-to-Syntyr migration guide](from-pico.md).

Also see [all alternatives](compare.md), [FAQ](faq.md), [native patterns](native-patterns.md) and the [official Pico classless styles guide](https://picocss.com/docs/classless).
