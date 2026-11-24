# ASCII effects (optional)

Source candidate only (alpha.5); not available in published alpha.4. Load core, symbols, then ASCII effects. For an npm package built from this candidate:

```html
<link rel="stylesheet" href="dist/syntyr.core.css">
<link rel="stylesheet" href="dist/syntyr.symbols.css">
<link rel="stylesheet" href="dist/syntyr.ascii.css">
```

For a plain HTML site, copy the installed CSS files from the package’s `node_modules/@syntyr/css/dist/` directory into the served `dist/` directory (or adjust the URLs to your public asset path). npm installation does not serve files automatically. In a bundler, import the package CSS instead. Or import `@syntyr/css/ascii.css` alongside core and symbols. The selective build accepts `--modules symbols,ascii`. The all bundle includes both; core and cinematic preset remain unchanged.

[Open the interactive generator and image converter](../tools/ascii-playground.html) (optional site-only JavaScript; exports are static). The generator supports ordered Bayer and Floyd–Steinberg dithering, custom glyph ramps and a five-row original text logo alphabet. [Copy three CSS-only hero sections](../examples/ascii-heroes.html). [Open the ASCII effects lab](../examples/ascii.html) for original, copyable character art. CSS only styles literal DOM text; it does not generate random characters, calculate a chart, perform real typing, decode text, or convert media. Use existing symbols for geometry and native progress or textual equivalents for status.

```html
<div class="syn-root" data-syn-theme="grid">
  <p>System online</p>
  <pre class="syn-ascii syn-ascii--compact syn-ascii--phosphor syn-ascii--scan"
       aria-hidden="true" tabindex="-1">[#####.....] 50%</pre>
  <p>Example completion: 50%</p>
</div>
```

| Modifier | Purpose |
| --- | --- |
| `syn-ascii--compact` | Compact character-cell typography |
| `syn-ascii--phosphor` | Theme-aware text and glow; respects intensity's glow token |
| `syn-ascii--gradient` | Decorative diagonal fade |
| `syn-ascii--dither` | Decorative opacity for literal character-density textures |
| `syn-ascii--scan` | Decorative horizontal scanline mask |
| `syn-ascii--banner` | Accent-colored, bold text art |
| `syn-ascii--cursor` | Static terminal block cursor |
| `syn-ascii--typewriter` | One-shot stepped visual reveal |
| `syn-ascii--wave` | One-shot vertical movement of a field |
| `syn-ascii--rain` | One-shot entrance of a precomputed character stream |
| `syn-ascii--decode` | One-shot stepped letter-spacing reveal; not character substitution |
| `syn-ascii--loader` | One-shot rotation of a supplied symbol; not an application loading state |

Use `--syn-ascii-color`, `--syn-ascii-font-size`, `--syn-ascii-line-height`, `--syn-ascii-spacing`, `--syn-ascii-opacity`, `--syn-ascii-duration` and `--syn-ascii-steps` on the root or artwork as appropriate. Use positive durations and step counts. Effects are static unless a motion modifier is explicitly attached to an element marked `aria-hidden="true"`; motion lasts no longer than five seconds and does not repeat. Reduced motion, forced colors, increased contrast and print disable motion, masks, and glow.

Keep meaningful text visible outside decorative art. Avoid focusable children inside hidden art. Keep scrollable meaningful code outside these decorative patterns; never replace actual progress, errors or status with a character image. Quiet intensity turns off the phosphor glow via the existing token; omit decorative motion classes for quiet application surfaces. Do not stack multiple motion or masking modifiers; each owns a single CSS property.

For new designs, compose existing `syn-ascii`, geometric frames, theme tokens and semantic HTML before adding a modifier. This module adds only treatments not supplied by the existing alignment and panel utilities. Procedural animation, real text scrambling and media conversion are deferred to optional tooling.

## Optional build-time ASCII CLI

From a checkout of this source candidate, with Node.js 22 or later, run the dependency-free CLI. It reuses the playground's deterministic renderer and export logic. It is a source-checkout tool, not part of the published npm CSS package or browser runtime.

```sh
node scripts/ascii.mjs --help
node scripts/ascii.mjs pattern torus --columns 80 --rows 24 --ramp blocks --time 1 > torus.txt
node scripts/ascii.mjs logo SYNTYR --style hash --format svg > wordmark.svg
node scripts/ascii.mjs image photo.ppm --columns 80 --dither floyd --format html > photo.html
```

The image command reads local 8-bit Netpbm PGM/PPM files (P2, P3, P5, P6), up to 16 MiB and four million source pixels. For PNG, JPEG and WebP, use the browser playground or convert locally to PGM/PPM with an existing image editor. The CLI does not install a decoder or fetch URLs. It writes artwork to stdout and diagnostics to stderr; invalid input exits nonzero. HTML output starts with a UTF-8 BOM for saved documents. SVG and HTML are escaped, use a validated solid hex color, and need no JavaScript. As with the browser tool, glyph-cell aspect and intensity are approximations.

Use these commands for static sites, README banners and reproducible build steps. Keep ordinary text alternatives for meaningful artwork. The CSS package has no CLI or Node dependency.

## 3D procedural artwork

The optional generator and build-time CLI include perspective-projected torus, sphere and cube meshes with a per-character depth buffer and directional lighting. The wireframe cube intentionally shows its rear edges. Select **3D torus**, **3D sphere**, **3D cube** or **3D wireframe cube** in the playground. The original two-dimensional sphere and torus remain available. The sphere is rotationally symmetric, so its rotation is less apparent than that of the cube or torus.

The renderer is bounded to 160 columns by 100 rows, uses fixed low-resolution meshes, and has no WebGL, external assets or dependency. It shares the existing opt-in five-second animation and static export controls; reduced-motion settings disable playback. The following reproducible CLI command renders a single frame:

```sh
node scripts/ascii.mjs pattern torus-3d --columns 80 --rows 30 --time 1.5 --format svg > torus.svg
```

## Full-color ASCII image conversion

Select **Preserve image RGB colors** after choosing a local image. Character density still follows luminance, inversion and the selected dithering method; each glyph receives the original sampled RGB color composited against black. Inversion changes density, not hue. Color is an approximation at the selected character resolution, not a pixel-accurate reproduction.

- TXT preserves characters only; color is intentionally omitted.
- HTML uses consecutive equal-color spans and escaped text.
- SVG uses colored text spans; no scripts or remote assets.
- ANSI truecolor uses standard 24-bit foreground SGR sequences, with a reset at the end of every row. Open the file in a truecolor-capable terminal (preferably with a dark background); ordinary text editors may show escape sequences. ANSI also supports the single selected color for patterns and logos.

The source-checkout CLI accepts the same image-color option:
```sh
node scripts/ascii.mjs image photo.ppm --columns 100 --image-colors --dither floyd --format svg > photo.svg
node scripts/ascii.mjs image photo.ppm --image-colors --format ansi > photo.ansi
cat photo.ansi
```

The existing grid and file-size bounds remain unchanged. No image uploads, package changes or runtime dependencies.

## Optional interactive ASCII companion

[Try five interactive effects](../tools/ascii-interactive.html): pointer-driven 3D orbit, particles, wave distortion, radar and scroll transitions. Copy the source candidate's two files, [ascii-interactive.mjs](../tools/ascii-interactive.mjs) and [ascii-logic.mjs](../tools/ascii-logic.mjs), into the same served directory. This optional ESM companion is not part of the npm CSS package.

Supply a container, a decorative plain-text pre element, and a native toggle button. The button is initially disabled in static HTML and becomes available only when the companion initializes. Keep meaningful content outside the artwork.

```html
<section id="hero" class="syn-root">
  <h2>Build beyond the ordinary</h2>
  <button type="button" aria-pressed="false" disabled>Enable or disable effect</button>
  <pre aria-hidden="true" tabindex="-1">.:-=+*#%@</pre>
</section>
```

In your own external module:

```js
import {attachAsciiEffect} from './ascii-interactive.mjs';
const root = document.querySelector('#hero');
const effect = attachAsciiEffect({
  root, art: root.querySelector('pre'),
  button: root.querySelector('button'),
  kind: 'orbit', cols: 64, rows: 24
});
// Call effect.destroy() when unmounting.
```

Kinds are orbit, particles, distortion, radar and scroll. The controller uses event-driven rendering at approximately 12 FPS maximum, with no perpetual animation loop. It restores the static fallback when disabled, when the page becomes hidden or when reduced motion, forced colors or increased contrast becomes active. Touch pointer movement is ignored. Scroll effects require activation. Maximum grid is 80 by 32 cells. No network calls, trackers, mandatory JavaScript or new public CSS classes.
