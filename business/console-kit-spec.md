# Syntyr Console Kit — proposed premium product specification

**Status: private prototype built, not for sale or accepting orders.** The current private preview contains twelve original screen types × Grid, Noir and Studio (36 generated variants), including original screens, approvals and CRM compositions, but no operative commercial license, checkout, customer distribution or validated buyer commitments. The MIT CSS core, all existing free themes, component classes, examples, recipe gallery and accessibility fixes remain free. Any future paid product must separately identify new original screen-level compositions and its operative license.

## Primary buyer and job-to-be-done

Independent developers and small agencies launching operational SaaS, security dashboards, infrastructure tooling, or in-house data apps on server-rendered stacks (Go/templ, Django, Rails, Astro, plain HTML/HTMX). They want polished, distinctive interface screens without wiring a React component system into an otherwise light app.

## Smallest credible kit (8 complete screens)

1. Dashboard home (KPIs, activity, status history, empty/loading/error variants)
2. Resource index (filter form, search, table, pagination and no-results state)
3. Resource detail (metadata, logs, actions and safety confirmations)
4. Create/edit form (native validation, field hints, errors and save confirmation)
5. Settings (profile, preferences and access configuration)
6. Team/invitations (members, roles, invitation table and empty states)
7. Billing overview (plan, invoices and usage; no fake payment processor)
8. Sign-in + reset-entry designs (presentation only; integration required)

For every screen deliver Grid and Noir, phone/tablet/desktop states, real keyboard traversal, proper labels and headings, reduced-motion support, and genuinely empty/error/loading mockups. Use synthetic data only.

## Assets and deliverables

- Self-contained original HTML/CSS pages and shared partials; include MIT Syntyr core with its license notice unchanged.
- Optional Go/templ variant **only after** buyer demand, not as a release blocker.
- Design-token customization guide, typed content schema examples where useful, implementation notes for HTMX/server actions.
- Tested browser screenshots; accessibility findings including unresolved issues, not unsubstantiated certifications.
- Clear support/update term and commercial license for *premium compositions*, never the MIT dependencies.

## Commercial test

Offer an honest demo showing **2 original screens**, clearly label remaining screens as planned. Test $59 one-time, and a $149 studio/agency bundle only if there are at least two distinct products or extra material to justify the bundle. Prefer signed letters of intent or genuine preorders subject to explicit delivery/refund commitments over collecting email addresses alone. No entitlement backend, license-key checks, DRM or telemetry.

Treat the following as research hypotheses, not business results: (a) a distinctive interface is worth paying for, (b) low-JS stacks are an underserved niche, (c) $59 is a credible early offer. Validate through 10 design-partner interviews and at least 10 paid commitments before expanding the pack. Price after support/maintenance cost and real conversion data.

## Not included and deliberately not promised

Live charts, search/filter behavior, authentication, payments, server state, complex comboboxes, or workflows are application responsibilities. Accessible static visuals and native HTML behavior are what the template guarantees. No subscription until ongoing hosted value exists.

## Originality and rights

Tailwind Plus is useful inspiration for **how to categorize and package** an application UI offering, not a permissible source of paid snippets. Do not copy its commercial assets or markup. Keep a per-file provenance manifest and clear `LICENSE-MIT` versus `LICENSE-COMMERCIAL` boundary for future deliverables. Consult qualified counsel before selling the final premium license.
