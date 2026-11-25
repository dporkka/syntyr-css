import { test, expect } from "@playwright/test";

const fixture = "/examples/web-components/form-associated.html";
const selector = "syn-demo-asset-range";

test.describe("form-associated fixture without JavaScript", () => {
  test.use({ javaScriptEnabled: false });

  test("native labeled inputs submit through GET without component upgrade", async ({ page }) => {
    await page.goto(fixture);
    await page.getByRole("spinbutton", { name: "Minimum assets" }).fill("25");
    await page.getByRole("spinbutton", { name: "Maximum assets" }).fill("300");
    await page.getByRole("button", { name: "Search inventory" }).click();
    await expect(page).toHaveURL(/\/examples\/web-components\/form-result\.html\?/);
    const params = new URL(page.url()).searchParams;
    expect(params.getAll("assets_min")).toEqual(["25"]);
    expect(params.getAll("assets_max")).toEqual(["300"]);
  });
});

test("enhancement submits exactly one pair through ElementInternals without hidden inputs", async ({ page }) => {
  await page.goto(fixture);
  await expect(page.locator(selector)).toHaveAttribute("data-enhanced", "");
  const result = await page.evaluate(() => {
    const form = document.querySelector("#inventory-form");
    const control = form.querySelector("syn-demo-asset-range");
    const data = new FormData(form);
    return {
      entries: [...data.entries()],
      nativeNames: [...control.querySelectorAll("input")].map(input => input.name),
      hiddenInputs: control.querySelectorAll('input[type="hidden"]').length,
      formOwned: control.form === form,
    };
  });
  expect(result.formOwned).toBe(true);
  expect(result.hiddenInputs).toBe(0);
  expect(result.nativeNames).toEqual(["", ""]);
  expect(result.entries).toEqual([["assets_min", "50"], ["assets_max", "500"]]);
});

test("required and cross-field validation block invalid submissions and recover", async ({ page }) => {
  await page.goto(fixture);
  const min = page.getByRole("spinbutton", { name: "Minimum assets" });
  const max = page.getByRole("spinbutton", { name: "Maximum assets" });
  const host = page.locator(selector);
  await min.fill("");
  expect(await page.locator("#inventory-form").evaluate(form => form.checkValidity())).toBe(false);
  expect(await host.evaluate(el => el.validity.valueMissing)).toBe(true);
  await min.fill("900");
  await max.fill("100");
  await expect(host).toHaveAttribute("data-range-invalid", "");
  expect(await host.evaluate(el => el.validity.rangeOverflow || el.validity.customError)).toBe(true);
  expect(await page.locator("#inventory-form").evaluate(form => form.checkValidity())).toBe(false);
  await max.fill("1000");
  expect(await page.locator("#inventory-form").evaluate(form => form.checkValidity())).toBe(true);
  await expect(host).not.toHaveAttribute("data-range-invalid", "");
});

test("form reset restores both defaults and submitted values", async ({ page }) => {
  await page.goto(fixture);
  await page.getByRole("spinbutton", { name: "Minimum assets" }).fill("75");
  await page.getByRole("spinbutton", { name: "Maximum assets" }).fill("150");
  await page.getByRole("button", { name: "Reset" }).click();
  await expect(page.getByRole("spinbutton", { name: "Minimum assets" })).toHaveValue("50");
  await expect(page.getByRole("spinbutton", { name: "Maximum assets" })).toHaveValue("500");
  expect(await page.locator("#inventory-form").evaluate(form => [...new FormData(form).entries()]))
    .toEqual([["assets_min", "50"], ["assets_max", "500"]]);
});

test("disabled fieldsets and disabled host exclude values and restore controls", async ({ page }) => {
  await page.goto(fixture);
  const fieldset = page.locator("#inventory-group");
  const host = page.locator(selector);
  const min = page.getByRole("spinbutton", { name: "Minimum assets" });
  await fieldset.evaluate(el => { el.disabled = true; });
  await expect(min).toBeDisabled();
  expect(await host.evaluate(el => el.matches(":disabled"))).toBe(true);
  expect(await page.locator("#inventory-form").evaluate(form => [...new FormData(form).entries()])).toEqual([]);
  await fieldset.evaluate(el => { el.disabled = false; });
  await expect(min).toBeEnabled();
  await host.evaluate(el => { el.setAttribute("disabled", ""); });
  await expect(min).toBeDisabled();
  expect(await page.locator("#inventory-form").evaluate(form => [...new FormData(form).entries()])).toEqual([]);
  await host.evaluate(el => { el.removeAttribute("disabled"); });
  await expect(min).toBeEnabled();
  expect(await page.locator("#inventory-form").evaluate(form => [...new FormData(form).entries()]))
    .toEqual([["assets_min", "50"], ["assets_max", "500"]]);
});

test("formStateRestoreCallback and name changes update native submission", async ({ page }) => {
  await page.goto(fixture);
  const host = page.locator(selector);
  await host.evaluate(el => {
    el.formStateRestoreCallback(JSON.stringify(["10", "20"]), "restore");
    el.setAttribute("name", "faces");
  });
  expect(await page.locator("#inventory-form").evaluate(form => [...new FormData(form).entries()]))
    .toEqual([["faces_min", "10"], ["faces_max", "20"]]);
  await expect(page.getByRole("spinbutton", { name: "Minimum assets" })).toHaveValue("10");
  await expect(page.getByRole("spinbutton", { name: "Maximum assets" })).toHaveValue("20");
});

test("reconnecting preserves values and does not duplicate form submission", async ({ page }) => {
  await page.goto(fixture);
  await page.getByRole("spinbutton", { name: "Minimum assets" }).fill("75");
  await page.locator(selector).evaluate(el => { el.remove(); document.querySelector("#inventory-group").append(el); });
  expect(await page.locator("#inventory-form").evaluate(form => [...new FormData(form).entries()]))
    .toEqual([["assets_min", "75"], ["assets_max", "500"]]);
});

test("host required attribute controls both native inputs after upgrade", async ({ page }) => {
  await page.goto(fixture);
  const host = page.locator(selector);
  await host.evaluate(el => { el.removeAttribute("required"); });
  await page.getByRole("spinbutton", { name: "Minimum assets" }).fill("");
  await page.getByRole("spinbutton", { name: "Maximum assets" }).fill("");
  expect(await page.locator("#inventory-form").evaluate(form => form.checkValidity())).toBe(true);
  await host.evaluate(el => { el.setAttribute("required", ""); });
  expect(await page.locator("#inventory-form").evaluate(form => form.checkValidity())).toBe(false);
});

test("invalid cross-field value blocks native GET submit", async ({ page }) => {
  await page.goto(fixture);
  await page.getByRole("spinbutton", { name: "Minimum assets" }).fill("900");
  await page.getByRole("spinbutton", { name: "Maximum assets" }).fill("100");
  await page.getByRole("button", { name: "Search inventory" }).click();
  await expect(page).toHaveURL(/\/examples\/web-components\/form-associated\.html$/);
  await expect(page.locator("[data-asset-error]"))
    .toHaveText("Minimum assets cannot exceed maximum assets.");
});

test("native validation reports the cross-field error at its input", async ({ page }) => {
  await page.goto(fixture);
  const min = page.getByRole("spinbutton", { name: "Minimum assets" });
  const max = page.getByRole("spinbutton", { name: "Maximum assets" });
  await min.fill("600");
  await max.fill("250");
  expect(await page.locator(selector).evaluate(el => el.matches(":invalid"))).toBe(true);
  expect(await page.locator("#inventory-form").evaluate(form => form.reportValidity())).toBe(false);
  await expect(max).toBeFocused();
  await max.fill("700");
  expect(await page.locator(selector).evaluate(el => el.matches(":valid"))).toBe(true);
});
