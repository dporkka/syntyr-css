/** Copy-owned, dependency-free style recipes for native React Native / Expo.
 * Pass the result to React Native's StyleSheet.create().
 * No browser CSS, DOM, or runtime styling library is involved.
 */
import { syntyrMobileTokens, type SyntyrMobileTheme } from "./tokens";

export type SyntyrNativeThemePreference = SyntyrMobileTheme | "auto";
export type SyntyrNativeInsets = { top: number; right: number; bottom: number; left: number };

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
  insets?: SyntyrNativeInsets,
) {
  const { colors, radius } = syntyrMobileTokens.themes[theme];
  const { spacing, fontSize, controlHeight, bodyLeading } = syntyrMobileTokens;

  const targetHeight = Math.max(controlHeight, platform === "android" ? 48 : 44);

  return {
    screen: {
      flex: 1,
      backgroundColor: colors.bg,
      padding: spacing["3"],
      ...(insets && {
        paddingTop: spacing["3"] + insets.top,
        paddingRight: spacing["3"] + insets.right,
        paddingBottom: spacing["3"] + insets.bottom,
        paddingLeft: spacing["3"] + insets.left,
      }),
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
    // Opt-in native composition recipes; no new web selectors or token source.
    stack: {
      gap: spacing["2"],
    },
    metricGrid: {
      flexDirection: "row" as const,
      flexWrap: "wrap" as const,
      gap: spacing["2"],
    },
    metricCard: {
      flexGrow: 1,
      flexBasis: 140,
      flexShrink: 1,
      minWidth: 0,
    },
    metricValue: {
      color: colors.text,
      fontSize: fontSize.base * 1.5,
      fontWeight: "700" as const,
    },
    controlLabel: {
      color: colors.text,
      fontSize: fontSize.sm,
      fontWeight: "600" as const,
    },
    action: {
      minHeight: targetHeight,
      paddingHorizontal: spacing["3"],
      paddingVertical: spacing["2"],
      borderRadius: radius,
      borderWidth: 2,
      borderColor: colors.accent,
      backgroundColor: colors.accent,
      alignItems: "center" as const,
      justifyContent: "center" as const,
    },
    actionSecondary: {
      backgroundColor: colors.surface,
      borderColor: colors["frame-strong"],
    },
    actionSecondaryLabel: {
      color: colors.text,
    },
    actionPressed: {
      borderColor: colors.text,
    },
    actionSecondaryPressed: {
      borderColor: colors.accent,
    },
    input: {
      color: colors.text,
      backgroundColor: colors.bg,
      borderColor: colors["frame-strong"],
      borderWidth: 1,
      borderRadius: radius,
      minHeight: targetHeight,
      paddingHorizontal: spacing["2"],
      paddingVertical: spacing["2"],
      fontSize: fontSize.base,
    },
    inputError: {
      borderColor: colors.danger,
      borderWidth: 2,
    },
    statusWarning: {
      color: colors.warning,
    },
    tabStrip: {
      flexDirection: "row" as const,
      flexWrap: "wrap" as const,
      gap: spacing["1"],
    },
    tab: {
      flexGrow: 1,
      flexBasis: 80,
      flexShrink: 1,
      minHeight: targetHeight,
      minWidth: 0,
      padding: spacing["2"],
      alignItems: "center" as const,
      justifyContent: "center" as const,
      backgroundColor: colors.surface,
      borderWidth: 2,
      borderColor: colors["frame-strong"],
      borderRadius: radius,
    },
    tabSelected: {
      backgroundColor: colors.accent,
      borderColor: colors.accent,
    },
    record: {
      minHeight: targetHeight,
      padding: spacing["2"],
      borderWidth: 1,
      borderColor: colors["frame-strong"],
      borderRadius: radius,
      backgroundColor: colors.surface,
      gap: spacing["1"],
    },
    recordSelected: {
      borderColor: colors.accent,
      borderWidth: 2,
    },
    buttonLabel: {
      color: colors["on-accent"],
      fontSize: fontSize.sm,
      fontWeight: "600" as const,
    },
  };
}
