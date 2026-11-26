/** Copy-owned, dependency-free style recipes for native React Native / Expo.
 * Pass the result to React Native's StyleSheet.create().
 * No browser CSS, DOM, or runtime styling library is involved.
 */
import { syntyrMobileTokens, type SyntyrMobileTheme } from "./tokens";

export type SyntyrNativeThemePreference = SyntyrMobileTheme | "auto";

/** Match the browser auto palette, with an explicit user override. */
export function resolveSyntyrNativeTheme(
  preference: SyntyrNativeThemePreference,
  systemScheme: "light" | "dark" | null | undefined,
): SyntyrMobileTheme {
  return preference === "auto" ? (systemScheme === "dark" ? "grid" : "studio") : preference;
}

/** Use native touch sizes; do not translate compact web controls into tiny targets. */
export function createSyntyrNativeStyles(
  theme: SyntyrMobileTheme = "studio",
  platform?: string,
) {
  const { colors, radius } = syntyrMobileTokens.themes[theme];
  const { spacing, fontSize, controlHeight, bodyLeading } = syntyrMobileTokens;

  const targetHeight = Math.max(controlHeight, platform === "android" ? 48 : 44);

  return {
    screen: {
      flex: 1,
      backgroundColor: colors.bg,
      padding: spacing["3"],
    },
    panel: {
      backgroundColor: colors.surface,
      borderColor: colors.frame,
      borderWidth: 1,
      borderRadius: radius,
      padding: spacing["3"],
    },
    heading: {
      color: colors.text,
      fontSize: fontSize.base,
      fontWeight: "700" as const,
      marginBottom: spacing["2"],
    },
    body: {
      color: colors.muted,
      fontSize: fontSize.sm,
      lineHeight: fontSize.sm * bodyLeading,
    },
    field: {
      color: colors.text,
      backgroundColor: colors.bg,
      borderColor: colors.frame,
      borderWidth: 1,
      borderRadius: radius,
      minHeight: targetHeight,
      paddingHorizontal: spacing["2"],
      fontSize: fontSize.base,
      marginTop: spacing["2"],
    },
    button: {
      backgroundColor: colors.accent,
      borderRadius: radius,
      minHeight: targetHeight,
      paddingHorizontal: spacing["3"],
      alignItems: "center" as const,
      justifyContent: "center" as const,
      marginTop: spacing["3"],
    },
    buttonPressed: {
      opacity: 0.85,
    },
    buttonDisabled: {
      opacity: 0.5,
    },
    badge: {
      alignSelf: "flex-start" as const,
      backgroundColor: colors["surface-hi"],
      borderWidth: 1,
      borderColor: colors.frame,
      borderRadius: radius,
      paddingHorizontal: spacing["2"],
      paddingVertical: spacing["1"],
    },
    badgeLabel: {
      color: colors.text,
      fontSize: fontSize.xs,
      fontWeight: "600" as const,
    },
    statusSuccess: {
      color: colors.success,
    },
    statusDanger: {
      color: colors.danger,
    },
    buttonLabel: {
      color: colors["on-accent"],
      fontSize: fontSize.sm,
      fontWeight: "600" as const,
    },
  };
}
