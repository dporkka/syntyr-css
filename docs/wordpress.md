# Syntyr for WordPress: CSS components and setup guide

**WordPress CSS component library without a JavaScript framework:** Syntyr can style selected Gutenberg Custom HTML blocks, child-theme templates or custom block patterns using ordinary semantic markup. This approach is useful for developer-maintained call-to-action panels, pricing summaries and dashboard-like frontends without replacing your WordPress theme or asking editors to learn a new page builder.

## Why use Syntyr on WordPress?

WordPress themes already manage headers, content templates and plugins. A `syn-root` wrapper lets a developer style just the new feature region, while retaining core menus, native WordPress forms and theme navigation. Syntyr's MIT-licensed CSS uses configurable tokens, accessible focus styling and native HTML elements; no React, npm pipeline, paid UI license or runtime library is required. Teams maintaining multiple WordPress sites can reuse the same source-owned component markup across themes.

## How to install Syntyr in a WordPress theme

1. **Use a staging or child theme.** Copy the candidate-built `dist/syntyr.embed.css` to `wp-content/themes/YOUR-CHILD-THEME/assets/syntyr.embed.css`. Never edit a parent theme directly.
2. **Enqueue the stylesheet.** Add the [Syntyr WordPress enqueue example](https://github.com/dporkka/syntyr-css/blob/main/integrations/wordpress/syntyr-enqueue.php) to the child theme's `functions.php`, or adapt it for a site-specific plugin. This uses `wp_enqueue_style` and a local file modification timestamp as a version.
3. **Add a Custom HTML block.** In the Block Editor, insert `/html` and paste the component below, or render it in a PHP theme template. Add the classes only to the portion you own.
4. **Preview then publish** your page; compare it with other theme pages to check inherited styles.

```html
<section class="syn-root" data-syn-theme="studio" aria-labelledby="wp-feature">
  <div class="syn-panel">
    <h2 class="syn-heading" id="wp-feature">Plan your next project</h2>
    <p class="syn-muted">A reusable feature inside a WordPress page.</p>
    <a class="syn-button syn-button--primary" href="/contact/">Contact us</a>
  </div>
</section>
```

## Limitations and WordPress-specific considerations

The Gutenberg Custom HTML block **does not enqueue** a CSS file; its job is to render markup. Editing permission matters: WordPress can remove HTML that a role lacks permission to add. Managed WordPress.com plans may not allow editing PHP theme files. Additional CSS or a custom block stylesheet can be alternatives, but do not paste a complete core distribution into a post. Avoid applying `syn-root` or optional semantic mode to the entire WordPress `body` because it would affect unrelated plugin widgets and theme elements.

**WordPress reference:** [Custom HTML block documentation](https://wordpress.org/documentation/article/custom-html/).

## Verify the result before publishing

Check the public, published URL rather than relying only on an editor preview. Confirm that the Syntyr stylesheet returns HTTP 200 with a CSS content type, that a button inside `.syn-root` has the desired theme, and that unrelated host navigation, product cards and forms remain unchanged. Test keyboard focus, accessible names, narrow screens around 320px, reduced motion and the platform's own responsive layouts. If an iframe is involved, test its height, keyboard navigation, sandbox attributes and HTTPS/CSP restrictions.

**Release compatibility:** The immutable **alpha.4** stylesheet `syntyr.core.css` is published. The **alpha.5** `syntyr.embed.css` bundle is a candidate build designed for existing themes; it is not part of the alpha.4 release. Build the candidate from the source repository and self-host a version-pinned copy for testing. Never load both bundles together, and verify theme-specific overrides before production rollout. Syntyr is a stylesheet, not an official integration or plug-in from the site platform.

Explore the [platform integration overview](site-builders.md), [Syntyr distribution and release guide](distribution.md), or [live host-theme example](../examples/platform-embed.html).
