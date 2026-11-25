# Syntyr CSS vs Tailwind CSS: components or utility-first styling?

**Syntyr vs Tailwind CSS** comes down to the level of abstraction you want in your markup. Tailwind is a utility-first CSS framework for composing designs with many small classes; Syntyr supplies themed component classes and scoped design tokens you can apply to native HTML. Both approaches can produce fast, accessible applications, and neither requires JavaScript just to display CSS.

**Version note:** Syntyr alpha.4 is the published immutable release; alpha.5 source features remain **unreleased**. Validate classes against the [distribution guide](distribution.md).

## Key differences at a glance

| Decision factor | Syntyr CSS | Tailwind CSS |
| --- | --- | --- |
| Styling approach | `syn-*` component classes, theme tokens and optional semantic styles | Composable utility classes near the markup |
| Build workflow | Prebuilt CSS can be linked or self-hosted without a consumer build step | Common production workflow generates CSS from detected utilities |
| Runtime JavaScript | Not required by CSS | Not required by CSS |
| Custom design detail | Token overrides, scoped classes and custom CSS | Granular utilities, variants and arbitrary-value styling |
| Design defaults | Consistent component styles and several published palettes | Team-defined compositions and theme conventions |
| HTML ownership | Native elements and any HTML renderer | Native elements and any HTML renderer |

## Choose Syntyr when a reusable interface contract is the goal

Syntyr can shorten repetitive page styling when a product has many related tables, forms, navigation regions and SaaS screens. A shared `syn-button` or card style reduces the number of visual decisions in each template. Themes are applied through `data-syn-theme` and documented `--syn-*` variables. CSS is scoped under `syn-root` to limit unintended changes elsewhere.

This does **not** make Syntyr inherently smaller, faster or more accessible than a well-designed Tailwind application. Measure actual assets and test real markup.

## Choose Tailwind when utility control is the goal

Tailwind gives developers precise layout and responsive control in components through utility classes and variants. It fits teams who already maintain a Tailwind pipeline and want wide ecosystem support. The downside can be repeated class-heavy markup or the need to establish component conventions of your own; for many teams that flexibility is exactly the attraction.

Syntyr and Tailwind can coexist in separately owned regions, but account for Preflight, cascade layers and token collisions. A blanket claim of frictionless compatibility would be misleading.

## Migration example and recommendation

For a pinned Syntyr release, self-host the stylesheet and style a native button as `<button class="syn-button syn-button--primary">Save</button>` within `<main class="syn-root" data-syn-theme="studio">`. The button submits or triggers your application logic as normal; Syntyr doesn't implement the action.

Start with one isolated page, compare real CSS transfer and maintenance costs, then keep the approach that fits your workflow. See the [FAQ](faq.md), [all comparisons](compare.md), [component catalog](catalog.html), and [official Tailwind utility documentation](https://tailwindcss.com/docs/styling-with-utility-classes).
