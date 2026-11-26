import React from "react";
import { fireEvent, render, waitFor } from "@testing-library/react-native";
import Host from "./src/Host";

it("renders the host className screen and exercises a copy-owned Syntyr control", async () => {
  const { getByText, getByRole, getByLabelText } = await render(<Host />);
  expect(getByText("Host NativeWind styling")).toBeTruthy();
  await fireEvent.press(getByRole("button", { name: "Open SaaS workspace" }));
  await waitFor(() => expect(getByText("Operations workspace")).toBeTruthy());
  await fireEvent.press(getByRole("tab", { name: "Clients" }));
  await fireEvent.changeText(getByLabelText("Search clients"), "retail");
  await waitFor(() => expect(getByText("1 matching clients")).toBeTruthy());
});
