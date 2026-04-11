import { expect, test } from "@playwright/test";
import { bootstrapProject, installMockApi } from "./support/mockControlPlane";

test.beforeEach(async ({ page }) => {
  await installMockApi(page);
});

test("waiting-question pause and resume flow", async ({ page }, testInfo) => {
  await bootstrapProject(page, "Waiting Flow Project");
  await page.getByRole("button", { name: "Sessions" }).click();
  await expect(page.getByRole("heading", { name: "Session Runtime" })).toBeVisible();

  const openQuestionPanel = page.locator("div").filter({ hasText: "Open waiting question" }).first();
  const taskSelect = openQuestionPanel.locator("select").first();
  await taskSelect.selectOption("task-1");
  await page
    .getByPlaceholder("What decision or clarification does the agent need?")
    .fill("Should we pause deployment until legal approval?");
  await page.getByPlaceholder("Why is work blocked?").fill("Legal sign-off is pending");
  await page.getByRole("button", { name: "Open question" }).click();

  await expect(page.getByText("Waiting")).toBeVisible();

  await page.getByRole("button", { name: "Waiting Inbox" }).click();
  await expect(page.getByRole("heading", { name: "Waiting Inbox" })).toBeVisible();
  await expect(page.getByText("Should we pause deployment until legal approval?")).toBeVisible();

  await page.getByPlaceholder("Reply to unblock the agent").fill("Approved. Continue with the current plan.");
  await page.getByRole("button", { name: /send reply/i }).click();
  await expect(page.getByText("answered")).toBeVisible();

  await page.screenshot({ path: testInfo.outputPath("waiting-question-pause-resume-flow.png"), fullPage: true });
});
