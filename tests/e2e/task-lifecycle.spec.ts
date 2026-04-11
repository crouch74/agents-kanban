import { expect, test } from "@playwright/test";
import { bootstrapProject, installMockApi } from "./support/mockControlPlane";

test.beforeEach(async ({ page }) => {
  await installMockApi(page);
});

test("task lifecycle to done flow", async ({ page }, testInfo) => {
  await bootstrapProject(page, "Task Lifecycle Project");
  await page.getByRole("button", { name: "Projects" }).click();
  await expect(page.getByRole("heading", { name: "Project Board" })).toBeVisible();

  const lifecycleTask = page.getByRole("button", { name: /Kick off planning and board setup/i }).first();
  await expect(lifecycleTask).toBeVisible();

  const todoColumn = page.getByText("Todo").first();
  const inProgressColumn = page.getByText("In Progress").first();
  const doneColumn = page.getByText("Done").first();

  await lifecycleTask.click();
  await expect(page.getByText("Task quick inspect")).toBeVisible();
  await expect(page.getByText("State: in_progress")).toBeVisible();

  await lifecycleTask.dragTo(todoColumn);
  await lifecycleTask.click();
  await expect(page.getByText("State: todo")).toBeVisible();

  await lifecycleTask.dragTo(inProgressColumn);
  await lifecycleTask.click();
  await expect(page.getByText("State: in_progress")).toBeVisible();

  await lifecycleTask.dragTo(doneColumn);
  await lifecycleTask.click();
  await expect(page.getByText("State: done")).toBeVisible();

  await page.screenshot({ path: testInfo.outputPath("task-lifecycle-to-done-flow.png"), fullPage: true });
});
