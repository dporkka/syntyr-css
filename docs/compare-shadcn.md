# Syntyr CSS vs shadcn/ui: CSS primitives or React components?

**shadcn/ui** and **Syntyr CSS** solve different parts of UI development. shadcn/ui distributes editable component source code and interactive patterns for React applications; Syntyr styles native HTML with framework-neutral CSS, optional modules and design tokens. Neither is a one-for-one replacement for the other.

**Release boundary:** Syntyr v0.3.0-alpha.4 is published. The alpha.5 source contains **unreleased** components and integrations; see the [distribution guide](distribution.md).

## What changes when you choose one?

| Factor | Syntyr CSS | shadcn/ui |
| --- | --- | --- |
| Core deliverable | Stylesheets, CSS classes and HTML recipes | Component source installed into your application |
| Framework | Any renderer that outputs HTML | React-oriented official component model |
| Interactive widgets | Host app or browser implements complex behavior | Component patterns and underlying accessible UI primitives |
| Styling | Scoped CSS tokens and `syn-*` classes | Tailwind utility classes and component styling conventions |
| Dependency ownership | No mandatory Syntyr runtime JS | Depends on chosen components and their packages |
| Best fit | HTML-first websites and SaaS presentation | Interactive React products needing editable widget code |

## When Syntyr is the better fit

Choose Syntyr for server-rendered pages, static sites, applications using HTMX or LiveView, or products that want to keep presentation portable across JavaScript frameworks. Syntyr does not ask you to copy a TypeScript component into every project. Use browser-native labels, buttons, forms and disclosures as the baseline.

However, a styled button does not provide data fetching, async validation, complex combobox selection, focus-trapped overlays or table state. Your application must implement those behaviors or adopt a dedicated accessible primitive.

## When shadcn/ui is the better fit

Choose shadcn/ui when a React component codebase is already central and your team wants full ownership of interactive components. Its component system and Tailwind integration can be an advantage for dense product interfaces. It is not accurate to claim Syntyr supplies the same feature depth without implementation work.

## Can they be used together?

They can coexist if styling boundaries are explicit. Keep Syntyr classes scoped to `syn-root`, audit Tailwind Preflight and layer order, and verify keyboard behavior rather than assuming a style adapter changes how widgets behave. The [Radix states guide](radix-integration.md) documents one optional styling integration path.

For more: [all Syntyr comparisons](compare.md), [frequently asked questions](faq.md), [Syntyr components](components.md) and the [official shadcn/ui documentation](https://ui.shadcn.com/docs).
