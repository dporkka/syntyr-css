# Optional Syntyr animation library

`syntyr.animate.mjs` is an **opt-in, dependency-free ES module** for
application-triggered motion. It delegates timing and compositing to the native
**Web Animations API** and viewport detection to **IntersectionObserver**.
There are no imports, startup side effects, global listeners, background timers,
framework adapters, CSS resets, or changes to core Syntyr.

Use the CSS-only `syntyr.motion.css` for static declarative effects. Load this
JavaScript module only when you actually need to trigger animations in code or
observe viewport entry; either add-on can be used without the other.

## Install and invoke

Copy `dist/syntyr.animate.mjs` and, if desired, `dist/syntyr.core.css` to
your own static directory. The module needs no bundler and runs in evergreen
browsers that support ES modules.

```html
<link rel="stylesheet" href="/css/syntyr.core.css">
<main class="syn-root">
  <button id="show" type="button">Animate card</button>
  <article id="card">Card content stays visible without JavaScript.</article>
</main>
<script type="module" src="/js/animation-demo.mjs"></script>
```

```js
// /js/animation-demo.mjs
import { animate, stagger, observeReveals } from '/js/syntyr.animate.mjs';

document.querySelector('#show')?.addEventListener('click', () => {
  const card = document.querySelector('#card');
  animate(card, 'enter', { direction: 'up', duration: 280 });
});

stagger(document.querySelectorAll('.syn-root .card'), 'fade', {
  interval: 75, delay: 0,
});

// This does nothing until invoked, and only animates opted-in descendants.
const disconnect = observeReveals(document);
// Call disconnect() when unmounting the page/region.
```

When the experimental `@syntyr/css` npm package is published, the module
also has a dedicated typed subpath:

```js
import { animate } from '@syntyr/css/animate';
```

That subpath exposes only the optional animation code and matching TypeScript
declarations. The default package import remains the CSS entrypoint.

## Minimal API

| Export | Purpose | Result |
| --- | --- | --- |
| `animate(element, preset = 'enter', options?)` | Animate one element on demand | Native `Animation` or `null` |
| `stagger(iterable, preset = 'enter', options?)` | Animate each element with an incremental WAAPI delay | Array of animations or `null` entries |
| `observeReveals(root = document)` | Observe `.syn-root [data-syn-reveal]` once per element | `disconnect()` cleanup function |

Presets include `fade-in`, `fade-out`, `slide-up`, `slide-down`,
`slide-left`, `slide-right`, `zoom-in`, `zoom-out`, `pop`, `bounce`,
`pulse`, `shake`, `rotate-in`, `flip-in` and `rotate`. The existing `fade`,
`enter` and `scale` aliases remain supported. `enter` takes
`direction: 'up' | 'down' | 'left' | 'right'` (direction of entrance),
while named `slide-*` presets specify travel direction.
Use `distance` and `scaleFrom` to customize supported effects.

**Playback controls:** `iterations: 3` repeats three times;
`loop: true` (or `iterations: Infinity`) repeats indefinitely.
Repetition is **off by default** (`iterations: 1`).
Use `iterationDirection: 'alternate'` to reverse every other cycle.
Also supported: `normal`, `reverse`, `alternate-reverse`.
`loop: true` and `iterations` cannot both be set;
invalid counts/directions throw `TypeError`. The native Animation
returned by `animate()` exposes `pause()`, `play()` and `cancel()`.

**Speed and rotation:** `speed: 2` runs at double speed; `speed: .5`
runs at half speed. The value is a positive finite multiplier of
native playback rate, and defaults to `--syn-animation-speed` or `1`.
`rotation: -360` makes the `rotate` preset spin counterclockwise
(`360` degrees is the default clockwise turn). The JavaScript
options are also available through `stagger()`.
Use `iterationDirection: 'reverse'` to reverse an entire
animation sequence, including its keyframe progression.

All presets accept `duration` and `delay` in milliseconds and `easing`
as a CSS timing function. `stagger` additionally accepts `interval` in
milliseconds. The module reads existing CSS custom properties when options
are omitted: `--syn-motion-duration` (220ms default),
`--syn-motion-stagger` (65ms), `--syn-motion-distance` (.75rem),
`--syn-motion-scale-from` (.96), and `--syn-ease-out`
(`cubic-bezier(.22, 1, .36, 1)`). These defaults also work without a Syntyr
stylesheet, and per-element CSS tokens can override them.

The CSS token `--syn-animation-iterations: 3` (or `infinite`) can
supply the JS helper's default repetition count. Explicit options win.
`stagger()` accepts repetition options; `observeReveals()` always
uses a single cycle, even when the CSS token requests looping.

```js
const running = animate(card, 'rotate', {
  loop: true, speed: 2, rotation: 360, duration: 900,
});
running?.pause();
running?.play();
running?.cancel();

animate(card, 'slide-up', {
  iterations: 3, iterationDirection: 'alternate', duration: 300,
});

// Exit effects are visual, not semantic hiding:
const exit = animate(card, 'fade-out', { duration: 220, iterations: 1 });
if (exit) exit.finished.then(() => { card.hidden = true; }).catch(() => {});
else card.hidden = true; // Reduced-motion and missing-API fallback
```

Unknown presets and invalid directions throw `TypeError`; missing target,
missing Web Animations API, or a reduced-motion preference return `null`
without modifying the DOM. Prefer `animation?.cancel()` for interruption and
`animation?.finished` when coordinating an actual transition (cancellation
rejects its promise). Animation properties are released at the end rather
than persisting a hidden or transformed element.

## Viewport reveals

```html
<section class="syn-root">
  <h2>Visible with CSS alone</h2>
  <p data-syn-reveal="enter">Animate on first viewport entry.</p>
  <p data-syn-reveal="fade">Fade when first seen.</p>
</section>
```

```js
import { observeReveals } from '/js/syntyr.animate.mjs';
const disconnect = observeReveals(document);
```

No `IntersectionObserver` is created automatically; call `observeReveals`
after rendering the relevant HTML fragment. It observes only descendants of
`.syn-root` with a `data-syn-reveal` attribute, runs each animation once,
and does **not** add `opacity: 0` to page content before JavaScript starts.
A region can be re-scanned after HTMX/Datastar/React renders new nodes.
The root argument limits the query, and the return function disconnects it.
There is no `MutationObserver` or automatic event interception.

## Accessibility and performance

- `prefers-reduced-motion: reduce` takes precedence over all presets and
  custom durations. Reduced-motion users always get visible, immediate content;
  if that preference changes while observing, animation is checked again.
- Content is never hidden while waiting for JavaScript, scroll observation,
  or native feature detection. Effects do not replace semantic HTML, focus
  management, ARIA announcements, or actual state-change notifications.
- Keyframes use composited `opacity`, `translate`, and `scale` rather than
  layout dimensions. Avoid animating essential text and high-density data,
  where fading can temporarily reduce readability. An element with custom
  individual transform properties may need a wrapper for composition.
- The module defaults to `fill: 'none'` and `iterations: 1`.
  A fade-out resets to visible CSS state unless your application
  separately removes/hides the content. Loops also use `fill: 'none'`;
  cancel long-running effects on component teardown.
- For layout changes, prefer native View Transitions where available. For
  interactive scrubbing and complex timelines, use a specialized animation
  engine *outside* Syntyr instead of expanding this low-level module.

## Verification

```sh
node --test tests/animate.test.mjs
# Optional local Chromium smoke test; install Playwright separately
python3 tests/website_animation_browser.py
python3 scripts/build.py --check
python3 -m unittest discover -s tests -v
```

Node is for the optional JavaScript behavior tests, **not** for building
Syntyr or using the CSS library. The production JS is copied byte-for-byte
by Syntyr's existing Python build, allowing deterministic release checks.


## Website animation presets (CSS only)

`syntyr.motion.css` provides **15 opt-in, non-scroll-linked website
animations**. No JavaScript or animation framework is needed. Only
elements with `data-syn-animate` animate, independently of the
`data-syn-scroll` view timeline and the optional icon animations.
These are **unreleased alpha.5 source candidate** features.

```html
<link rel="stylesheet" href="/css/syntyr.core.css">
<link rel="stylesheet" href="/css/syntyr.motion.css">
<main class="syn-root">
  <h2 data-syn-animate="fade-in">Welcome back</h2>
  <div class="syn-panel" data-syn-animate="slide-up">
    CSS-only entrance.
  </div>
  <span class="syn-badge" data-syn-animate="pulse"
        style="--syn-animation-iterations: 3;
               --syn-animation-duration: 800ms">Three pulses</span>
  <span class="syn-badge syn-animate--loop" data-syn-animate="bounce"
        aria-hidden="true"
        style="--syn-animation-duration: 1200ms;
               --syn-animation-direction: alternate">●</span>
  <span class="syn-badge syn-animate--loop"
        data-syn-animate="rotate" aria-hidden="true"
        style="--syn-animation-duration: 1.2s;
               --syn-animation-speed: 2;
               --syn-animation-rotation: -360deg">◌</span>
</main>
```

### Available effects

| Animation | Purpose |
| --- | --- |
| `data-syn-animate="fade-in"` | Gentle opacity entrance |
| `data-syn-animate="fade-out"` | Visual opacity exit |
| `data-syn-animate="slide-up"` | Move upward into place |
| `data-syn-animate="slide-down"` | Move downward into place |
| `data-syn-animate="slide-left"` | Move leftward into place |
| `data-syn-animate="slide-right"` | Move rightward into place |
| `data-syn-animate="zoom-in"` | Scale up and appear |
| `data-syn-animate="zoom-out"` | Scale down and disappear |
| `data-syn-animate="pop"` | Brief overshoot entrance |
| `data-syn-animate="bounce"` | Vertical bounce |
| `data-syn-animate="pulse"` | Gentle scale emphasis |
| `data-syn-animate="shake"` | Horizontal shake |
| `data-syn-animate="rotate"` | Complete turn, clockwise or counterclockwise |
| `data-syn-animate="rotate-in"` | Rotate gently into view |
| `data-syn-animate="flip-in"` | 3D Y-axis entrance |

### Timing and loop controls

| CSS variable | Default | Purpose |
| --- | --- | --- |
| `--syn-animation-duration` | `420ms` | Duration of each cycle |
| `--syn-animation-speed` | `1` | Positive speed multiplier: `0.5` slow, `2` fast (modern CSS typed arithmetic) |
| `--syn-animation-delay` | `0ms` | Delay before start |
| `--syn-animation-easing` | `ease-out` | Timing function |
| `--syn-animation-iterations` | `1` | Count or `infinite` |
| `--syn-animation-direction` | `normal` | `normal` / `reverse` / `alternate` / `alternate-reverse` |
| `--syn-animation-play-state` | `running` | `running` or `paused` |
| `--syn-animation-fill-mode` | `none` | Native CSS fill mode |
| `--syn-animation-distance` | `1rem` | Slide / bounce distance |
| `--syn-animation-scale` | `.94` | Zoom start or end scale |
| `--syn-animation-rotation` | `360deg` | Rotation angle; set `-360deg` for counterclockwise |

`syn-animate--loop` is shorthand for an infinite iteration count.
Set `--syn-animation-iterations: 2` or any positive CSS iteration count
to make a finite loop. Combine with
`--syn-animation-direction: alternate` to avoid abrupt jumps.
A host can pause via `--syn-animation-play-state: paused` without
shipping a Syntyr runtime. `--syn-animation-speed: 2` halves the cycle
duration; `--syn-animation-speed: 0.5` doubles it. Modern CSS engines
with typed arithmetic support the multiplier directly. Browsers without
typed CSS division retain the explicit `--syn-animation-duration`
instead. CSS users can always set that duration directly for universal
speed control. The CSS speed multiplier changes cycle duration but
does not change delay; native JavaScript playback rate changes the
animation clock (including delays).

**Accessibility:** Animations do not create a hidden baseline state.
Under `prefers-reduced-motion: reduce` all presets and loops are
disabled. `fade-out` and `zoom-out` are visual only: by default,
they return to visible state afterward, because fill is `none`.
When dismissing a dialog, button or actionable content, update the
DOM/HTML state and focus as well—opacity or
`animation-fill-mode: forwards` is not a semantic hide.
Keep infinite loops decorative and avoid moving essential text.

## Website block effects (CSS only)

Load the optional `syntyr.motion.css` stylesheet **alongside core**. These
effects can be applied to existing Syntyr Blocks, sections, React-rendered
markup, and CMS templates. No JavaScript, hydration, observer setup, or new
framework is required. This section describes the **unreleased alpha.5
candidate**, not the published alpha.4 assets.

```html
<link rel="stylesheet" href="/css/syntyr.core.css">
<link rel="stylesheet" href="/css/syntyr.motion.css">

<section class="syn-root syn-region" aria-labelledby="features-heading">
  <h2 id="features-heading" data-syn-scroll="rise">Built for clarity</h2>
  <div class="syn-grid">
    <article class="syn-panel" data-syn-scroll="fade">Feature one</article>
    <article class="syn-panel" data-syn-scroll="slide-left">Feature two</article>
    <article class="syn-panel" data-syn-scroll="zoom">Feature three</article>
    <article class="syn-panel" data-syn-scroll="slide-right">Feature four</article>
  </div>
</section>
```

`data-syn-scroll` accepts `fade`, `rise`, `slide-left`,
`slide-right`, or `zoom`. Add it to a short block or an individual
heading/card. Native CSS view timelines link animation progress to scroll
position, with short blocks completing when they have fully entered the viewport,
without JavaScript scroll handlers. Override
`--syn-block-reveal-distance` (default `1.5rem`) or
`--syn-block-reveal-scale` (default `.94`) per element.
Avoid scroll-linked opacity on long-form text or content essential to
understanding the page.

### Image parallax blocks

Apply `data-syn-parallax` to a section with a natural or explicit height.
Include one decorative media layer as a **direct child** marked
`data-syn-parallax-layer`, plus a foreground `data-syn-parallax-content`.

```html
<section class="syn-root syn-region" data-syn-parallax
         style="min-block-size: 26rem; --syn-parallax-travel: 2rem"
         aria-labelledby="parallax-title">
  <img data-syn-parallax-layer src="/images/landscape.webp"
       alt="" width="1600" height="900" loading="lazy">
  <div class="syn-site-hero" data-syn-parallax-content>
    <h2 id="parallax-title">A more engaging hero</h2>
    <p>Important content stays in normal document flow.</p>
    <a class="syn-button syn-button--primary" href="/start">Explore</a>
  </div>
</section>
```

Media is oversized and clipped inside its section. The parent defines a
native view timeline, and the media moves over its visible scroll range.
Use `--syn-parallax-travel` (default `2.5rem` each way) to keep movement
subtle. Make sure foreground text stays readable against the image; add
an overlay if needed. The layer should never contain essential content
or controls. When motion is reduced or view timelines are unsupported,
the image is **static** and all foreground content remains visible.
Avoid `background-attachment: fixed` and JavaScript scroll handlers.

### Media hover zoom and existing hover lift

```html
<a class="syn-root syn-panel" style="display: block" href="/portfolio/project" data-syn-hover="zoom">
  <img src="/images/project.webp" alt="Project preview"
       width="640" height="420" data-syn-hover-media>
  <span>Explore the project</span>
</a>
```

Use `data-syn-hover="zoom"` on an image block and
`data-syn-hover-media` on its image. Hover or keyboard focus-within
scales only the media by `--syn-hover-zoom` (default `1.06`) on
fine-pointer devices. For cards, reuse the existing
`syn-surface--lift` from `syntyr.recipes.css` instead of another
hover-lift class. You can use CSS-only scroll effects and static
Syntyr effects together, but check contrast and visual distraction.

**Fallback and accessibility:** Unsupported browsers simply show the
static blocks; no baseline CSS hides content. All new scroll, parallax,
and hover motion is disabled by `prefers-reduced-motion: reduce`.
The module never intercepts input, alters semantics, starts a timer, or
ships an animation dependency. Existing `data-syn-reveal` belongs to
the separate optional JavaScript `observeReveals()` API; it does not
control CSS-only `data-syn-scroll`.


### Animated gradient wash (composable CSS)

Use the existing static `syn-gradient-wash` from `syntyr.effects.css`.
The optional `syntyr.motion.css` adds a decorative, slowly drifting
gradient layer when `data-syn-gradient="drift"` is present. The background
remains static if motion is reduced or unsupported, and all content remains
visible. The animated layer never accepts pointer events.

```html
<link rel="stylesheet" href="/css/syntyr.core.css">
<link rel="stylesheet" href="/css/syntyr.effects.css">
<link rel="stylesheet" href="/css/syntyr.motion.css">

<section class="syn-root syn-gradient-wash" data-syn-gradient="drift"
         style="--syn-gradient-drift-duration: 16s"
         aria-labelledby="gradient-title">
  <div data-syn-gradient-content class="syn-site-hero">
    <h2 id="gradient-title">An atmospheric landing page</h2>
    <p>The content stays stationary and remains readable.</p>
  </div>
</section>
```

Keep the `data-syn-gradient-content` wrapper as a direct child for the
foreground stacking order. The animation moves only a decorative pseudo-element
with a composited `translate`, rather than repainting the entire gradient
on every frame. Use modest sections and inspect contrast against actual
photography or themes. Do not mix `data-syn-gradient` and `data-syn-parallax`
on the same element; instead nest separate wrappers.

### Text accents (no splitting or JavaScript)

```html
<section class="syn-root" aria-labelledby="text-effects-title">
  <h2 id="text-effects-title" data-syn-text="underline">
    A headline with an animated underline
  </h2>
  <p>Supporting information stays completely static.</p>
  <p class="syn-heading" data-syn-text="glint">
    A restrained shifting headline accent
  </p>
</section>
```

`data-syn-text="underline"` uses a native CSS view timeline to
transition underline color as a short heading enters. Without view timelines,
the accent underline is **static** and visible. It preserves natural line
wrapping, selectable text, and the document's accessible name.

`data-syn-text="glint"` animates a text-clipped theme gradient, when
`background-clip: text` is supported; set
`--syn-text-glint-duration` (default `9s`). Reduced motion or increased
contrast leaves the original solid text color. Forced-colors mode also
restores a solid system text color. Do not apply shifting text gradients to
essential text, body paragraphs, form labels, or critical navigation.
Check the foreground contrast in all custom themes: an animated accent
is decorative and is not guaranteed to preserve every arbitrary token
combination's contrast.

The two effects are independent of the optional JavaScript animation
companion and do not add timers, DOM cloning, inaccessible character
splitting, or component variants. They are **alpha.5 source-candidate APIs**
until included in a published Syntyr version.
