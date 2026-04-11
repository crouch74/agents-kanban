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

  const doneColumn = page.getByText("Done").first();

  await lifecycleTask.click();
  await expect(page.getByText("Task quick inspect")).toBeVisible();
  await expect(page.getByText("State: in_progress")).toBeVisible();

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
  await expect(page.getByText("State: done")).toBeVisible();

  await page.screenshot({ path: testInfo.outputPath("task-lifecycle-to-done-flow.png"), fullPage: true });
});
