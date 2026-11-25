# Email UI components with Syntyr CSS

Use Syntyr's optional email module for email-related **web interfaces**: newsletter subscription, mailbox lists, message reading, composing, notification preferences and one-time email verification. The components are MIT-licensed, framework-neutral, semantic HTML and CSS only. They work with native forms, HTMX, server-rendered HTML, React and other HTML renderers; Syntyr does not send messages or store state.

**These are not HTML email templates.** Gmail, Outlook and other **email clients** have different CSS support from modern browsers. Do not paste `syntyr.email.css` into outbound email or assume its cascade layers, variables and container queries will be supported. Build transactional/marketing email markup separately, with email-client-tested inline styles and appropriate plain-text fallbacks.

## Installation

Load the standard core first, then the opt-in module:

```html
<link rel="stylesheet" href="/dist/syntyr.core.css">
<link rel="stylesheet" href="/dist/syntyr.email.css">
```

The complete `syntyr.all.css` bundle also includes the email module, but **core stays unchanged**. The optional selective builder accepts `--modules email` and assembles tokens and base styles without needing Node or JavaScript:

```sh
python3 scripts/build_selective.py --components forms,form-composition,buttons --modules email --output /tmp/email-ui.css
```

Use the [backend-free example](../examples/email.html) for complete semantic markup. The demo disables all submit buttons rather than pretending to save or send data.

## Component inventory

| Pattern | Class | Native HTML and application responsibility |
| --- | --- | --- |
| Email signup | `.syn-email-signup` | `<form>`, explicit `<label>`, `<input type="email" required autocomplete="email">`, consent, server subscription endpoint |
| Inbox | `.syn-email-workspace`, `.syn-email-layout`, `.syn-email-sidebar`, `.syn-email-inbox`, `.syn-email-item` | `<nav>` with list links; server marks unread with `data-syn-unread="true"` and current location with `aria-current="location"` |
| Message preview | `.syn-email-meta`, `.syn-email-subject`, `.syn-email-preview`, `.syn-email-time` | Real sender/subject/time text, `<time datetime>`; no fake read receipt |
| Message detail | `.syn-email-message`, `.syn-email-message-header`, `.syn-email-body` | Article, title, sender/recipients, safe body content; sanitize rich messages |
| Composer | `.syn-email-compose`, `.syn-email-recipient-list` | Labeled native email, subject, textarea and file inputs; application resolves recipients, drafts, attachments and sending |
| Preferences | `.syn-email-preferences` | `<fieldset>`/`<legend>` and native checkboxes; application persists per-channel consent and opt-out |
| Email verification | `.syn-email-code` | Native `type="text"`, `inputmode="numeric"`, `autocomplete="one-time-code"`; server validates token and enforces expiration/rate limits |

All classes are scoped to `.syn-root`. Compose with existing `.syn-form`, `.syn-field`, `.syn-label`, `.syn-input`, `.syn-textarea`, `.syn-button`, `.syn-chip`, `.syn-check` and `.syn-panel` instead of introducing duplicates. The mailbox switches from one column to two based on its **container width**, not the viewport. Theme colors come from existing `--syn-*` tokens. Forced-colors selections and keyboard focus remain visible.

## Signup and consent

```html
<section class="syn-root" data-syn-theme="studio">
  <form class="syn-email-signup" action="/newsletter/subscribe" method="post">
    <div class="syn-field">
      <label class="syn-label" for="signup-email">Email address</label>
      <input class="syn-input" id="signup-email" name="email"
             type="email" autocomplete="email" required>
    </div>
    <button class="syn-button syn-button--primary" type="submit">Subscribe</button>
  </form>
</section>
```

Only use an actual application endpoint for the form action. Validate and normalize addresses server-side without assuming browser validation is sufficient. Capture a clear consent record where necessary, send confirmation as appropriate, respect unsubscribe requests, and avoid prechecked marketing-consent boxes. Add CSRF protection, bot and abuse controls, and rate limiting as your framework requires. A subscription form alone does not establish consent.

## Inbox and composing

Render each inbox row as **one link**; do not nest a reply button or another link inside it. If a row needs actions, use a separate action area rather than a nested interactive target. Maintain the actual unread/current state on the server or in application state; CSS only styles the supplied attributes. An unread dot must be accompanied by an accessible text indication (for example, "Unread" in the link's accessible name). `aria-current` identifies the current destination, not a checkbox or multiselection state.

Display plain-text email with escaped text, preserving necessary line breaks; treat HTML from senders as **untrusted content**. Render sanitized email HTML in a properly sandboxed and isolated surface only when necessary, with remote images, tracking pixels, links, downloads and attachments handled under explicit product policies. Do not `innerHTML` raw inbound email into `.syn-email-body`.

Use native `<input type="email">` for individual recipients and `multiple` only when you actually accept a comma-separated list. `.syn-email-recipient-list` is visual decoration for validated recipient tokens; it is **not** a tokenizing combobox or address-book integration. The application owns add/remove, keyboard interaction, draft autosave, backend sending and delivery state. The browser-supplied file picker must be paired with server-side file size, type, antivirus and authorization checks.

## Preferences, verification and transactional semantics

Keep security/transactional notifications separate from optional marketing subscriptions. For marketing preferences, a functional opt-out mechanism and correct consent records are requirements of the product and applicable laws, not effects of CSS. Persist choices and show an explicit success or failure state after submitting. For one-time verification, tokens must be unpredictable, expire, have replay protection, and be rate-limited; autocomplete assists users but does not verify identity itself.

The module has **no runtime dependencies**, does not provide an email transport, and cannot guarantee a message's arrival. If you want reusable *outbound* email templates, implement them as a separate export with compatibility tests in actual email clients rather than sharing browser CSS.
