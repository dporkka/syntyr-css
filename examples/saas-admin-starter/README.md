# SaaS Admin Starter

Four ready-to-copy pages using the **unreleased Syntyr alpha.5 source candidate**.
No runtime JavaScript, framework, remote assets, API, backend or payment processor.

Open [Overview](index.html), [Pipeline](pipeline.html), [Customers](customers.html)
and [Billing](billing.html). Each page is a complete HTML document with common
navigation, responsive page-specific CSS and Syntyr core/recipe styles.

## Reuse

Copy the four HTML files and `styles.css` into your app. Update stylesheet paths
to the matching `dist/syntyr.core.css` and `dist/syntyr.recipes.css` release
candidate assets. The currently published alpha.4 package is **not** guaranteed
to contain the source-candidate APIs this template uses.

## Integration contract

- All names, dates, metrics, money and statuses are fictional.
- Internal links work; data mutations, sign-in and invoice downloads do not exist.
- The Customers `GET` form sends query parameters to `customers.html`, but the
  static preview does **not** apply filters. On a server, validate/encode inputs,
  escape outputs, preserve form values, paginate and enforce tenant-scoped access.
- Pipeline status is read-only. Implement stage changes and audit trails in the host.
- Subscription management is disabled. Only enable after building authorized
  billing sessions, signature-checked idempotent webhooks and entitlement checks.
- Preserve skip links, captions, labels, keyboard scrolling, focus, reduced motion,
  forced-colors behavior, and zoom/reflow support.

Run `python3 -m unittest discover -s tests -p test_saas_admin_starter.py -v`
to check the template contract. MIT licensed.
