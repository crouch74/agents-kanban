import { expect, test } from "@playwright/test";
import { bootstrapProject, installMockApi } from "./support/mockControlPlane";

test.beforeEach(async ({ page }) => {
  await installMockApi(page);
});

test("task lifecycle to done flow", async ({ page }, testInfo) => {
  await bootstrapProject(page, "Task Lifecycle Project");
  await page.getByText("Back to board").click();

  const lifecycleTask = page.getByRole("button", { name: /Kick off planning and board setup/i }).first();
  await expect(lifecycleTask).toBeVisible();

  const doneColumn = page.getByText("Done").first();

  await lifecycleTask.click();
  await expect(page.getByText("Back to board")).toBeVisible();
  await expect(page.getByText("In Progress").first()).toBeVisible();

  await page.evaluate(async () => {
    await fetch("http://127.0.0.1:8000/api/v1/tasks/task-1", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ board_column_id: "col-done" }),
    });
  });
  await page.reload();
  await page.getByRole("button", { name: "Projects" }).click();
  await expect(doneColumn).toBeVisible();
  await lifecycleTask.click();
  await expect(page.getByText("Done").first()).toBeVisible();

  await page.screenshot({ path: testInfo.outputPath("task-lifecycle-to-done-flow.png"), fullPage: true });
});
