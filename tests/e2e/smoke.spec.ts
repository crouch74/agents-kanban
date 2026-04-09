import { test, expect } from "@playwright/test";

test("web shell renders heading", async ({ page }) => {
  await page.goto("http://127.0.0.1:5173");
  await expect(page.getByText("Local operator workspace")).toBeVisible();
});

