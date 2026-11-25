# Syntyr for Ghost: CSS components for posts and themes

**Ghost publishing site customization:** Syntyr works with the HTML card in Ghost's editor or with custom Handlebars theme templates. It is suited to featured resource lists, membership benefit callouts and reusable editorial sections, where an ordinary content card needs a more consistent product-style interface.

## Why use Syntyr on Ghost?

Ghost is focused on publishing and memberships. Syntyr adds a configurable, MIT-licensed presentation layer without replacing Ghost's editorial workflow or membership infrastructure. You can reuse the same `syn-root` cards in a Ghost post and on an independently hosted landing page, rather than embedding a separate SPA. The styles are CSS-only; no special JavaScript client is required for headings, buttons, lists or native disclosure.

## How to install Syntyr on a Ghost publication

1. Build `syntyr.embed.css` from the alpha.5 source and host it as a versioned static asset (or include it in a custom Ghost theme).
2. From **Ghost Admin → Settings → Advanced → Code Injection**, add a stylesheet link to the **Site Header**. A theme developer can instead load it from the theme's `default.hbs`.
3. In a post or page, choose an **HTML card** and paste an independent Syntyr component:

```html
<section class="syn-root" data-syn-theme="studio" aria-labelledby="ghost-member">
  <div class="syn-panel">
    <h2 class="syn-heading" id="ghost-member">Member resources</h2>
    <p class="syn-muted">Explore our curated guides and downloads.</p>
    <a class="syn-button syn-button--primary" href="/resources/">See resources</a>
  </div>
</section>
```

4. Test the public post in both your active theme's regular and dark appearances, if offered, and compare the panel with neighboring article typography.

## Limitations and Ghost-specific considerations

An HTML card is not a replacement for Ghost's membership logic, newsletters, forms or paywall: the linked destination still needs to be implemented within Ghost. Code Injection may affect every page, so only render Syntyr classes inside regions you own. Avoid setting `syn-root` on a whole article unless you want Syntyr to control all of that article's typography. Theme updates can alter selector specificity, so recheck your content blocks after an upgrade.

**Ghost references:** [HTML cards](https://ghost.org/help/cards/) and [Adding styles through Code Injection](https://ghost.org/help/code-injection-styles/).

## Verify the result before publishing

Check the public, published URL rather than relying only on an editor preview. Confirm that the Syntyr stylesheet returns HTTP 200 with a CSS content type, that a button inside `.syn-root` has the desired theme, and that unrelated host navigation, product cards and forms remain unchanged. Test keyboard focus, accessible names, narrow screens around 320px, reduced motion and the platform's own responsive layouts. If an iframe is involved, test its height, keyboard navigation, sandbox attributes and HTTPS/CSP restrictions.

**Release compatibility:** The immutable **alpha.4** stylesheet `syntyr.core.css` is published. The **alpha.5** `syntyr.embed.css` bundle is a candidate build designed for existing themes; it is not part of the alpha.4 release. Build the candidate from the source repository and self-host a version-pinned copy for testing. Never load both bundles together, and verify theme-specific overrides before production rollout. Syntyr is a stylesheet, not an official integration or plug-in from the site platform.

Explore the [platform integration overview](site-builders.md), [Syntyr distribution and release guide](distribution.md), or [live host-theme example](../examples/platform-embed.html).
