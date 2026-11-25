import { test, expect } from "@playwright/test";

const base = "/examples/lit/";
let runtimeErrors;
let externalRequests;

test.beforeEach(async ({ page }) => {
  runtimeErrors = [];
  externalRequests = [];
  page.on("pageerror", error => runtimeErrors.push(String(error)));
  page.on("request", request => {
    if (!request.url().startsWith("http://127.0.0.1:4188/")) {
      externalRequests.push(request.url());
    }
  });
});

test.afterEach(() => {
  if (runtimeErrors) expect(runtimeErrors).toEqual([]);
  if (externalRequests) expect(externalRequests).toEqual([]);
});

test.describe("without JavaScript", () => {
  test.use({ javaScriptEnabled: false });

  test("Lit fallback markup stays readable", async ({ page }) => {
    await page.goto(base + "index.html");
    const fallbacks = page.locator("[data-lit-fallback]");
    await expect(fallbacks).toHaveCount(2);
    await expect(fallbacks.first()).toContainText("Online");
    await expect(fallbacks.first()).toBeVisible();
    await expect(fallbacks.last()).toBeVisible();
  });

  test("React explains the JS requirement; HTMX form still navigates by GET", async ({ page }) => {
    await page.goto(base + "react-interop.html");
    await expect(page.locator("[data-nojs-fallback]")).toBeVisible();

    await page.goto(base + "htmx-interop.html");
    await expect(page.locator("#htmx-result [data-lit-fallback]")).toBeVisible();
    await page.getByRole("button", { name: "Load relay status" }).click();
    await expect(page).toHaveURL(/\/examples\/lit\/htmx-result\.html\?q=relay$/);
    await expect(page.locator("#htmx-result [data-lit-fallback]")).toContainText("Online");
  });
});

test("Light DOM reuses Syntyr styles, state, events, disabled and keyboard", async ({ page }) => {
  await page.goto(base + "index.html");
  const light = page.locator("syn-demo-status-panel");
  await expect(light.locator(".syn-panel .syn-status")).toBeVisible();
  await expect(light.locator("[data-lit-fallback]")).toHaveCount(0);
  await expect(light).toHaveAttribute("online", "");
  await expect(light.locator(".syn-panel")).toHaveCSS("position", "relative");
  const button = light.getByRole("button");
  await button.click();
  await expect(light.locator(".syn-status--warning")).toHaveText("Offline");
  await expect(page.locator("#event-output")).toContainText("North hub: offline");
  await light.evaluate(e => { e.busy = true; });
  await expect(button).toBeDisabled();
  await expect(light.locator(".syn-panel [data-busy-region]")).toHaveAttribute("aria-busy", "true");
  await expect(light.getByRole("status")).toHaveText("Updating status…");
  expect(await light.getByRole("status").evaluate(node => node.closest('[aria-busy="true"]'))).toBeNull();
  await light.evaluate(e => { e.busy = false; });
  await expect(light.locator(".syn-panel [data-busy-region]")).toHaveAttribute("aria-busy", "false");
  await button.focus();
  await page.keyboard.press("Enter");
  await expect(light).toHaveAttribute("online", "");
});

test("Shadow DOM uses inherited tokens, explicit parts and composed events", async ({ page }) => {
  await page.goto(base + "index.html");
  const shadow = page.locator("syn-demo-shadow-signal");
  const button = shadow.locator('button[part="toggle"]');
  await expect(button).toHaveAttribute("aria-pressed", "true");
  expect(await shadow.evaluate(e => Boolean(e.shadowRoot))).toBe(true);
  await expect(shadow.locator('[part="panel"]')).toHaveCSS("border-top-style", "dashed");
  const background = await shadow.locator('[part="panel"]').evaluate(e => getComputedStyle(e).backgroundColor);
  await page.locator('section[data-syn-theme="noir"]').evaluate(e => { e.dataset.synTheme = "grid"; });
  await expect.poll(async () => shadow.locator('[part="panel"]').evaluate(e => getComputedStyle(e).backgroundColor))
    .not.toBe(background);
  expect(await shadow.evaluate(e => getComputedStyle(e).getPropertyValue("--syn-accent").trim())).toBeTruthy();
  await button.focus();
  await page.keyboard.press("Enter");
  await expect(button).toHaveAttribute("aria-pressed", "false");
  await expect(page.locator("#event-output")).toContainText("composed shadow event");
});

test("React 19 receives native custom events from Lit", async ({ page }) => {
  await page.goto(base + "react-interop.html");
  const lit = page.locator("#react-root syn-demo-status-panel");
  await lit.getByRole("button", { name: "Mark offline" }).click();
  await expect(page.locator("#react-event-output")).toHaveText(
    "React customer hub: offline (React 19 handler)");
  await expect(lit.locator(".syn-status--warning")).toBeVisible();
});

test("HTMX swaps the host, Lit upgrades again, and native events still bubble", async ({ page }) => {
  await page.goto(base + "htmx-interop.html");
  const original = page.locator("#htmx-result syn-demo-status-panel");
  await expect(original.locator(".syn-status--warning")).toBeVisible();
  await original.evaluate(e => { e.dataset.testOld = "yes"; });
  await page.getByRole("button", { name: "Load relay status" }).click();
  const replacement = page.locator("#htmx-result syn-demo-status-panel");
  await expect(replacement.locator(".syn-status--success")).toHaveText("Online");
  await expect(page).toHaveURL(/\/examples\/lit\/htmx-interop\.html$/);
  await expect(replacement).not.toHaveAttribute("data-test-old", "yes");
  await expect(replacement.locator("[data-lit-fallback]")).toHaveCount(0);
  await replacement.getByRole("button", { name: "Mark offline" }).click();
  await expect(page.locator("#htmx-event-output")).toContainText("HTMX relay: offline");
});
