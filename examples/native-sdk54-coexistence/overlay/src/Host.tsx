import React from "react";
import { Text, View } from "react-native";
import App from "./App";
import type { SyntyrNativeInsets } from "./styles";

export default function Host({ insets }: { insets?: SyntyrNativeInsets }) {
  return (
    <View style={{ flex: 1 }}>
      <Text className="bg-blue-700 text-white p-2">Host NativeWind styling</Text>
      <App insets={insets} />
    </View>
  );
}
