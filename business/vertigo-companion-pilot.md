# Syntyr × Vertigo companion pilot (research, not a product offer)

**Baseline: November 15, 2026.** Neither a paid Syntyr/Vertigo
bundle nor a customer-ready combined application is available. There are no
verified paying customers, interviewed design partners, signed commitments,
or conversion rates for this specific combination. The public free
[Syntyr admin styling preview](../examples/vertigo-admin.html) is static;
the separate private Vertigo branch has a disposable local two-tenant
PostGIS/browser showcase, not an externally hosted SaaS product.

## Hypothesis worth testing

Developers building Go-based B2B SaaS, operations systems, CRMs, and internal
admin tools may prefer **working Go resource/auth/tenant infrastructure with
a polished, optional CSS skin** to a new JavaScript runtime. The buyer
benefit is reduced implementation and long-term maintenance work, not the
number of visual themes.

The open Syntyr CSS core, tokens, published themes, and existing examples
remain MIT. The Vertigo application and Syntyr presentation layer remain
independently installable. Paid value, if validated, would come from
**new, separately authored application compositions and integration guides**,
not the existing free CSS or claims of finished authentication/billing.

## Target buyer and interview plan

Recruit ten **qualified, opt-in** reviewers who are building or maintaining
real applications: five Go/template or Go/HTMX SaaS builders, three small
agencies developing customer portals, and two developers of data-heavy
vertical operations/CRM tools. This is a research sample, **not** a
statistically representative market survey.

For each conversation, establish:

1. The buyer's current stack, actual application, and procurement authority.
2. Their last dashboard/resource CRUD implementation: time spent on auth,
   responsive styling, forms, accessibility, and tenant isolation.
3. Whether they prefer the unchanged native Vertigo theme or its optional
   Syntyr version **with identical functional behavior**.
4. The largest blocker to copying the publicly available Syntyr HTML/CSS
   into an existing app; distinguish real technical adoption from aesthetic
   preference.
5. Which complete workflows (resource list, editor, approvals, CRM, billing
   presentation) they would buy *as static UI files*, including what backend
   behavior they correctly expect to implement themselves.
6. Their prior paid UI-kit purchases and whether a separately licensed
   premium composition could justify a one-time price. Record a specific,
   verifiable commitment separately from a polite "would buy".

Keep private names, contact records, company information, and notes
**outside this public repository**. Do not mass-message communities.

## Paired technical demonstration

Offer the same fictitious two-tenant task CRUD flow in native Vertigo and
in the optional Syntyr skin. For the latter, the repo owner can run the
local disposable acceptance showcase documented in Vertigo's private
`docs/SYNTYR_SHOWCASE.md` (not accessible to the public). Alternatively,
the public [static admin preview](../examples/vertigo-admin.html) is useful
for CSS feedback but **must never be presented as working auth or CRUD**.

Review the same screen states in both variants: index, list/search,
create/edit form, validation, mobile width, keyboard and screen-reader
navigation. Theme and density changes must not change permission or data
semantics. Do not expose the local fixture server to the internet.

The demonstration is not production security, accessibility, deployment
or performance certification.

## Offer and pricing research

Test *one* optional paid hypothesis after completing the first interviews:

- **Free:** existing MIT Syntyr Core and optional styling bridge.
- **Paid hypothesis:** separately authored, ready-to-integrate Vertigo-oriented
  admin workflow compositions with clean static HTML/CSS, responsive states,
  documentation, and explicit non-inclusion of backend functionality.
- Discuss the existing Syntyr Console Kit's **$59** pilot hypothesis and
  **$149** Pro hypothesis for price sensitivity, without implying those
  products have launched. Avoid creating a third paid SKU or promising
  a Vertigo license bundle before product and license rights are settled.
- Treat customization services as a separate scoped quote, never as a
  bundled entitlement.

## Four-week decision rule

**Week 1:** Publish an accurate demonstration walkthrough, collect ten
qualified interview invitations, and identify at least three reviewers with
a current Go admin UI to ship.

**Week 2:** Complete interviews and pairwise native/Syntyr reviews. Ask for
specific integration objections and previous purchasing evidence.

**Week 3:** Support up to three voluntary code-level trials of the *free*
Syntyr adapter in isolated development projects. Track time to first
correctly styled page and whether real app behavior is preserved.

**Week 4:** Count independent successful integrations, documented purchase
commitments, concrete requested compositions, estimated support hours, and
any product-security blockers. **Unknown is not zero.** Do not infer revenue
from GitHub stars, screenshots, or verbal compliments.

Continue toward a paid offer only if there are actual successful integrations
and credible independently documented buyer commitments. If developers
only like the visual style or integration creates significant support burden,
keep the skin free and stop expanding the bundle concept.

## Non-negotiable launch boundaries

Before any payment or redistribution: resolve the existing Syntyr name
clearance, audit rights to all separately licensed premium source assets,
complete manual accessibility checks, publish accurate product scope/refund
terms, and independently validate checkout/fulfillment. Do not imply that
Vertigo's private repo is redistributed merely because its UI supports
Syntyr. Never transfer existing MIT files behind a paid license.
