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

The fixture also pins affected `glob` versions (9.0.0–14.0.1) to
**14.0.2**, fixing [GHSA-3g3m-2fjr-6pw4](https://github.com/advisories/GHSA-3g3m-2fjr-6pw4)
in the Jest development toolchain. Leave the unrelated `glob` 7.x copy outside
this override's scope. This is a major-version compatibility override: remove
it once the parent packages resolve a patched version without an override.
Repeat `npm test -- --coverage` to exercise Jest's coverage file matching as
well as the other fixture checks before accepting a lockfile update.

The previously documented [picomatch advisory GHSA-fc5q-39xc-vjpf](https://github.com/advisories/GHSA-fc5q-39xc-vjpf)
was withdrawn by the GitHub Advisory Database on November 18, 2026,
because it was not considered a security issue. This is not a patched-version
claim. Continue to avoid untrusted glob patterns in build and test tooling.

Run `npm audit --package-lock-only --ignore-scripts --audit-level=moderate`
in the fixture when refreshing the lockfile. The November 26, 2026 patched
lock audit returned zero vulnerabilities; that is a point-in-time result,
not a claim that future advisories cannot affect the Expo/Jest graph.

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
