# Syntyr CSS vs Bootstrap: choosing a CSS UI framework

Syntyr and Bootstrap both supply reusable classes for common interface patterns, but they target different priorities. **Bootstrap** has a broad, mature collection of layout utilities, components, examples and optional JavaScript plugins. **Syntyr** focuses on scoped CSS components, semantic HTML and native browser behavior, with no required library runtime JavaScript for styling.

**Version note:** Syntyr v0.3.0-alpha.4 is published; new alpha.5 source modules are **unreleased**. Check the [release and distribution details](distribution.md).

## Feature comparison

| Concern | Syntyr CSS | Bootstrap |
| --- | --- | --- |
| Primary model | Scoped `syn-root` and `syn-*` components | Established Bootstrap component and utility classes |
| Native HTML forms | Standard forms with optional Syntyr presentation | Form control styles and layout utilities |
| JavaScript | No Syntyr runtime required for styles; application owns enhanced behavior | CSS can work alone; specific components use Bootstrap JavaScript |
| Theming | `data-syn-theme` and `--syn-*` tokens | CSS variables, Sass options and color modes |
| Ecosystem | Smaller, evolving design system | Extensive documentation, examples and third-party integrations |
| Styling reach | Explicit scoped region | Bootstrap Reboot and other styles can affect the page globally |

## Why pick Syntyr?

Consider Syntyr when you want tighter style scoping for an existing site, design tokens that serve multiple visual styles, or HTML-first application screens without inheriting a full JavaScript component convention. It can pair with server-rendered templates, HTMX, LiveView and React because the browser receives ordinary HTML.

Native disclosures and browser APIs can handle some interactions, but do not automatically replace every Bootstrap widget. Cross-browser fallbacks and application behavior still need testing. See [progressive enhancement](progressive-enhancement.md) and [accessibility](accessibility.md).

## Why pick Bootstrap?

Bootstrap is a strong choice for teams that want familiar grids, conventional navigation, examples and a broad support ecosystem. Its documented JavaScript plugins can provide production-tested behaviors that Syntyr intentionally leaves to the host application. If your current Bootstrap application works, migrating just for novelty may introduce more risk than value.

## Migrating from Bootstrap

Try one standalone `syn-root` region rather than loading competing component styles indiscriminately. Audit both frameworks' resets, CSS order, button classes, responsive breakpoints and interaction ownership. Replace widgets only after confirming keyboard, touch and screen-reader behaviors.

Compare more options in the [Syntyr alternatives hub](compare.md), check the [FAQ](faq.md), and read the [official Bootstrap introduction](https://getbootstrap.com/docs/5.3/getting-started/introduction/).
