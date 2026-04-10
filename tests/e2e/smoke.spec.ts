import { test, expect } from "@playwright/test";

test("web shell renders heading", async ({ page }, testInfo) => {
  await page.goto("http://127.0.0.1:5173");
  await expect(page.getByText("Local operator workspace")).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath("web-shell.png"),
    fullPage: true,
  });
});
