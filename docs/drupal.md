# Syntyr for Drupal: scoped CSS in custom themes and Twig

**Drupal theme CSS integration:** Add Syntyr to a custom Drupal theme or selected module template for editorial dashboards, account-area callouts and custom content blocks. Drupal continues to provide routing, permissions, data rendering and Twig template output; Syntyr handles the styling of explicitly marked HTML regions.

## Why use Syntyr on Drupal?

Drupal's asset libraries already let developers attach styles only where needed. Syntyr fits that model: no JavaScript framework, package manager or client-side state layer is needed for its HTML-first components. A `syn-root` region helps avoid accidental changes to Views, admin interfaces and modules that use unrelated classes. That is especially valuable when upgrading a complex Drupal site incrementally instead of replacing its established theme.

## How to install Syntyr using a Drupal theme library

1. Copy `dist/syntyr.embed.css` into your **custom theme**, for example `themes/custom/mytheme/css/syntyr.embed.css`. Use a versioned file from a candidate build during development.
2. Declare a stylesheet in your theme's `mytheme.libraries.yml` (adjust the theme and file names):

```yaml
syntyr:
  css:
    theme:
      css/syntyr.embed.css: {}
```

3. Attach the library where the component is rendered (Twig template or preprocess attachment). In a Twig template, that can be:

```twig
{{ attach_library('mytheme/syntyr') }}
<section class="syn-root" data-syn-theme="studio">
  <div class="syn-panel"><h2 class="syn-heading">Available services</h2></div>
</section>
```

4. Clear Drupal caches after a library change, render the page and check the component alongside adjacent Views or Block output.

## Limitations and Drupal-specific considerations

A library declaration alone does not load CSS on every page: it must be attached appropriately. Syntyr does not alter Drupal permissions, Twig auto-escaping, menus or module behavior. Avoid broad `body` selectors and theme-wide `syn-root` because Drupal sites often combine modules with different markup assumptions. More specific rules in the active custom theme or module stylesheet may still require narrowly scoped overrides.

**Drupal reference:** [Adding theme CSS and JavaScript through libraries](https://www.drupal.org/docs/develop/theming-drupal/adding-assets-css-js-to-a-drupal-theme-via-librariesyml).

## Verify the result before publishing

Check the public, published URL rather than relying only on an editor preview. Confirm that the Syntyr stylesheet returns HTTP 200 with a CSS content type, that a button inside `.syn-root` has the desired theme, and that unrelated host navigation, product cards and forms remain unchanged. Test keyboard focus, accessible names, narrow screens around 320px, reduced motion and the platform's own responsive layouts. If an iframe is involved, test its height, keyboard navigation, sandbox attributes and HTTPS/CSP restrictions.

**Release compatibility:** The immutable **alpha.4** stylesheet `syntyr.core.css` is published. The **alpha.5** `syntyr.embed.css` bundle is a candidate build designed for existing themes; it is not part of the alpha.4 release. Build the candidate from the source repository and self-host a version-pinned copy for testing. Never load both bundles together, and verify theme-specific overrides before production rollout. Syntyr is a stylesheet, not an official integration or plug-in from the site platform.

Explore the [platform integration overview](site-builders.md), [Syntyr distribution and release guide](distribution.md), or [live host-theme example](../examples/platform-embed.html).
