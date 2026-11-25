# Syntyr × Expo native smoke fixture (SDK 58)

This is an **optional test application**, not an installation requirement for
Syntyr or an Expo package published to npm. It exercises the real React Native
components and generated Syntyr theme adapter without loading browser CSS.

The pinned versions originate from the official Expo
`blank-typescript@sdk-58` template, with development-only Jest and native
testing-library dependencies.

## Run the checks

From `examples/expo-native-smoke`:

```sh
npm ci
npm run typecheck
npm test
npm run export:android
npm run export:ios
```

The `sync` step runs before each check. It copies the **canonical** files in
`../../integrations/react-native/` into ignored `src/`, along with the
copy-owned `../react-native/App.tsx` screen. Never edit the generated files.

- `npm test` uses `jest-expo` and React Native Testing Library to verify
  accessible native `TextInput`/`Pressable` interactions and all seven
  Syntyr palette mappings.
- `npm run typecheck` checks the screen and adapter against Expo's real
  TypeScript / React Native types.
- The two `expo export` commands execute Metro's **production JavaScript
  bundler** for the Android and iOS platforms. They do **not** produce an
  installable APK or IPA and do not exercise the platform renderers.

To launch on an actual Android device or emulator, first install and configure
the Android SDK, JDK and an Android emulator or USB device, then:

```sh
npm run android
```

To launch on an actual iOS Simulator, use **macOS with Xcode** and an iOS
Simulator, then:

```sh
npm run ios
```

Expo Go on a physical compatible device can also connect to the development
server. Always verify native semantics, screen readers, text scaling, focus,
software keyboard and safe areas on real devices before calling the adapter
production-ready.

## Dependency security boundary (November 2026)

This optional Expo/Jest development fixture pins the transitive
`minimatch` dependency to **11.0.9** using a fixture-local npm override.
Several upstream tools otherwise select affected 9.x/10.x versions under
[GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249).
This is a major-version override; after modifying this graph, repeat
`npm ci`, `npm run typecheck`, `npm test`, and both platform export checks.

**Residual issue:** [GHSA-fc5q-39xc-vjpf](https://github.com/advisories/GHSA-fc5q-39xc-vjpf)
affects `picomatch` through its current 4.0.7 release, with no patched
npm version available at this review date. Expo, React Native, and Jest
pull it transitively. Do not accept untrusted glob patterns in fixture
build or testing scripts; upgrade and retest promptly when upstream ships
an actual fix. The high-severity advisory is **not resolved** by the
`minimatch` override.

## Scope and maintenance

The fixture must not modify `@syntyr/css` dependencies, exports or core CSS.
No native styling runtime is shipped to CSS users. Syntyr's canonical
`src/tokens.css` remains the only palette/spacing source of truth. The
generator produces `integrations/react-native/tokens.ts`, and this fixture's
`sync` script copies it unchanged.

A CI runner **without** Android SDK, Xcode or hardware should report only
TypeScript, Jest and platform **bundle** verification. Do not label an Expo
export as a successful device or simulator smoke test.

See [the mobile framework integration guide](../../docs/mobile-frameworks.md)
for Flutter, SwiftUI, Compose and Ionic/Capacitor boundaries.
