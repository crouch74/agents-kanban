import { expect, test } from "@playwright/test";
import { bootstrapProject, installMockApi } from "./support/mockControlPlane";

test.beforeEach(async ({ page }) => {
  await installMockApi(page);
});

test("project bootstrap flow", async ({ page }, testInfo) => {
  await bootstrapProject(page, "Bootstrap Flow Project");
  await expect(page.getByRole("dialog", { name: "New Project" })).not.toBeVisible();
  await expect(page.getByRole("heading", { name: "Bootstrap Flow Project" })).toBeVisible();
  await expect(page.getByRole("button", { name: "+ New Project" })).toBeVisible();

  await page.screenshot({ path: testInfo.outputPath("project-bootstrap-flow.png"), fullPage: true });
});
