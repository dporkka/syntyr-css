# Syntyr visual composition — premium restraint, distinct character

This guide applies original layout decisions informed by the **principles**
publicly described by Resend, Vercel, Linear, Raycast and PostHog. Do not copy
their proprietary brand marks, code, fonts, illustrations, components or layouts.
The Syntyr CSS public contract stays independent and MIT licensed.

## Product-led presentation

- Show a real HTML/CSS component next to the markup used to construct it.
  Annotate fictional data honestly; never imply a static mockup is a live app.
- Use one dominant action and one secondary action in the first viewport.
  Move tertiary exploration paths to the next relevant section.
- Give each page one descriptive `h1`, readable section headings, and a clear
  keyboard-first navigation path. Do not rely on visual headings alone.

## Surface and typography rules

1. Prefer **one visible boundary per edge**. When nested surfaces both have
   borders, use `--syn-border-subtle` for internal dividers and reserve
   `--syn-frame` / `--syn-frame-strong` for controls and meaningful edges.
2. Apply depth sparingly. A raised overlay may use `--syn-shadow-overlay`;
   routine dashboard cards should rely on spacing and role separation first.
3. Use `--syn-font-ui` for ordinary controls, `--syn-font-display` for
   headings and `--syn-mono` for technical data. The optional system-serif
   editorial recipe should not bleed into operational controls.
4. Prefer sentence case for Studio, Minimal and Corporate UI. Technical
   uppercase labels are intentional in Grid and Terminal, not the default.
5. Use `--syn-accent` for real actions, selection, and a few signature
   details. Do not color every title, border, metric and icon at once.

## Shared spacing and responsive composition

- Use `--syn-page-gutter` and `--syn-content-max` for shell geometry instead
  of repeating fixed per-theme page widths. Use `--syn-section-space` for
  ordinary section separation, and `--syn-content-gap` for general layout.
- Place headings and their copy in `.syn-stack` or `.syn-u-stack` when using
  component spacing. These suppress only direct-child margins; preserve
  `.syn-prose` for readable long-form copy and explicit utility margins for
  intentional exceptions.
- Preview compact, comfortable, and spacious panel padding across *nested*
  themes. Preserve touch target sizing and readable type independent of density.
- Keep mobile heroes content-led: shorten vertical padding before reducing
  typography or truncating meaningful content. Test 320px and a larger
  desktop width, including text-resize and right-to-left layout as applicable.

## Same components, three visual directions

- [Studio operations](../examples/flagship-studio.html): compact density,
  unambiguous tables, quiet cards and a clear action order.
- [Noir editorial](../examples/flagship-noir.html): system serif, atmospheric
  background on one section, generous white space, restrained warm accents.
- [Grid control](../examples/flagship-grid.html): precise geometric framing,
  sparse cyan highlights, legible operational records and explicitly simulated
  output. Opt into cinematic effects only on a contained hero.

These are **documentation-only compositions**. Their `flagship.css` file is
application-owned showcase styling, not an additional required Syntyr module.

## Accessibility, motion and maintenance

- Maintain visible focus indicators and appropriate contrast for meaningful
  text and control boundaries; never depend on color, glow, or tiny labels alone.
- The data or state must still make sense at 320px and 400% zoom. Wide tables
  may scroll in a labeled, keyboard-focusable region.
- Suppress nonessential effects under forced-colors; respect reduced motion.
  Avoid perpetual `will-change`, large blur layers and decorative timers.
- Favor CSS custom properties and existing `syn-*` classes over bespoke
  component forks. Keep theme, density, intensity, and geometry independent.
- Measure real browser rendering and review screenshots before making
  visual regressions a release gate.

## References

Public design reading:
- [Resend brand guidelines](https://resend.com/handbook/design/what-are-our-brand-guidelines)
- [Linear design refresh](https://linear.app/now/behind-the-latest-design-refresh)
- [Vercel Geist design system](https://vercel.com/geist/introduction)

See also [theme customization](theme-customization.md),
[visual intensity](visual-intensity.md), and
[design research](design-research-linear-resend.md).
