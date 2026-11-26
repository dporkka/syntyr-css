# Syntyr native SaaS starter

A standalone, MIT-licensed Expo example. The generated source belongs to your
app: there is no Syntyr npm dependency, CSS runtime, styling engine, or
requirement to keep a Syntyr repository checkout. The locked dependencies are
copied from the tested Expo SDK 58 fixture in the source candidate.

## Run

Use a Node version supported by the locked Expo / React Native versions.

```sh
npm ci
npm run typecheck
npm test
npm run export:android
npm run export:ios
npm start
```

The production Metro exports are JavaScript/Hermes bundles, not installable
APK/IPA files. Use `npm run android` with a configured Android development
environment, or `npm run ios` on macOS with Xcode and Simulator. A compatible
physical Expo Go device can connect to the development server when supported.

## Make it yours

- `src/tokens.ts`: snapshot of the canonical Syntyr native tokens (seven palettes).
- `src/styles.ts`: native styles, system appearance mapping and touch target floors.
- `src/recipes.tsx`: optional reusable native presentation components.
- `src/App.tsx`: local appearance controls and sample form.
- `src/OperationsScreen.tsx`: local dashboard, fictional client list and settings.
- `index.ts`: Expo root and safe-area provider; integrate with your host navigation
  instead of wrapping existing providers or adding insets twice.

Rename the app and slug and configure your own identifiers, icons, navigation,
backend, authentication, tenant isolation, persistence, and validation. The
sample has no real business data, authentication, network requests or persistence.
Do not treat its sample status, access or save states as authorization or data
handling. For an existing NativeWind/Uniwind application, use the copied
StyleSheet components without changing the host styling engine or package graph.

## Verification boundaries

Automated tests exercise interactive presentation behavior, appearance,
route-like local tabs, touch minimums and insets. Validate keyboard behavior,
screen readers, text scaling, safe areas, native rendering, and performance on
real Android and iOS devices before releasing.

This fixture-derived dependency graph carries the source fixture's
`minimatch` override (11.0.9) for GHSA-g3hv-75wg-m249. Test upgrades before
changing it. Residual GHSA-fc5q-39xc-vjpf affects transitive `picomatch` in
the locked graph; do not accept untrusted glob patterns and retest after an
upstream fix. Audit the app's own dependency graph before deploying.
