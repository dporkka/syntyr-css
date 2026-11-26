import React from "react";
import { registerRootComponent } from "expo";
import { SafeAreaProvider, initialWindowMetrics, useSafeAreaInsets } from "react-native-safe-area-context";
import App from "./src/App";
import type { SyntyrNativeInsets } from "./src/styles";

function InsetAwareApp() {
  const insets = useSafeAreaInsets();
  return React.createElement<{ insets?: SyntyrNativeInsets }>(App, { insets });
}

function Root() {
  return React.createElement(SafeAreaProvider, { initialMetrics: initialWindowMetrics }, React.createElement(InsetAwareApp));
}

registerRootComponent(Root);
