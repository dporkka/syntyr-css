import React from "react";
import { View } from "react-native";
import { fireEvent, render, waitFor } from "@testing-library/react-native";
import App from "./src/App";
import OperationsScreen from "./src/OperationsScreen";
import { NativeAction, NativeState, NativeRecord } from "./src/recipes";
import { createSyntyrNativeStyles } from "./src/styles";
import { syntyrMobileTokens } from "./src/tokens";

describe("Syntyr native SaaS recipes", () => {
  it("opens the workspace, shows metrics, navigates, and returns to the basic sample", async () => {
    const { getByText, getByRole, queryByText } = await render(<App />);
    await fireEvent.press(getByRole("button", { name: "Open SaaS workspace" }));
    expect(getByText("Operations workspace")).toBeTruthy();
    expect(getByText("$42k")).toBeTruthy();
    expect(getByRole("tab", { name: "Overview" }).props.accessibilityState.selected).toBe(true);
    await fireEvent.press(getByRole("button", { name: "Review clients" }));
    await waitFor(() => expect(getByRole("tab", { name: "Clients" }).props.accessibilityState.selected).toBe(true));
    expect(queryByText("$42k")).toBeNull();
    await fireEvent.press(getByRole("button", { name: "Back to basic recipes" }));
    expect(getByText("Syntyr on mobile")).toBeTruthy();
  });

  it("filters fictional CRM records, selects a record, and clears an empty result", async () => {
    const { getByRole, getByLabelText, getByText, queryByText } = await render(
      <OperationsScreen theme="grid" onBack={jest.fn()} />,
    );
    await fireEvent.press(getByRole("tab", { name: "Clients" }));
    expect(getByText("3 matching clients")).toBeTruthy();
    await fireEvent.changeText(getByLabelText("Search clients"), "RETAIL");
    await waitFor(() => expect(getByText("1 matching clients")).toBeTruthy());
    expect(queryByText("Mesa Works")).toBeNull();
    const harbor = getByRole("button", { name: "Harbor Retail, Retail operations, Needs review" });
    await fireEvent.press(harbor);
    expect(getByText("Selected client: Harbor Retail")).toBeTruthy();
    expect(getByRole("button", { name: "Harbor Retail, Retail operations, Needs review" }).props.accessibilityState.selected).toBe(true);
    await fireEvent.changeText(getByLabelText("Search clients"), "nothing");
    expect(getByText("No matching clients")).toBeTruthy();
    expect(queryByText("Selected client: Harbor Retail")).toBeNull();
    await fireEvent.press(getByRole("button", { name: "Clear search" }));
    expect(getByText("3 matching clients")).toBeTruthy();
    expect(getByLabelText("Search clients").props.value).toBe("");
  });

  it("shows explicit local field errors and saved-preview state without retaining stale success", async () => {
    const { getByRole, getByLabelText, getByText, queryByText } = await render(
      <OperationsScreen theme="studio" onBack={jest.fn()} />,
    );
    await fireEvent.press(getByRole("tab", { name: "Settings" }));
    await fireEvent.changeText(getByLabelText("Workspace name"), "  ");
    await fireEvent.press(getByRole("button", { name: "Save preview" }));
    expect(getByText("Enter a workspace name.")).toBeTruthy();
    expect(getByLabelText("Workspace name").props.accessibilityHint).toBe("Enter a workspace name.");
    expect(queryByText("Preview saved locally.")).toBeNull();
    await fireEvent.changeText(getByLabelText("Workspace name"), "Updated preview");
    await fireEvent.press(getByRole("button", { name: "Save preview" }));
    expect(getByText("Preview saved locally.")).toBeTruthy();
    expect(queryByText("Enter a workspace name.")).toBeNull();
    await fireEvent.changeText(getByLabelText("Workspace name"), "Unsaved edit");
    expect(queryByText("Preview saved locally.")).toBeNull();
  });

  it("honors disabled/busy actions and uses real native retry controls", async () => {
    const styles = createSyntyrNativeStyles("studio");
    const onPress = jest.fn();
    const { getByRole, getByLabelText, rerender, queryByRole } = await render(
      <View><NativeAction styles={styles} label="Submit" onPress={onPress} disabled /></View>,
    );
    expect(getByRole("button", { name: "Submit" }).props.accessibilityState.disabled).toBe(true);
    await fireEvent.press(getByRole("button", { name: "Submit" }));
    expect(onPress).not.toHaveBeenCalled();
    await rerender(<View><NativeAction styles={styles} label="Submit" onPress={onPress} busy /></View>);
    expect(getByRole("button", { name: "Submit" }).props.accessibilityState.busy).toBe(true);
    await fireEvent.press(getByRole("button", { name: "Submit" }));
    expect(onPress).not.toHaveBeenCalled();
    await rerender(<View><NativeState styles={styles} kind="loading" title="Loading preview" description="Please wait."
      action={{ label: "Retry", onPress }} /></View>);
    expect(getByLabelText("Loading")).toBeTruthy();
    expect(queryByRole("button", { name: "Retry" })).toBeNull();
    await rerender(<View><NativeState styles={styles} kind="error" title="Preview unavailable" description="Try again."
      action={{ label: "Retry", onPress }} /></View>);
    await fireEvent.press(getByRole("button", { name: "Retry" }));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it("does not pretend a read-only record has button semantics", async () => {
    const { getByText, queryByRole } = await render(
      <NativeRecord styles={createSyntyrNativeStyles("studio")} title="Read-only record"
        description="Illustration" status="Active" tone="success" />,
    );
    expect(getByText("Read-only record")).toBeTruthy();
    expect(queryByRole("button")).toBeNull();
  });

  it.each(Object.keys(syntyrMobileTokens.themes))("matches semantic colors and native sizing for %s", (name) => {
    const theme = name as keyof typeof syntyrMobileTokens.themes;
    const { colors } = syntyrMobileTokens.themes[theme];
    const android = createSyntyrNativeStyles(theme, "android");
    const ios = createSyntyrNativeStyles(theme, "ios", { top: 24, right: 5, bottom: 12, left: 8 });
    for (const control of ["action", "input", "tab", "record"] as const) {
      expect(android[control].minHeight).toBeGreaterThanOrEqual(48);
      expect(ios[control].minHeight).toBeGreaterThanOrEqual(44);
    }
    expect(ios.screen.paddingTop).toBe(syntyrMobileTokens.spacing["3"] + 24);
    expect(ios.screen.paddingRight).toBe(syntyrMobileTokens.spacing["3"] + 5);
    expect(ios.screen.paddingBottom).toBe(syntyrMobileTokens.spacing["3"] + 12);
    expect(ios.screen.paddingLeft).toBe(syntyrMobileTokens.spacing["3"] + 8);
    expect(android.screen.paddingTop).toBeUndefined();
    expect(android.action.backgroundColor).toBe(colors.accent);
    expect(android.tabSelected.backgroundColor).toBe(colors.accent);
    expect(android.inputError.borderColor).toBe(colors.danger);
    expect(android.statusWarning.color).toBe(colors.warning);
  });
});
