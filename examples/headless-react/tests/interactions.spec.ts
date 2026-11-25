import { test, expect } from "@playwright/test";

test("Radix action menu supports keyboard navigation and restores focus", async ({ page }) => {
  await page.goto("/");
  const trigger = page.getByRole("button", { name: "Campaign actions" });
  await trigger.focus();
  await page.keyboard.press("ArrowDown");
  await expect(page.getByRole("menu")).toBeVisible();
  const review = page.getByRole("menuitem", { name: "Review campaign" });
  await expect(review).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator(".syn-toast-description")).toHaveText("Review selected; no data changed.");
  await expect(trigger).toBeFocused();
});

test("React Aria combobox filters and selects options via keyboard", async ({ page }) => {
  await page.goto("/");
  const field = page.getByRole("combobox", { name: "Advertising format" });
  await field.fill("Digital");
  await expect(page.getByRole("option", { name: "Digital screen" })).toBeVisible();
  await expect(page.getByRole("option", { name: "Static billboard" })).toHaveCount(0);
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");
  await expect(field).toHaveValue("Digital screen");
});

test("Radix toast can be announced, dismissed and remains nonblocking", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Show a notification" }).click();
  await expect(page.locator(".syn-toast-description")).toHaveText("This is not a persisted operation.");
  await page.getByRole("button", { name: "Dismiss Demo notification" }).click();
  await expect(page.locator(".syn-toast-description")).toHaveCount(0);
});

test("opt-in styling applies to portal content inside the themed root", async ({ page }) => {
  await page.goto("/");
  const menu = page.getByRole("button", { name: "Campaign actions" });
  await menu.click();
  const surface = page.locator(".syn-menu-surface");
  await expect(surface).toBeVisible();
  await expect(surface).toHaveCSS("border-top-style", "solid");
  await expect(page.locator("body")).toHaveClass(/syn-root/);
});

test("narrow layouts keep the menu and combobox within the viewport", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 680 });
  await page.goto("/");
  await page.getByRole("button", { name: "Campaign actions" }).click();
  await expect(page.locator(".syn-menu-surface")).toBeVisible();
  const overflows = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(overflows).toBe(false);
  await page.keyboard.press("Escape");
  await page.getByRole("combobox", { name: "Advertising format" }).fill("Transit");
  await expect(page.getByRole("option", { name: "Transit advertising" })).toBeVisible();
});

test("forced colors and reduced motion preserve menu keyboard access", async ({ page }) => {
  await page.emulateMedia({ forcedColors: "active", reducedMotion: "reduce" });
  await page.goto("/");
  const trigger = page.getByRole("button", { name: "Campaign actions" });
  await trigger.focus();
  await page.keyboard.press("ArrowDown");
  await expect(page.getByRole("menuitem", { name: "Review campaign" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(trigger).toBeFocused();
});


test("React Aria sortable data grid changes DOM order and announces the sorted column", async ({ page }) => {
  await page.goto("/");
  const grid = page.getByRole("grid", { name: "Campaign inventory" });
  await expect(grid).toBeVisible();
  const nameHeader = grid.getByRole("columnheader", { name: "Asset" });
  await expect(nameHeader).toHaveAttribute("aria-sort", "ascending");
  await expect(grid.getByRole("row").nth(1)).toContainText("Airport display");
  await nameHeader.click();
  await expect(nameHeader).toHaveAttribute("aria-sort", "descending");
  await expect(grid.getByRole("row").nth(1)).toContainText("Transit shelter");
  const faces = grid.getByRole("columnheader", { name: "Faces" });
  await faces.click();
  await expect(faces).toHaveAttribute("aria-sort", "ascending");
  await expect(grid.getByRole("row").nth(1)).toContainText("Airport display");
});

test("sortable data grid works from keyboard and keeps focus visible", async ({ page }) => {
  await page.goto("/");
  const grid = page.getByRole("grid", { name: "Campaign inventory" });
  const asset = grid.getByRole("columnheader", { name: "Asset" });
  await asset.focus();
  await page.keyboard.press("Enter");
  await expect(asset).toHaveAttribute("aria-sort", "descending");
  await expect(asset).toBeFocused();
});

test("inventory filtering constrains selection scope and clears stale selections", async ({ page }) => {
  await page.goto("/");
  const filter = page.getByRole("searchbox", { name: "Filter inventory by asset name" });
  const grid = page.getByRole("grid", { name: "Campaign inventory" });

  await filter.fill("transit");
  await expect(grid.getByRole("row")).toHaveCount(2);
  await page.getByRole("button", { name: "Select 1 matching asset" }).click();
  await expect(grid.getByRole("row", { name: /Transit shelter/ })).toHaveAttribute("aria-selected", "true");
  await expect(page.getByRole("status", { name: "Inventory selection scope" })).toContainText("1 selected");

  await filter.fill("airport");
  await expect(grid.getByRole("row")).toHaveCount(2);
  await expect(grid.getByRole("row", { name: /Airport display/ })).not.toHaveAttribute("aria-selected", "true");
  await expect(page.getByRole("status", { name: "Inventory selection scope" })).toContainText("0 selected");
  await expect(page.getByRole("button", { name: "Clear selection" })).toBeDisabled();
});

test("inventory offers a safe preview action and an accessible record detail view", async ({ page }) => {
  await page.goto("/");
  const grid = page.getByRole("grid", { name: "Campaign inventory" });
  const selectedRow = grid.getByRole("row", { name: /Central billboard/ });
  await selectedRow.focus();
  await page.keyboard.press("Space");
  await expect(selectedRow).toHaveAttribute("aria-selected", "true");
  await page.getByRole("button", { name: "Preview selection" }).click();
  await expect(page.locator(".syn-toast-description")).toContainText("1 asset");

  await page.getByRole("button", { name: "View details for Central billboard" }).click();
  const details = page.getByRole("region", { name: "Asset details" });
  await expect(details.getByRole("heading", { name: "Central billboard" })).toBeVisible();
  await expect(details).toContainText("12 faces");
});

test("inventory empty filter state remains truthful and non-actionable", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("searchbox", { name: "Filter inventory by asset name" }).fill("not-an-asset");
  await expect(page.getByText("No matching assets")).toBeVisible();
  await expect(page.getByRole("button", { name: "Select 0 matching assets" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Preview selection" })).toBeDisabled();
});


test("resource selection stays actionable at 320px with enlarged text", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 780 });
  await page.goto("/");
  await page.addStyleTag({ content: "html { font-size: 64px !important; }" });
  await page.getByRole("searchbox", { name: "Filter inventory by asset name" }).fill("central");
  await page.getByRole("button", { name: "Select 1 matching asset" }).click();
  await expect(page.getByRole("status", { name: "Inventory selection scope" })).toContainText("1 selected");
  await page.getByRole("button", { name: "View details for Central billboard" }).click();
  await expect(page.getByRole("region", { name: "Asset details" })).toContainText("12 faces");
  const overflows = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(overflows).toBe(false);
});
