import { expect, test } from "@playwright/test";
import { bootstrapProject, installMockApi } from "./support/mockControlPlane";

test.beforeEach(async ({ page }) => {
  await installMockApi(page);
});

test("places the add task composer below lane tasks", async ({ page }) => {
  await bootstrapProject(page, "Board Layout Project");
  await page.getByText("Back to board").click();

  const kickoffTask = page.getByRole("button", { name: /Kick off planning and board setup/i }).first();
  await expect(kickoffTask).toBeVisible();

  const lane = kickoffTask.locator('xpath=ancestor::div[contains(@class, "min-w-[260px]")][1]');
  const taskBox = await kickoffTask.boundingBox();
  const taskInput = lane.getByPlaceholder("Add task title");
  const addTaskButton = lane.getByRole("button", { name: "+ Add task" });

  await expect(taskInput).toBeVisible();
  await expect(addTaskButton).toBeVisible();

  const inputBox = await taskInput.boundingBox();
  const buttonBox = await addTaskButton.boundingBox();

  expect(taskBox).not.toBeNull();
  expect(inputBox).not.toBeNull();
  expect(buttonBox).not.toBeNull();

  expect(inputBox!.y).toBeGreaterThan(taskBox!.y + taskBox!.height);
  expect(buttonBox!.y).toBeGreaterThan(inputBox!.y + inputBox!.height);
});
