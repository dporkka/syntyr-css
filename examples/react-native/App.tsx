/** Copy into an Expo or React Native app; adjust imports to copied adapter files. */
import React, { useMemo, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View, useColorScheme } from "react-native";
import { createSyntyrNativeStyles } from "../../integrations/react-native/styles";
import { syntyrMobileTokens, type SyntyrMobileTheme } from "../../integrations/react-native/tokens";

export default function App() {
  const systemTheme = useColorScheme();
  const [submissions, setSubmissions] = useState(0);
  const [email, setEmail] = useState("");
  const theme: SyntyrMobileTheme = systemTheme === "dark" ? "noir" : "studio";
  const styles = useMemo(() => StyleSheet.create(createSyntyrNativeStyles(theme)), [theme]);
  const colors = syntyrMobileTokens.themes[theme].colors;

  return (
    <ScrollView style={styles.screen} contentContainerStyle={{ paddingBottom: 32 }}>
      <View style={styles.panel}>
        <Text accessibilityRole="header" style={styles.heading}>Syntyr on mobile</Text>
        <Text style={styles.body}>
          Native controls, shared Syntyr design values, and no browser stylesheet.
        </Text>
        <TextInput
          accessibilityLabel="Email address"
          autoCapitalize="none"
          autoComplete="email"
          keyboardType="email-address"
          placeholder="Email address"
          placeholderTextColor={colors.muted}
          value={email}
          onChangeText={setEmail}
          style={styles.field}
        />
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Submit sample form"
          onPress={() => setSubmissions((current) => current + 1)}
          style={styles.button}
        >
          <Text style={styles.buttonLabel}>Submit</Text>
        </Pressable>
        <Text style={[styles.body, { marginTop: syntyrMobileTokens.spacing["2"] }]}>
          Submitted {submissions} time(s)
        </Text>
      </View>
    </ScrollView>
  );
}
