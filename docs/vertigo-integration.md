# Optional Syntyr CSS skin for Vertigo admin

**Status: original MIT styling demonstration, not an installed Vertigo
plugin or an end-to-end Vertigo deployment.** No Vertigo database, auth,
billing or tenant state was invoked to render the static example.

The live example is at
https://dporkka.github.io/syntyr-css/examples/vertigo-admin.html

A separate **private** Vertigo integration has been exercised against a
local, disposable Go/PostGIS application with two authenticated tenant sessions
and real generated task CRUD. This is owner-run development evidence, **not**
a public hosted demo, production certification, shipped Vertigo plugin, or
commercial bundle. The public example above remains a static illustration;
no auth, tenant routing, billing, or CRUD backend runs in that page.

We are researching whether separately authored premium application compositions
would help developers using Go and server-rendered HTML. The existing MIT
Syntyr CSS and adapters remain free. No paid Vertigo/Syntyr product or checkout
is currently offered.

## Why optional, not a hard dependency

Vertigo's Go admin templates in kit/admin/admin.go use an inline stylesheet
and classes such as .row, .cards, .card, .button, .search, .tablewrap and
.notice. Syntyr includes a separate opt-in stylesheet that targets these
existing class names, scoped to the body class syn-vertigo-admin.

No user of Vertigo must install Syntyr. No user of Syntyr must install
Vertigo. This adapter is an optional presentation layer only.

## Integration outline (on your Vertigo application branch)

1. Copy Syntyr's MIT-licensed compiled core CSS and
   integrations/vertigo/admin.css into assets served **locally** by the
   Vertigo application, for example at /assets/syntyr.core.css and
   /assets/syntyr.vertigo.css. Keep license attribution.
2. Mount a public read-only static asset handler for those exact paths
   using Go's net/http or your existing static server. Do not add CDN or
   authentication requirements for public CSS files.
3. The current Vertigo admin pageShell helper builds a common HTML shell
   with an inline default CSS block. Change the *application-specific*
   shell only if you choose to enable Syntyr; link both CSS files
   **after** its existing inline style, and add body classes and a theme:

~~~html
<!-- After Vertigo's existing <style>...</style> in <head> -->
<link rel="stylesheet" href="/assets/syntyr.core.css">
<link rel="stylesheet" href="/assets/syntyr.vertigo.css">
<!-- In the shared body tag -->
<body class="syn-root syn-vertigo-admin" data-syn-theme="studio">
~~~

4. Leave the default Vertigo HTML templates and security middleware intact.
   Test admin index, list, edit/create, errors, confirmations, tenant
   boundaries, keyboard navigation and forms against your real application.
5. For the dark themes, switch the body to data-syn-theme="grid" or
   data-syn-theme="noir". Both palettes are in the same CSS core.

**This repository does not modify Vertigo pageShell automatically.** The
current Vertigo function compiles templates with a hard-coded shell; a
production-quality opt-in shell configuration belongs in Vertigo, with its
own tests, if enough customers request it.

## Boundaries and accessibility

- CSS changes presentation, not route authorization, CSRF validation,
  RLS, tenant routing, billing entitlements or input validation.
- The default Vertigo admin template includes native form controls; some
  search fields and data tables should still be audited for accessible
  labels, headings, error references and table headers in their real state.
- Vertigo's own dangerous-action confirmation currently uses inline
  JavaScript in some admin templates. Syntyr's adapter adds **zero**
  JavaScript but does not remove script used elsewhere in Vertigo.
- In a production app, load from your own server, pin the Syntyr
  stylesheet version, test with a CSP, and verify focus, reduced motion,
  real zoom and high-contrast modes.

The styling adapter is independent of Hugo and Zola. Syntyr's static
site does not need a Vertigo process to use this CSS.

## Verified scope (November 14, 2026)

- Chromium, Firefox and WebKit passed browser interaction/viewport checks
  on the optional static admin preview at 320, 390 and 1280px.
- Automated tests checked that the existing Vertigo-style card and button
  class names actually render Syntyr surface/accent tokens in Studio and
  Noir, then checked that removing the optional stylesheet removes its paint.
- Enlarged-text reflow cases passed in Chromium, Firefox and WebKit.
- axe-core 4.10.3 recorded no confirmed automated WCAG-tagged violations on
  the static adapter demo, but one inconclusive check requires manual review.
  Actual screen-reader and browser zoom testing remain incomplete.

These are presentation-level checks of a standalone HTML example, not
end-to-end verification of Vertigo's authenticated resource CRUD screens.

## Current Vertigo shared-shell integration (separate opt-in branch)

Syntyr additionally provides `integrations/vertigo/shell.css`, a token bridge
for Vertigo's newer `kit/ui` `.vg-*` components. The `feat/optional-syntyr-skin`
branch in `dporkka/vertigo` vendors the **published alpha.4 core** plus this
bridge and the legacy `admin.css` adapter, and enables it only with
`VERTIGO_UI_SKIN=syntyr`. CSS is served locally from a versioned path. Its
Go regression tests do not establish end-to-end database-backed UI approval.
