import React from "react";
import { fireEvent, render, waitFor } from "@testing-library/react-native";
import App from "./src/App";
import { createSyntyrNativeStyles, resolveSyntyrNativeTheme } from "./src/styles";
import { syntyrMobileTokens } from "./src/tokens";

describe("Syntyr native Expo integration", () => {
  it("renders accessible native controls and responds to interactions", async () => {
    const { getByLabelText, getByRole, getByText } = await render(<App />);
    expect(getByRole("header")).toBeTruthy();
    const email = getByLabelText("Email address");
    await fireEvent.changeText(email, "mobile@example.com");
    await waitFor(() => expect(getByLabelText("Email address").props.value).toBe("mobile@example.com"));
    await fireEvent.press(getByLabelText("Submit sample form"));
    await waitFor(() => expect(getByText("Submitted 1 time(s)")).toBeTruthy());
  });

  it("allows an explicit appearance override and return to system appearance", async () => {
    const { getByLabelText, getByText } = await render(<App />);
    await fireEvent.press(getByLabelText("Grid appearance"));
    await waitFor(() => expect(getByText("Palette: grid")).toBeTruthy());
    expect(getByLabelText("Grid appearance").props.accessibilityState.checked).toBe(true);
    await fireEvent.press(getByLabelText("Studio appearance"));
    await waitFor(() => expect(getByText("Palette: studio")).toBeTruthy());
    await fireEvent.press(getByLabelText("System appearance"));
    expect(getByLabelText("System appearance").props.accessibilityState.checked).toBe(true);
  });

  it("matches the web auto palette and keeps an explicit preference", () => {
    expect(resolveSyntyrNativeTheme("auto", "dark")).toBe("grid");
    expect(resolveSyntyrNativeTheme("auto", "light")).toBe("studio");
    expect(resolveSyntyrNativeTheme("auto", null)).toBe("studio");
    expect(resolveSyntyrNativeTheme("noir", "light")).toBe("noir");
  });

  it("keeps native controls at platform touch target minimums", () => {
    const android = createSyntyrNativeStyles("studio", "android");
    const ios = createSyntyrNativeStyles("studio", "ios");
    for (const control of ["field", "button"] as const) {
      expect(android[control].minHeight).toBeGreaterThanOrEqual(48);
      expect(ios[control].minHeight).toBeGreaterThanOrEqual(44);
    }
  });

  it.each(Object.keys(syntyrMobileTokens.themes))(
    "styles use exact palette colors for %s",
    (themeName) => {
      const name = themeName as keyof typeof syntyrMobileTokens.themes;
      const styles = createSyntyrNativeStyles(name);
      const colors = syntyrMobileTokens.themes[name].colors;
      expect(styles.screen.backgroundColor).toBe(colors.bg);
      expect(styles.panel.backgroundColor).toBe(colors.surface);
      expect(styles.button.backgroundColor).toBe(colors.accent);
      expect(styles.buttonLabel.color).toBe(colors["on-accent"]);
      expect(styles.button.minHeight).toBeGreaterThanOrEqual(44);
    }
  );
});
