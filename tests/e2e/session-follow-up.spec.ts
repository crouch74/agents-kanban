import { expect, test } from "@playwright/test";
import { bootstrapProject, installMockApi } from "./support/mockControlPlane";

test.beforeEach(async ({ page }) => {
  await installMockApi(page);
});

test("session follow-up flow", async ({ page }, testInfo) => {
  await bootstrapProject(page, "Session Follow-up Project");
  await page.getByRole("button", { name: "Sessions" }).click();
  await expect(page.getByRole("heading", { name: "Session Runtime" })).toBeVisible();

  const kickoffSessionButton = page.getByRole("button").filter({ hasText: "acp-bootstrap-kickoff" }).first();
  await expect(kickoffSessionButton).toBeVisible();
  await kickoffSessionButton.click();
  await expect(page.getByText("Output + runtime logs")).toBeVisible();
  await expect(page.getByText("Implemented slice")).toBeVisible();

  await page.getByRole("button", { name: "Retry" }).click();
  await expect(page.getByRole("heading", { name: "acp-bootstrap-kickoff-retry" })).toBeVisible();

  await page.screenshot({ path: testInfo.outputPath("session-follow-up-flow.png"), fullPage: true });
});
