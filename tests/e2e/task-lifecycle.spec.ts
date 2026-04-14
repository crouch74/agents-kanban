import { expect, test } from "@playwright/test";

test("create project add tasks move across board and comment", async ({ page }, testInfo) => {
  await page.goto("http://127.0.0.1:5173");

  await page.getByRole("button", { name: /\+ New Project/i }).click();
  await page.getByPlaceholder("Acme migration program").fill("E2E Project");
  await page.getByRole("button", { name: "Create project" }).click();

  await expect(page.getByText("E2E Project").first()).toBeVisible();

  await page.getByPlaceholder("Add task title").first().fill("Implement parser");
  await page.getByRole("button", { name: "+ Add task" }).first().click();

  const taskCard = page.getByText("Implement parser").first();
  await expect(taskCard).toBeVisible();

  await taskCard.click();
  await expect(page.getByText("Back to board")).toBeVisible();
  await page.getByPlaceholder("Leave progress comment").fill("Parser implementation started.");
  await page.getByText("Post comment").first().click();
  await expect(page.getByText("Parser implementation started.")).toBeVisible();

  await page.getByText("Back to board").click();
  await expect(page.getByRole("button", { name: /Implement parser/i }).first()).toBeVisible();

  await page.screenshot({ path: testInfo.outputPath("task-board-lifecycle.png"), fullPage: true });
});
