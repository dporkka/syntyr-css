import React from "react";
import { fireEvent, render, waitFor } from "@testing-library/react-native";
import App from "./src/App";
import { createSyntyrNativeStyles } from "./src/styles";
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
