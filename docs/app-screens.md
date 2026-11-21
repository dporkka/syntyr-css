# Nine native application screens

Nine original, framework-neutral **application screens** pair existing Syntyr core and recipes classes with an optional, copy-owned example stylesheet. These examples are intended as complete layout starting points rather than a new component API. **All names, accounts, timestamps, statuses, prices and connections are illustrative.** They do not communicate with a service or persist state.

| Screen | Example file | Purpose |
| --- | --- | --- |
| Workspace setup | [app-onboarding.html](../examples/app-onboarding.html) | First-run checklist, progress and next-step navigation |
| Team and invitations | [app-team.html](../examples/app-team.html) | Member directory, roles, pending invites and scope guidance |
| Notification center | [app-notifications.html](../examples/app-notifications.html) | Unread/read activity, clear timestamps and preview preferences |
| Integrations | [app-integrations.html](../examples/app-integrations.html) | Connected and available service catalog with permission guidance |
| Security and access | [app-security.html](../examples/app-security.html) | MFA, session history, API-key empty state and security checklist |
| Account and profile | [app-account.html](../examples/app-account.html) | Disabled form fields, preferences and organization context |
| Audit log | [app-audit.html](../examples/app-audit.html) | Actor, resource, outcome and UTC event table, with disabled filters |
| Help and support | [app-support.html](../examples/app-support.html) | Native FAQ disclosures, guidance and example requests |
| Application states | [app-states.html](../examples/app-states.html) | Empty, error, loading, permission denied and offline recipes |

## Copy the markup and styles

These are **nine real HTML files**, not sections that require a JavaScript tab router. All navigation uses ordinary links with real destinations. Each example loads `syntyr.core.css`, then `syntyr.recipes.css`, and finally [`app-screens.css`](../examples/app-screens.css). Copy the three CSS assets or use your app's existing pinned Syntyr version. The `app-screens.css` file has no external imports or assets and styles only the `.app-screens` example subtree; it is not bundled in the stable core API. Do not load an all-in-one bundle alongside the individual CSS files.

Each page uses `.syn-root`, `.syn-app-shell`, `.syn-app-rail`, `.syn-app-nav`, `.syn-workspace`, `.syn-app-card`, and appropriate native semantic HTML elements. The sidebar and page headings are standalone; when embedding a page in an existing shell, remove duplicate landmarks and preserve exactly one page `h1` and `main`. Adapt the `href` values to your router or server-rendered paths.

## Connect real application behavior safely

- **Team and invitations:** authenticate, authorize membership mutations per organization, validate roles and email addresses on the server, apply rate limits, and send invitations through an approved backend. Buttons stay disabled in the static examples.
- **Notifications:** fetch member-scoped events with stable IDs; enforce authorization before marking read. The example shows no functional preference save or notification delivery. If you add a preference form, include CSRF protection and a clear success/error response.
- **Integrations:** initiate OAuth or equivalent authorization in the server flow, store tokens encrypted, track scopes and revocation, and verify callbacks. Never embed client secrets or pretend a static connected label proves an active integration.
- **Security:** enforce recent authentication for MFA, recovery-code issuance, session revocation, and API-key creation. Show secrets once and never include a real key in HTML, telemetry, URLs, or screenshots. The API-key empty state is deliberate.
- **Account/profile:** require authentication, validate personal data and display sensitive updates only after reauthentication; never mistake disabled sample fields for persisted data.
- **Audit logs:** store tenant-scoped append-only events, redact sensitive payloads, and enforce permissions on export and filtering.
- **Support:** validate submissions server-side, implement rate limits and avoid exposing private support cases. Native FAQ details can work without JavaScript.
- **UI states:** ensure loading statuses are announced without repeated alerts, errors provide recovery actions, and permission-denied states never substitute for backend authorization.
- **Onboarding:** track completed steps in a durable member/organization record. This static example marks a step current with `aria-current="step"` but does not claim persistence.

Keep selection and activity status in content rather than relying solely on color. Read-only demonstration controls that would mutate data are intentionally disabled. Replace fictional sample data before production use, and do not remove `disabled` until the server endpoint and policy checks actually exist.

## Validation

Run focused structural tests with `python3 -m unittest discover -s tests -p test_app_screens.py -v`. The optional browser regression uses a locally installed Playwright package and Chromium, without becoming a Syntyr runtime dependency:

```sh
SYNTYR_PLAYWRIGHT_MODULE=/path/to/playwright \
SYNTYR_CHROMIUM=/path/to/chromium \
node tests/app-screens_browser.cjs
```

The browser check covers native navigation, six viewport widths, 200% and 400% enlarged-text stress at 320px, keyboard focus, reduced-motion and forced-colors rendering. The regular browser matrix, reflow suite and axe audit inventories also include all nine pages. A real screen-reader, actual browser zoom and production authorization test are still required before shipping a live app.
