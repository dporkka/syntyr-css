# Syntyr on mobile: React Native, Expo, Flutter, SwiftUI and Compose

**Status: opt-in source adapter (alpha.5 candidate), not published as a native
package.** Syntyr's web CSS does **not** execute in the native iOS or Android
renderers. The supported portable contract is **literal design tokens** from
one existing source, `src/tokens.css`. Browser-only components and behaviors
must be implemented with native controls.

| Target | Adoption route | Scope |
| --- | --- | --- |
| React Native / Expo (iOS, Android) | Copy `integrations/react-native/{tokens,styles}.ts` | Native colors, spacing, fonts, basic surface/input/button style objects |
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
  shared spacing `1–5`, font sizes `xs/sm/base`, and control height.
- `integrations/react-native/tokens.ts`: the **same values** as a standalone
  typed `as const` module, with `SyntyrMobileTheme`.
- `integrations/react-native/styles.ts`: a small, copy-owned native recipe
  that uses those generated tokens. It is not a new component library.

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
email field, a stateful button and a light/dark palette switch based on
`useColorScheme()`. The example is **source to copy into an existing app**,
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
- Native builds have **not** been run by the Syntyr test suite; token/adapter
  contract tests are run in CI or locally. Validate a real iOS/Android app
  before claiming full platform certification.

References: [React Native styles](https://reactnative.dev/docs/style.html),
[Expo Web](https://docs.expo.dev/workflow/web/),
[Expo CSS limitations](https://docs.expo.dev/versions/v55.0.0/config/metro/).
