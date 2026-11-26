# Historical Expo 54 / NativeWind 4 coexistence probe

An isolated compatibility experiment for apps that already use NativeWind 4
and Tailwind 3. It is **not** a new supported Syntyr utility bridge, an
alternative production starter, a migration or an endorsement of the
older dependency graph.

The test extends the standalone Syntyr starter with a host-owned NativeWind
`className` label and the unchanged Syntyr `StyleSheet`-based sample screens.
The host keeps its Tailwind configuration. No `@theme` files or browser CSS
are imported. Only the test in the canonical smoke fixture has a stable
native wrapper around the root across rerenders for RNTL 13/14 compatibility.

## Repeat the experiment

Run from the Syntyr source checkout with Node/npm and Python installed.
Use a new disposable directory. This probe resolves dependencies afresh
from the directly pinned manifest; unlike the SDK 58 starter it does
not provide a maintained or audited transitive lockfile.

```sh
python3 scripts/export_native_starter.py --output ../sdk54-probe
cp -R examples/native-sdk54-coexistence/overlay/. ../sdk54-probe/
cd ../sdk54-probe
# The SDK 58 lock no longer describes the intentionally different probe.
rm package-lock.json
npm install --no-audit --no-fund
npm run typecheck
npm test
npm exec -- tailwindcss -i global.css -o dist/host.css
npm run export:android
npm run export:ios
```

Retain the locally generated lock if comparing repeated experiments.
For application development, never replace an existing lock/config with
this overlay; instead copy the required native token, style and recipe
files into the app, use its existing providers and navigation, and audit
its actual dependency graph. Use the host's existing styling approach.
The Tailwind v4 files for Uniwind and NativeWind 5 are not for this stack.

## Observations (2026-11-26)

| Direct dependency | Tested version |
| --- | --- |
| Expo | 54.0.37 |
| React Native | 0.81.5 |
| React | 19.1.0 |
| NativeWind | 4.2.3 |
| Tailwind CSS | 3.3.2 |
| React Native Reanimated / Worklets | 4.1.1 / 0.5.1 |
| React Native Safe Area Context | 5.6.0 |
| RNTL / jest-expo | 13.3.3 / 54.0.18 |
| Jest / TypeScript | 29.7.0 / 5.9.3 |
| Node / npm | 24.22.3 / 11.19.1 |

- TypeScript passed.
- Three test suites / 24 tests passed, including the host label and
  Syntyr workspace navigation and filtering.
- Tailwind emitted the host background, padding and text utilities.
- Production Metro bundled Android and iOS successfully using the host
  NativeWind configuration.

These are source, test-runner and JS bundle results from a Linux environment,
not native view rendering, CSS interop runtime styling, native builds, startup
or accessibility certification. This is an isolated experiment, not evidence
from any production app. The older stack should not be selected for a new
application solely on this basis.

NativeWind's [v4 setup documentation](https://www.nativewind.dev/docs/getting-started/installation)
and [Expo SDK 54 reference](https://docs.expo.dev/versions/v54.0.0/) describe
the host configuration/version boundaries. These pins reflect the experiment,
not the latest versions or current recommendations.
