# Initial Studio campaign-card bundle-size experiment

Single-screen development experiment, November 26, 2026. No device renderer
or signed binary was exercised. Results are raw production Hermes JavaScript
bundle bytes in an isolated Expo SDK 58.0.25 / RN 0.88.1 test, not universal
vendor overhead or a runtime comparison. Each style engine uses its app-owned
dependencies; NativeWind v5 required the Expo-compatible Reanimated,
Worklets and safe-area peers. Both vendor cases used Tailwind CSS 4.3.5 and
the exact generated Studio palette bridge.

| Case | Android bytes | iOS bytes |
| --- | ---: | ---: |
| StyleSheet (baseline) | 1,491,160 | 1,486,194 |
| Uniwind 1.14.0 | 1,773,142 (+18.91%) | 1,772,362 (+19.26%) |
| NativeWind 5.0.0-rc.1 / react-native-css 3.1.0-rc.1 | 2,874,007 (+92.74%) | 2,869,087 (+93.05%) |

Use the same blank Expo fixture versions and production Hermes settings for
each isolated app. Do not install either styling engine into the CSS core.
Keep all example copy, structure, token choices, and target sizes the same.
The following static card has no real action handler; it is a bundle
measurement specimen, not a usable screen.

Baseline entrypoint component (the token values are from Studio at the
measured source revision; use the corresponding generated palette):

```tsx
import { Platform, View, Text, Pressable, StyleSheet } from "react-native";

const styles = StyleSheet.create({
  panel: { backgroundColor: "#ffffff", borderWidth: 1, borderColor: "#b8c6d8", borderRadius: 4, padding: 18 },
  text: { color: "#15233a", fontSize: 16 },
  button: { backgroundColor: "#2458c6", borderRadius: 4,
    minHeight: Platform.OS === "android" ? 48 : 44,
    alignItems: "center", justifyContent: "center" },
  label: { color: "#ffffff", fontSize: 14 },
});

export default function App() {
  return (
    <View style={styles.panel}>
      <Text style={styles.text}>Campaign performance</Text>
      <Pressable accessibilityRole="button" style={styles.button}>
        <Text style={styles.label}>Open details</Text>
      </Pressable>
    </View>
  );
}
```

Both utility adapters use this same isolated app component:

```tsx
import "../global.css";
import { View, Text, Pressable } from "react-native";

export default function App() {
  return (
    <View className="bg-syntyr-surface border border-syntyr-frame rounded-syntyr p-syntyr-3">
      <Text className="text-syntyr-text text-syntyr-base">Campaign performance</Text>
      <Pressable accessibilityRole="button"
        className="bg-syntyr-accent rounded-syntyr min-h-syntyr-control android:min-h-[48px] items-center justify-center">
        <Text className="text-syntyr-on-accent text-syntyr-sm">Open details</Text>
      </Pressable>
    </View>
  );
}
```

Configure each vendor separately using the
[mobile integration guide](../../../docs/mobile-frameworks.md).
Export Android and iOS into separate output directories with
`npx expo export --clear --platform android --output-dir dist/android` and
the corresponding iOS command. Use the
[bundle report](../README.md#compare-identical-screen-bundle-sizes) against
those output directories.

These bundles are deliberately tiny-screen evidence. Different screens,
dependency graphs, dynamic theming, animations and release tooling change
results. Measure startup, theme-change latency and scrolling frame timing
on the same physical target or emulator with repeated production builds;
do not infer any of those from these sizes.
