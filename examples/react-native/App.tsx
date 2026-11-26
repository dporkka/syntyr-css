/** Copy into an Expo or React Native app; adjust imports to copied adapter files. */
import React, { useMemo, useState } from "react";
import { Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View, useColorScheme } from "react-native";
import { createSyntyrNativeStyles, resolveSyntyrNativeTheme, type SyntyrNativeThemePreference } from "../../integrations/react-native/styles";
import { syntyrMobileTokens } from "../../integrations/react-native/tokens";

export default function App() {
  const systemTheme = useColorScheme();
  const [submissions, setSubmissions] = useState(0);
  const [email, setEmail] = useState("");
  const [preference, setPreference] = useState<SyntyrNativeThemePreference>("auto");
  const theme = resolveSyntyrNativeTheme(preference, systemTheme);
  const styles = useMemo(() => StyleSheet.create(createSyntyrNativeStyles(theme, Platform.OS)), [theme]);
  const colors = syntyrMobileTokens.themes[theme].colors;

  return (
    <ScrollView style={styles.screen} contentContainerStyle={{ paddingBottom: 32 }}>
      <View style={styles.panel}>
        <View style={styles.badge}>
          <Text style={styles.badgeLabel}>Palette: {theme}</Text>
        </View>
        <Text accessibilityRole="header" style={styles.heading}>Syntyr on mobile</Text>
        <Text style={styles.body}>
          Native controls, shared Syntyr design values, and no browser stylesheet.
        </Text>
        <Text style={styles.body}>Appearance</Text>
        {(["auto", "studio", "grid"] as const).map((option) => (
          <Pressable
            key={option}
            accessibilityRole="radio"
            accessibilityLabel={option === "auto" ? "System appearance" : option === "studio" ? "Studio appearance" : "Grid appearance"}
            accessibilityState={{ checked: preference === option }}
            onPress={() => setPreference(option)}
            style={({ pressed }) => [
              styles.button,
              preference !== option && { backgroundColor: colors["surface-hi"] },
              pressed && styles.buttonPressed,
            ]}
          >
            <Text style={[styles.buttonLabel, preference !== option && { color: colors.text }]}>
              {option === "auto" ? "System" : option === "studio" ? "Light" : "Dark"}
            </Text>
          </Pressable>
        ))}
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
          style={({ pressed }) => [styles.button, pressed && styles.buttonPressed]}
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
