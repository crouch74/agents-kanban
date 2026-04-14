import { expect, test } from "@playwright/test";

test("task board shell renders", async ({ page }, testInfo) => {
  await page.goto("http://127.0.0.1:5173");
  await expect(page.getByText("Shared Task Board")).toBeVisible();
  await expect(page.getByRole("button", { name: "Projects" }).nth(1)).toBeVisible();
  await page.screenshot({
    path: testInfo.outputPath("task-board-shell.png"),
    fullPage: true,
  });
});
