# Syntyr CSS FAQ: installation, frameworks, licensing and components

Syntyr is an MIT-licensed, CSS-first interface system for native HTML, SaaS dashboards and business websites. These frequently asked questions cover installation, framework compatibility, accessibility, licensing and how it compares with alternatives.

**Version note:** v0.3.0-alpha.4 is the published immutable release, with Grid, Noir and Studio themes. The alpha.5 source tree contains **unreleased** candidate features. Check the [distribution guide](distribution.md) before copying a newer example into a released site.

## What is Syntyr CSS?

Syntyr is a framework-neutral design system built from scoped CSS classes, semantic HTML and design tokens. It styles ordinary buttons, forms, dashboards and reusable page compositions. It is **not** an application framework, data layer or JavaScript widget engine. Browse the [component catalog](catalog.html) and [starter examples](../examples/semantic-starter.html).

## Is Syntyr CSS free and open source?

The core CSS library is available under the [MIT license](../LICENSE). You can use, modify and self-host it in personal or commercial projects under the license terms. Commercial or experimental packages should not be confused with the MIT core; see [products and roadmap](products.html) for product status.

## Does Syntyr require JavaScript or a build tool?

**No runtime JavaScript or build tool is required to use its styles.** Link a stylesheet and write HTML. Browser-native controls such as `<details>` work without a Syntyr script. Your application still supplies JavaScript when required for complex state, data tables, asynchronous workflows or browser fallbacks. See the [progressive enhancement guide](progressive-enhancement.md).

## How do I install Syntyr on an existing website?

Download a published release and self-host the core stylesheet, then add the `syn-root` class to the region you want styled. For a quick evaluation, use the [pinned alpha.4 CSS](https://syntyr-css.pages.dev/v/0.3.0-alpha.4/syntyr.core.css). Do not rely on a mutable development-branch build for production. [Installation and caching details](distribution.md).

## Can I use Syntyr with React, Next.js, Vue, Svelte or Astro?

Yes. Syntyr styles HTML that those frameworks render. Add the stylesheet and use its `syn-*` classes. React and other frameworks still own events, state and application behavior. It also works with server templates, HTMX, LiveView, Livewire and Go templ; see [framework integration examples](framework-integrations.md).

## Does Syntyr work with WordPress, Wix, Shopify, Webflow and Framer?

Potentially, where a platform permits custom stylesheets or scoped HTML/CSS. Editor restrictions, shadow roots, content security policies and hosting rules vary. Syntyr cannot bypass a platform's restrictions. See the [site-builder integration guide](site-builders.md) for platform-by-platform limitations.

## Can Syntyr style semantic HTML forms and native browser controls?

Yes. Its styles work with standard inputs, labels, fieldsets, buttons, dialogs, disclosures and popovers. Some enhanced semantic-mode bundles and patterns are **alpha.5 source candidates**, not published alpha.4 features. Browser support for declarative dialog commands and popover APIs varies; keep an accessible fallback. Read [native patterns](native-patterns.md) and [accessibility](accessibility.md).

## Is Syntyr accessible out of the box?

Syntyr includes CSS for focus and responsive layouts, but **a stylesheet cannot guarantee application accessibility**. Choose proper semantic elements, associate labels, verify contrast across themes, support keyboard navigation, and test at zoom and in forced-colors mode. The [accessibility review](accessibility.md) explains what to verify.

## How do themes and design tokens work?

Use `data-syn-theme` on a scoped root and override documented `--syn-*` custom properties. Grid, Noir and Studio ship in alpha.4; additional themes in the alpha.5 source are not yet published. Start with [theme customization](theme-customization.md).

## How is Syntyr different from Tailwind CSS?

Tailwind supplies utility classes to style nearly anything; Syntyr supplies predesigned, scoped components and token-driven styles that can be used without a compilation step. Neither requires runtime JavaScript for CSS. Choose based on whether you want utility-level control or reusable component defaults. See [Syntyr vs Tailwind](compare-tailwind.md).

## How does Syntyr compare to Bootstrap, shadcn/ui and daisyUI?

Bootstrap offers a mature UI ecosystem; shadcn/ui offers source-owned interactive component patterns; daisyUI offers Tailwind integration and standalone prebuilt CSS. Syntyr emphasizes native HTML, scoped CSS and optional enhancements, rather than replacing a full interactive widget system. Read the [comparison hub](compare.md).

## Can I use Syntyr together with Tailwind or shadcn/ui?

Yes in principle, but test CSS layer order, resets, tokens and which system owns each region. Keep Syntyr scoped inside `syn-root` and avoid applying competing global resets to the same markup. This is an integration choice, not a promised conflict-free plug-in. Read [framework integrations](framework-integrations.md) and [Radix integration](radix-integration.md).

## When should I not choose Syntyr?

Use native CSS alone for a small bespoke interface you can maintain easily. Choose Tailwind if your team prefers utility-first styling; Bootstrap for its ecosystem; or shadcn/ui when reusable, interactive React components are the primary requirement. Syntyr is a better fit when you want a repeatable visual contract for HTML-first pages without adopting a JavaScript component runtime. [Compare the options](compare.md).

## Where do I find documentation and source code?

Start with the [HTML documentation](reference.html), [FAQ](faq.md) and [component catalog](catalog.html), or inspect the [public repository](https://github.com/dporkka/syntyr-css). Search-oriented [comparisons](compare.md) explain the main tradeoffs. Report technical issues on GitHub.
