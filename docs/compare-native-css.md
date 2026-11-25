# Syntyr CSS vs plain CSS: when is a design system worth it?

Syntyr is **written in CSS**, so "Syntyr vs native CSS" is not a comparison of competing browser technologies. The decision is whether to maintain your own styles from scratch or adopt a predefined, scoped design system. Plain CSS, custom properties, cascade layers and native HTML remain available with or without Syntyr.

**Release note:** Syntyr alpha.4 is published; experimental alpha.5 source patterns are **unreleased**. Start with the [versioned distribution guide](distribution.md).

## Build from scratch or adopt Syntyr?

| Concern | Syntyr CSS | Plain CSS |
| --- | --- | --- |
| Base styling | Existing `syn-*` components and theme tokens | Every visual convention is authored by your team |
| Dependencies | Stylesheet distribution; no required runtime JavaScript | No third-party design-system dependency |
| Consistency | Shared component names across screens | Depends on your own CSS architecture |
| Flexibility | Extend tokens and styles within a predefined contract | Full ownership of selectors, cascade and component rules |
| Long-term cost | Track a small external API and release differences | Maintain internal primitives, documentation and consistency |
| Semantic HTML | Uses normal browser elements | Uses normal browser elements |

## When plain CSS is the better choice

Choose native CSS for one-off landing pages, a distinctive editorial site, or small bespoke components where maintaining a shared library is unnecessary. New browser features—container queries, `color-mix()`, `:has()`, cascade layers and custom properties—reduce the amount of custom framework code many apps need.

A well-maintained stylesheet may be more durable than any external library if the number of repeated UI surfaces is small. No framework, including Syntyr, guarantees speed or accessibility.

## When Syntyr earns its dependency

Adopt Syntyr when the same component contracts recur across multiple pages, products or teams. Its CSS variables and scoped style names can simplify palette changes and visual governance. The core is MIT-licensed and can be self-hosted, but you're still responsible for version pinning and testing.

## A practical experiment

Take one screen, implement it with your existing CSS and a scoped Syntyr region, and compare actual maintenance burden, CSS transferred, accessibility outcomes and time spent on visual consistency. If Syntyr adds more conventions than it removes, stick with plain CSS.

Explore the [alternatives hub](compare.md), [FAQ](faq.md), [native browser APIs](native-browser-apis.md) and [MDN's introduction to CSS](https://developer.mozilla.org/en-US/docs/Web/CSS).
