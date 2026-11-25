# Syntyr Figma Design Kit — alpha.5 pilot

[Open the editable Syntyr kit](https://www.figma.com/design/Lj8uKUtgJfXMyzVb96x5Q1)

This is **an editable design pilot**, not a Figma Community publication, a
complete accessible component library, or a pixel-perfect mirror of CSS.

## Created in Figma

- Seven independent **single-mode** collections: Studio, Grid, Noir,
  Industrial, Terminal, Corporate and Minimal; nine literal palette
  color variables per collection (**63 variables**). Code syntax maps to
  `var(--syn-*)`.
- Existing four Studio components: primary and outline button, panel, and
  success status, plus their original review.
- New **Syntyr / Button Variants v1** component set: Style=Primary/Outline
  × State=Default/Focus/Disabled (**six variants**). Each has a label
  property linked to the text node.
- New **Syntyr / Input States v1** component set: Default, Focus,
  Invalid and Disabled (**four variants**) with editable placeholder text.
- New standalone **Syntyr / Navigation v1** and **Syntyr / Table v1**
  components; review frames contain instances rather than copies.

Both new review frames were inspected visually. The input review still has
a **compact invalid-state instance** despite an attempted width correction,
and the primary focus ring is an approximation. Do not publish until these
discrepancies and all relevant contrast states are resolved.

## What Figma does not guarantee

The Figma Starter workspace only permits **one variable mode per collection**.
Theme switching is not implemented as seven modes in a single collection.
The source JSON includes 13 literal colors and 2 dimensions per theme;
the current native kit contains only nine selected color roles per theme.
Do not claim exact 1:1 token parity or copy over incomplete modes blindly.

Studio references from `src/tokens.css`: background #F5F7FB, surface
#FFFFFF, text #15233A, accent #2458C6, accent foreground #FFFFFF,
frame #B8C6D8 and success #17694B. Default button min-height 44px,
14px semibold text, 16px horizontal padding, 4px radius at 16px root.

The design uses Inter as a practical font substitute for CSS's system stack;
native focus outline positioning, disabled behavior, ARIA semantics, layout
reflow, responsive rules and hover states **must be verified in a browser**.
Component instances are visual examples only; they are not interactive UI.

The Figma MCP request quota was reached during this iteration. Remaining
work requires additional tool access and review rather than guessing at
the resulting canvas.

## Source-derived design handoff (code-side)

The candidate now generates [a versioned Figma handoff contract](../metadata/figma/syntyr-handoff.v1.json)
from the **actual Syntyr CSS source**, alongside the existing seven palette
token files. Its foundation entries include the original CSS expression,
a 16px-root pixel value **only for literal rem/px sizes**, and a
`requires_browser_validation` flag for expressions such as `clamp()` and
`var()`. Density-mode control heights are derived independently. Component
entries reference the CSS selectors and source files rather than inventing
Figma component state values.

```sh
python3 scripts/export_figma_handoff.py
python3 scripts/export_figma_handoff.py --check
python3 -m unittest discover -s tests -p test_figma_handoff.py -v
```

**Designer reconciliation path:** compare each mode's 13 exported palette
colors with the variables currently present in Figma; import missing roles
without duplicating existing variables. Confirm spacing, typography, native
controls, and the compact invalid-input instance against rendered CSS at
real browser zoom. Check that button and input variants use variable bindings,
reusable component instances and correct focus/disabled states.

This contract is **not** live Figma synchronization or a parity certificate.
Figma editing was blocked by Starter-plan MCP tool limits during this pass.
The existing native kit, including its known defects, was not modified.

## Remaining designer release gates

1. Repair the invalid input preview width and accurate focus-visible rings.
2. Add full spacing/typography roles and component-level semantic token aliases.
3. Validate color and layout against browser screenshots at all seven themes,
   both default and high contrast / disabled states.
4. Add form label/error/description relationships, responsive tables and
   navigation variants; audit accessibility semantics during handoff.
5. Review editability, variant properties and component descriptions; only then
   consider Figma library/community publication or Code Connect.

Source of truth: `src/tokens.css`, `src/components/buttons.css`,
`src/components/forms.css`, `src/components/data.css`, and
`src/components/layout.css`. Token exchange:
`metadata/figma/syntyr-<theme>.tokens.json`.

## Portable design-token snapshots (source candidate)

For design tools and token pipelines that accept DTCG token documents, export
an explicit theme and density from the canonical CSS without installing Node
or contacting Figma:

```sh
python3 scripts/export_design_tokens.py --theme studio --density compact > studio-compact.tokens.json
python3 scripts/export_design_tokens.py --theme noir --density spacious > noir-spacious.tokens.json
```

The exporter supports all seven source-candidate palettes and three density
modes. It preserves literal rem dimensions and sRGB colors, and expresses
supported CSS references as typed token aliases (for example,
`{palette.accent}`). Each document is a standalone snapshot, not a native
Figma variable collection or a full CSS cascade model.

Responsive expressions, fluid spacing, derived color mixes, typography
stacks and other browser-dependent values are intentionally excluded. The
existing flat Figma palette exports and reconciliation handoff remain
unchanged. Import compatibility with particular versions of Figma, Penpot,
and Tokens Studio requires separate tool-specific verification. This is
source tooling for the unreleased alpha.5 candidate, not an alpha.4 API.
