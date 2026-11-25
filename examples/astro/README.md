# Syntyr + Astro (opt-in)

This static Astro example imports the local `@syntyr/css` distribution.
It is **not** part of the Syntyr runtime or the hosted CSS distribution.

Requires **Node.js 22.23.4 or newer** (Node 24 LTS recommended) and a compatible
npm version, following Astro 7.4's updated minimum runtime requirements.
The Astro 5 dependency was retired because it had multiple known security
advisories. Keep this *example* on patched Astro releases.

```sh
cd examples/astro
node --version
npm install
npm run build
npm run verify
npm run preview
```

The generated static HTML needs no Syntyr JavaScript runtime. Neither
installing Astro nor using a build step is required for Syntyr consumers.

Check the Astro [upgrade guide](https://docs.astro.build/en/upgrade-astro/)
before changing major versions, and rerun the example build.

The example deliberately configures `base: '/syntyr-astro/'` and static
output, verifying that the generated CSS URL retains its deployment prefix.
Serve `dist/` under that prefix, or change `base` and the verifier argument
to match your hosting destination. The verifier rejects unexpected scripts
and missing or unprefixed stylesheets. No third-party runtime is required
by Syntyr's styles.
