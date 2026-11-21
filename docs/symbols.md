# Icons, Unicode, and ASCII art (optional)

Syntyr styles user-supplied icons and text; it **does not** ship icon glyphs, an
icon font, emoji assets, a JavaScript icon runtime, or an ASCII-art generator.
The free MIT module is `dist/syntyr.symbols.css`. It is optional and works
with any of the seven source themes, server-rendered HTML and framework views.

```html
<link rel="stylesheet" href="/css/syntyr.core.css">
<link rel="stylesheet" href="/css/syntyr.symbols.css">
```

Use these two files, **or** `syntyr.all.css`, not both. If you don't use
icons or text art, load core alone. The module is also included in the
unreleased alpha.5 `syntyr.all.css` source bundle.

## 1. SVG icons (no mandatory icon pack)

Syntyr's `.syn-icon` is only a sizing, alignment and inheritance contract.
Put it directly on an inline SVG, or on a wrapper around an SVG. Default size
is `1.25em`; override `--syn-icon-size` for a specific icon or container.
SVG `stroke` and `fill` remain under your control; this supports both
outline packs and filled icons. The following path is an original example.

```html
<button type="button" class="syn-button">
  <svg class="syn-icon" viewBox="0 0 24 24" fill="none"
       stroke="currentColor" stroke-width="1.8" aria-hidden="true"
       focusable="false">
    <path d="M20 7v5h-5M4 17v-5h5M5.8 9a7 7 0 0 1 12.8-1.8L20 12M4 12l1.4 4.8A7 7 0 0 0 18.2 15"/>
  </svg>
  Refresh report
</button>
<button type="button" class="syn-button" aria-label="Search reports">
  <svg class="syn-icon" viewBox="0 0 24 24" fill="none"
       stroke="currentColor" stroke-width="1.8" aria-hidden="true"
       focusable="false">
    <circle cx="10.5" cy="10.5" r="6.5"/>
    <path d="m15.5 15.5 5 5"/>
  </svg>
</button>
```

**Supported icon sources:** your own SVGs, or individually imported or copied
assets from Lucide, Heroicons, Tabler, and similar libraries under their
respective licenses. None is vendored or required. Avoid loading an entire
icon font or a massive SVG sprite for a handful of icons. An SVG that uses
`currentColor` inherits Syntyr's theme colors automatically.

## 2. Animate icons (optional, pure CSS)

The same optional symbols stylesheet provides six motion modifiers for an
inline SVG or SVG wrapper: `syn-icon--spin`, `syn-icon--pulse`,
`syn-icon--bounce`, `syn-icon--shake`, `syn-icon--wiggle` and `syn-icon--pop`.
Nothing animates unless you add a modifier, and **no JavaScript is required**.

Copy one of the [77 original icons in the Blocks gallery](blocks.html) or use
your own SVG. The icon artwork is not baked into the stylesheet.

~~~html
<!-- Spinning progress icon alongside visible status text -->
<p role="status">
  <svg class="syn-icon syn-icon--spin" viewBox="0 0 24 24"
       fill="none" stroke="currentColor" aria-hidden="true" focusable="false">
    <path d="M12 2v4m0 12v4M2 12h4m12 0h4"/>
  </svg>
  Loading report...
</p>

<!-- Animate only while hovering or keyboard-focusing the button -->
<button type="button" class="syn-button">
  <svg class="syn-icon syn-icon--spin syn-icon--on-interact"
       viewBox="0 0 24 24" fill="none" stroke="currentColor"
       aria-hidden="true" focusable="false">
    <path d="M20 6v6h-6M4 18v-6h6M5 10a7 7 0 0 1 13-3M19 14a7 7 0 0 1-13 3"/>
  </svg>
  Refresh
</button>
~~~

Motion is continuous by default. Control it per element or on a shared parent:

~~~html
<svg class="syn-icon syn-icon--pop syn-icon--on-interact"
     style="--syn-icon-motion-duration:350ms;
            --syn-icon-motion-iterations:1;
            --syn-icon-motion-easing:ease-out"
     viewBox="0 0 24 24" aria-hidden="true"><!-- your paths --></svg>
~~~

| CSS variable | Default | Meaning |
| --- | --- | --- |
| `--syn-icon-motion-duration` | `1s` | Length of one cycle |
| `--syn-icon-motion-iterations` | `infinite` | Number of repetitions; use `1` for one-shot effects |
| `--syn-icon-motion-easing` | `linear` for spin; `ease-in-out` otherwise | Timing function |

`--on-interact` pauses motion until the icon itself is hovered or focused, or
its enclosing button/link is hovered or keyboard-focused. It does not register
events or implement loading state. An icon with a running animation class and no
`--on-interact` animates continuously.

Every preset is fully disabled by `prefers-reduced-motion: reduce` (including
hover/focus effects). Always communicate loading, success and errors in visible
text or semantic status; motion must remain decorative. Animate a wrapper if
other CSS already controls the SVG's `transform` property. Only one motion
modifier should be applied per icon.

## 3. Unicode as actual text

```html
<span class="syn-symbol syn-symbol--accent" aria-hidden="true">◆</span>
<span>Operational</span>
<span class="syn-symbol syn-symbol--muted" aria-hidden="true">→</span>
<span>Details</span>
```

Useful small marks include `→`, `›`, `◆`, `◇`, `●`, `▸`, `⌘`,
and `⌁`. They are examples, not a mandatory character vocabulary. Unicode
symbols need font coverage; system font fallbacks, emoji variation selectors,
platform-specific glyphs, high-contrast mode and text direction can all change
their presentation. Check the exact characters in your target browsers and fonts.
Do not rely on a symbol's color or shape alone to communicate state.

## 4. ASCII and Unicode box-drawing art

Use real `<pre>` text. `.syn-ascii` preserves spaces, line breaks and
monospace alignment and scrolls horizontally rather than splitting a border.
It pairs with existing `.syn-terminal` recipes, but does not require them.

```html
<p id="sys-health">API online and jobs online.</p>
<pre class="syn-ascii syn-ascii--accent" aria-hidden="true">+-------------------+
|  SYSTEM: ONLINE   |
+-------------------+
|  API  [OK]        |
|  JOBS [OK]        |
+-------------------+</pre>
```

The example above is **ASCII**. Unicode box-drawing characters such as
`┌─┐│└─┘` are an optional visual alternative, not ASCII. Unicode can contain
wide or ambiguous-width characters, so text grids may not align consistently
across fonts and platforms; don't embed emoji in precision-aligned columns.
Use spaces, not tabs, for exact alignment. The CSS never inserts semantic
content with `::before` or `::after`.

## Accessibility and fallback rules

- Decorative SVGs and symbols next to visible labels use
  `aria-hidden="true"`; inline SVGs may also use `focusable="false"`.
  Icon-only interactive controls need a meaningful accessible name
  (`aria-label` or visible visually-hidden text) and keyboard focus.
- Decorative text art may use `aria-hidden="true"`, **but the information
  must also exist as ordinary visible text, table or markup**. If the art
  conveys important information, do not hide it without an equivalent.
  Test with a screen reader, zoom/reflow and forced-colors settings.
- Don't depend on Unicode or pseudoelement `content` for meaningful labels.
  A missing glyph must never remove an action or its status semantics.
- Native CLI programs do **not** load CSS. Use Syntyr's separate
  `terminal/palettes.json` ANSI colors, honor `NO_COLOR`, detect TTY
  support, and offer a plain-text fallback. Don't impose Unicode art on
  terminals that cannot render it.

See the [standalone gallery](../examples/symbols.html), the existing
[terminal and geometry guide](geometry-terminal.md), and the
[CSS distribution notes](distribution.md).
