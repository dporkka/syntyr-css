import { test, expect } from "@playwright/test";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

// Test browser-owned focus, disclosure and form navigation with no app scripts.
// The webServer config runs the real Python GET form fixture.
const nativeRecipe = pathToFileURL(
  resolve(import.meta.dirname, "../../../examples/native-recipes.html")
).href;

test("floating labels, disclosure, and full GET fallback work without JavaScript", async ({ page }) => {
  await page.goto(nativeRecipe);
  const input = page.locator("#example-email");
  const label = page.locator('label[for="example-email"]');

  for (const width of [900, 320]) {
    await page.setViewportSize({ width, height: 820 });
    await input.blur();
    await label.scrollIntoViewIfNeeded();
    const rect = await label.boundingBox();
    expect(rect?.width).toBeGreaterThan(0);
    expect(rect?.height).toBeGreaterThan(0);
    await page.mouse.click(rect.x + rect.width / 2, rect.y + rect.height / 2);
    await expect(input).toBeFocused();
  }

  const fallback = page.locator("#native-report-fallback");
  await fallback.locator("summary").click();
  await expect(fallback.getByText("System report: operational.", { exact: false })).toBeVisible();

  await page.goto("http://127.0.0.1:8765/examples/htmx.html");
  await page.locator("#query").fill("Acme");
  await page.locator("#search-button").click();
  await page.waitForURL("**/customers/search?q=Acme");
  await expect(page.getByText("Acme Corporation")).toBeVisible();
  await expect(page.locator("#query")).toHaveValue("Acme");
  await expect(page.locator("body.syn-root")).toHaveCount(1);
});
