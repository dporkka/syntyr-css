# Syntyr on mobile: React Native, Expo, Flutter, SwiftUI and Compose

**Status: opt-in source adapter (alpha.5 candidate), not published as a native
package.** Syntyr's web CSS does **not** execute in the native iOS or Android
renderers. The supported portable contract is **literal design tokens** from
one existing source, `src/tokens.css`. Browser-only components and behaviors
must be implemented with native controls.

| Target | Adoption route | Scope |
| --- | --- | --- |
| React Native / Expo (iOS, Android) | Copy `integrations/react-native/{tokens,styles}.ts` and optional `recipes.tsx` | Native tokens, touch-safe styles, copy-owned SaaS presentation |
| React Native Web / Expo Web | Same native style adapter for shared screens; Syntyr CSS in web-only HTML | Native `View` / `Text` do not become Syntyr HTML components |
| Flutter | Bundle `metadata/mobile/syntyr.tokens.json` as an asset | Theme data mapped to Flutter widgets |
| SwiftUI | Add the JSON asset to an Xcode target | Colors, spacing and metrics mapped to SwiftUI controls |
| Jetpack Compose | Add JSON to `src/main/assets/` | Colors and sizing mapped to Compose Material themes |
| Ionic / Capacitor (web-powered) | Load Syntyr's existing CSS normally | Full browser CSS support in the WebView; test platform-specific accessibility |
| NativeScript / .NET MAUI | Parse the same portable JSON | Custom native style bindings; no tested adapter shipped |

## Exact token contract

Run from the Syntyr repository root:

```sh
python3 scripts/export_mobile_tokens.py
python3 scripts/export_mobile_tokens.py --check
python3 -m unittest discover -s tests -p test_mobile_adapters.py -v
```

The generated files are:

- `metadata/mobile/syntyr.tokens.json`: all seven named Syntyr palettes,
  with 13 literal SRGB color roles each, per-palette `radius`/`cut`,
  shared spacing `1–5`, font sizes `xs/sm/base`, body line-height multiplier,
  and control height.
- `integrations/react-native/tokens.ts`: the **same values** as a standalone
  typed `as const` module, with `SyntyrMobileTheme`.
- `integrations/react-native/styles.ts`: a small, copy-owned native recipe
  that uses those generated tokens. It is not a new component library.
- `integrations/react-native/recipes.tsx`: optional copy-owned React Native
  presentation for metrics, statuses, fields, navigation tabs, records,
  actions and empty/error/loading states. Only React and native controls;
  no required styling engine, navigation library or browser runtime.
- `integrations/react-native/tailwind/<palette>.css`: one optional generated
  Tailwind v4 theme per palette, containing literal native-compatible values.
  Choose exactly one at build time.

Unit `logical-points` means the generator converts Syntyr's literal CSS
`rem` values using the explicit **16px browser baseline** (for example,
`0.75rem -> 12`). In a native UI, treat the numbers as dp on Android,
points on iOS, or logical pixels in Flutter. This is a **design scale
mapping**, not a promise of identical physical size, font metrics or dynamic
type behavior. Native consumers must adapt to accessibility font scaling,
platform text metrics and user device settings. Colors do not automatically
follow system appearance; select the desired palette.

Only literal values are exported. Derived `color-mix()`, runtime CSS
variables, hover, grid, container queries, viewport-relative typography,
motion and browser focus semantics **are deliberately excluded**. Do not
parse `dist/syntyr.core.css` at runtime or use a WebView solely to get
Syntyr-native styling.

## React Native / Expo: copy-owned, no adapter dependency

In an Expo or bare React Native app, copy both `integrations/react-native/*.ts`
files into `src/theme/`, then use:

```tsx
import { Pressable, StyleSheet, Text, View } from "react-native";
import { createSyntyrNativeStyles } from "./theme/styles";

const styles = StyleSheet.create(createSyntyrNativeStyles("studio"));

export function Example() {
  return (
    <View style={styles.panel}>
      <Text accessibilityRole="header" style={styles.heading}>Account</Text>
      <Pressable accessibilityRole="button" style={styles.button}>
        <Text style={styles.buttonLabel}>Continue</Text>
      </Pressable>
    </View>
  );
}
```

See [the interactive native screen](../examples/react-native/App.tsx) for an
email field, a stateful button and a system/light/dark palette chooser.
`resolveSyntyrNativeTheme(preference, useColorScheme())` resolves `auto` to
Studio in light mode or when appearance is unavailable, and Grid in dark
mode (matching the web auto palette); explicit named palettes win. The demo
keeps preference in local component state; persistence is host-owned.
Pass `Platform.OS` as the optional second argument to
`createSyntyrNativeStyles` for 48dp Android and at least 44pt iOS control
heights. Native text scaling remains enabled. The style recipes also include
badge surfaces and text, semantic success/error text, and pressed/disabled
button presentation. Apply disabled styles only together with `disabled`
and the corresponding accessibility state. Use status words or icons with
semantic colors rather than relying on color alone.
The example is **source to copy into an existing app**,
not a separate installable Expo project; in the app, adjust relative imports.
A separate [Expo SDK 58 development smoke fixture](https://github.com/dporkka/syntyr-css/tree/main/examples/expo-native-smoke)
is provided for reproducible native TypeScript, Jest/RNTL interaction tests,
and production Android/iOS Metro bundle exports. Run `npm ci`,
`npm run typecheck`, `npm test`, `npm run export:android`, and
`npm run export:ios` from that fixture. **Metro exports do not run on
devices or produce signed native binaries**; simulator/hardware checks are
still required. The fixture imports the canonical adapter by an ignored
build-local source copy, not a second design-system implementation.
Use the host application's safe-area provider and navigation system as usual.
The example uses real `TextInput` and `Pressable` controls with accessibility
labels; gestures, screen reader behavior, validation, keyboard handling and
focus management remain the native application's responsibility.

Do **not** import `@syntyr/css`, `syntyr.core.css` or `syn-*` classes into
Android/iOS React Native screens. An Expo Web or React Native Web route can
load Syntyr CSS in **web-only markup**, or use the token adapter for shared
native components. Syntyr does not require NativeWind, Uniwind, Tamagui or
Restyle. If your application already uses a CSS-to-native system, feed it the
token values explicitly; don't assume Syntyr selectors, pseudo-classes or
browser layout features will be compiled correctly.

## Native SaaS workspace recipes

Copy [recipes.tsx](../integrations/react-native/recipes.tsx) alongside the
generated tokens and styles. The
[operations workspace example](../examples/react-native/OperationsScreen.tsx)
composes seven native presentation recipes into a dashboard, searchable
client list, and settings form. The existing sample app opens it from
"Open SaaS workspace"; copy both example screens if using that entrypoint.
All counts and records are fictional; search, selection, and save feedback
are local state only. There are no network calls, real account mutations,
or navigation dependencies.

```tsx
import React, { useMemo } from "react";
import { Platform, StyleSheet, View } from "react-native";
import { createSyntyrNativeStyles } from "./theme/styles";
import { NativeAction, NativeMetric, NativeStatus } from "./theme/recipes";

export function Dashboard({ onOpen }: { onOpen: () => void }) {
  const styles = useMemo(
    () => StyleSheet.create(createSyntyrNativeStyles("studio", Platform.OS)),
    [],
  );
  return (
    <View style={styles.stack}>
      <View style={styles.metricGrid}>
        <NativeMetric styles={styles} label="Open proposals" value="7" />
        <NativeMetric styles={styles} label="Tasks due" value="4" />
      </View>
      <NativeStatus styles={styles} tone="warning" label="Needs review" />
      <NativeAction styles={styles} label="Review proposals" onPress={onOpen} />
    </View>
  );
}
```

Other recipes expose real native roles and host-owned callbacks:

| Recipe | Responsibility |
| --- | --- |
| NativeAction | Pressable, disabled/busy accessibility state, primary/secondary appearance |
| NativeMetric / NativeStatus | Native text, semantic role colors and wrap-friendly metrics |
| NativeField | Controlled input, visible label, hint/error text |
| NativeTabs | Selected tab semantics, callback to host navigation |
| NativeRecord | Read-only content or genuine Pressable; explicit status words |
| NativeState | Empty, loading or error content; retry/clear only when supplied |

Use a host SafeAreaProvider and pass its inset values as the optional third
argument to `createSyntyrNativeStyles(theme, Platform.OS, insets)`, or let
host navigation supply inset padding instead, never both. The Expo fixture
pins Expo-compatible `react-native-safe-area-context` **only in the test app**
and injects those values into the copy-owned example. With explicit insets,
the fixture disables automatic scroll insets. Native scroll/list headers
remain scrollable at larger text sizes. Host apps still own keyboard and
focus recovery, input validation, persistent storage, access control and
navigation.

The optional Expo Jest fixture exercises the workspace interactions, all
palettes, touch target floors, insets, and state semantics; automated native
component tests do not certify physical rendering or screen readers.

## Optional Tailwind v4 native theme bridge

For an app already using [Uniwind](https://uniwind.dev/) or
[NativeWind v5](https://www.nativewind.dev/v5), copy one generated
[palette file](https://github.com/dporkka/syntyr-css/tree/main/integrations/react-native/tailwind)
into its app-owned CSS entrypoint directory. These files are experimental
source adapters, not npm modules. NativeWind v4 (Tailwind v3) is not a target.
Use the styling engine's own Expo/Metro configuration and installation guide.

Uniwind entrypoint:

```css
@import "tailwindcss";
@import "uniwind";
@import "./studio.css";
```

Configure Metro with `withUniwindConfig(getDefaultConfig(__dirname),
{ cssEntryFile: "./global.css" })` from `uniwind/metro`.

NativeWind v5 (release candidate) entrypoint:

```css
@import "tailwindcss/theme.css" layer(theme);
@import "tailwindcss/preflight.css" layer(base);
@import "tailwindcss/utilities.css";
@import "nativewind/theme";
@import "./studio.css";
```

Configure Metro with `withNativewind(getDefaultConfig(__dirname))` from
`nativewind/metro`. Import the entrypoint once from the host's root module.
Install each engine and all of its required peers in the host app; do not
combine two Metro wrappers or install the vendor packages in Syntyr core.
Never load Syntyr browser CSS or import several palette files together. The generated `@theme`
block declares namespaced literal colors, spacing, text sizes, control size
and radius; it does not redefine Tailwind defaults, import browser selectors,
or include runtime theme switching.

```tsx
import { View, Text, Pressable } from "react-native";

export function CampaignCard({ onOpen }: { onOpen: () => void }) {
  return (
    <View className="bg-syntyr-surface border border-syntyr-frame rounded-syntyr p-syntyr-3">
      <Text className="text-syntyr-text text-syntyr-base">Campaign performance</Text>
      <Pressable accessibilityRole="button" onPress={onOpen}
        className="bg-syntyr-accent rounded-syntyr min-h-syntyr-control android:min-h-[48px] items-center justify-center">
        <Text className="text-syntyr-on-accent text-syntyr-sm">Open details</Text>
      </Pressable>
    </View>
  );
}
```

These names are generated and covered by the Tailwind v4 compiler smoke, not a claim all
native properties or selectors work on every engine/version. Keep class
names statically discoverable; use the host's documented platform variants
and safe-area provider. For example, in an app already using
`react-native-safe-area-context`, use `useSafeAreaInsets()` inside its
provider and apply the insets to the screen container's padding; do not
apply the same inset twice when navigation already handles it.
The static bridge imports one palette at build time;
for runtime palette switching use the existing `StyleSheet` adapter or the
vendor's documented variable/theme API with the generated JSON/TS values.
Use the vendor's version-specific configuration rather than attempting to
compile Syntyr CSS or emulate DOM inheritance. Host dependencies, navigation,
focus handling, keyboard behavior, and native release builds remain app-owned.

To validate utility generation locally, install the existing optional
[example's Tailwind toolchain](https://github.com/dporkka/syntyr-css/tree/main/examples/tailwind-v4)
and run `npm run check:native-palettes` there. This compiles every named
palette and checks the utility-to-token mappings; it does not run Metro.

For an initial **bundle-size** comparison, use an identical simple screen
with production Hermes exports and report raw bytes by platform. The
fixture's optional `npm run report:bundle-size -- android
stylesheet=/path/to/baseline uniwind=/path/to/uniwind
nativewind=/path/to/nativewind` command hashes and measures only Expo's
platform-specific JS/Hermes bundles. Use the paths to the exported
directories; the first case is the baseline. Compare only matching bundle
formats. It does not measure APK/IPA size, memory or runtime performance.

Before rollout, compare identical screens using the same pinned Expo/RN
versions, device, production bundle mode, and palette. Measure cold start,
theme-change latency, large-list frame timing and bundle bytes; record median
and p95 across repeated runs. Do not infer native performance from web CSS
size or vendor marketing benchmarks.

## Flutter

Declare the copied JSON under `flutter/assets/syntyr.tokens.json` in
`pubspec.yaml`:

```yaml
flutter:
  assets:
    - assets/syntyr.tokens.json
```

In Dart, load once and build the palette for your widgets:

```dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;

Future<ThemeData> loadSyntyrTheme(String name) async {
  final root = jsonDecode(await rootBundle.loadString(
    'assets/syntyr.tokens.json')) as Map<String, dynamic>;
  final theme = (root['themes'] as Map<String, dynamic>)[name] as Map;
  final colors = theme['colors'] as Map;
  Color color(String role) =>
      Color(int.parse('FF${(colors[role] as String).substring(1)}', radix: 16));
  return ThemeData(
    scaffoldBackgroundColor: color('bg'),
    colorScheme: ColorScheme.fromSeed(
      seedColor: color('accent'),
      surface: color('surface'),
      onSurface: color('text'),
    ),
    cardColor: color('surface'),
  );
}
```

`ColorScheme.fromSeed` computes unspecified Material roles rather than
duplicating all Syntyr roles; map `muted`, `frame`, `danger`, and
`on-accent` explicitly for exact custom widget colors.

## SwiftUI

Bundle the JSON in the app target, parse it with `JSONSerialization` or
`Decodable`, then convert RGB hex to SwiftUI `Color`. For example:

```swift
import SwiftUI

func syntyrColor(_ hex: String) -> Color {
    let value = UInt64(hex.dropFirst(), radix: 16)!
    return Color(
        .sRGB,
        red: Double((value >> 16) & 0xff) / 255,
        green: Double((value >> 8) & 0xff) / 255,
        blue: Double(value & 0xff) / 255,
        opacity: 1
    )
}

// Given the selected palette's "colors" dictionary:
// Text("Account").foregroundStyle(syntyrColor(colors["text"]!))
```

Use semantic native accessibility roles and dynamic type; a fixed design
font size is not a substitute for the user's preferred text size.

## Android Jetpack Compose

Add the JSON to `app/src/main/assets/syntyr.tokens.json`, load it through
`context.assets.open(...)`, and read `themes[themeName].colors`.
For example, once `hex` is read from the JSON:

```kotlin
import androidx.compose.ui.graphics.Color

val syntyrSurface = Color(android.graphics.Color.parseColor(hex))
```

In your Compose theme, map the named palette roles to `MaterialTheme`
`colorScheme` fields; keep user font scaling and touch-target conventions.
This is a token import route, **not** a verified Compose UI toolkit.

## Ionic / Capacitor

Ionic and Capacitor usually render HTML/CSS inside a WebView, so use the
existing `dist/syntyr.core.css` on HTML nodes within a `.syn-root`:

```html
<link rel="stylesheet" href="/assets/syntyr.core.css">
<main class="syn-root" data-syn-theme="studio">
  <button class="syn-button syn-button--primary" type="button">Continue</button>
</main>
```

Ionic components may use Shadow DOM; ordinary external selectors do not
cross shadow roots. Prefer styling Syntyr-owned HTML, or the Ionic component's
documented CSS custom properties/parts. Respect safe areas, on-screen
keyboards and touch interactions.

## Boundary and maintenance policy

- One authored source: `src/tokens.css`. All native tokens are generated,
  deterministic and checked by `--check`. No second hand-maintained theme.
- The CSS package's exports and zero-dependency core are **unchanged**.
  Native consumers copy only the files they need; no React, Expo, Flutter,
  Swift or Compose dependencies are added to Syntyr.
- Runtime controls remain genuinely native. Native keyboard navigation,
  gesture handling, accessibility and OS adaptations are not made equivalent
  by colors or spacing alone.
- Python contract tests verify deterministic exports. The separate Expo fixture
  supports native component tests and Metro exports, not device/simulator
  certification. NativeWind and Uniwind have separate version and runtime
  requirements; validate them on real iOS/Android devices before rollout.

References: [React Native styles](https://reactnative.dev/docs/style.html),
[Expo Web](https://docs.expo.dev/workflow/web/),
[Expo CSS limitations](https://docs.expo.dev/versions/v55.0.0/config/metro/).
