/** Copy-owned, dependency-free style recipes for native React Native / Expo.
 * Pass the result to React Native's StyleSheet.create().
 * No browser CSS, DOM, or runtime styling library is involved.
 */
import { syntyrMobileTokens, type SyntyrMobileTheme } from "./tokens";

export function createSyntyrNativeStyles(theme: SyntyrMobileTheme = "studio") {
  const { colors, radius } = syntyrMobileTokens.themes[theme];
  const { spacing, fontSize, controlHeight } = syntyrMobileTokens;

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
      lineHeight: fontSize.sm * 1.55,
    },
    field: {
      color: colors.text,
      backgroundColor: colors.bg,
      borderColor: colors.frame,
      borderWidth: 1,
      borderRadius: radius,
      minHeight: controlHeight,
      paddingHorizontal: spacing["2"],
      fontSize: fontSize.base,
      marginTop: spacing["2"],
    },
    button: {
      backgroundColor: colors.accent,
      borderRadius: radius,
      minHeight: controlHeight,
      paddingHorizontal: spacing["3"],
      alignItems: "center" as const,
      justifyContent: "center" as const,
      marginTop: spacing["3"],
    },
    buttonLabel: {
      color: colors["on-accent"],
      fontSize: fontSize.sm,
      fontWeight: "600" as const,
    },
  };
}
