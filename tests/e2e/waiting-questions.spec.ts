import { expect, test } from "@playwright/test";
import { bootstrapProject, installMockApi } from "./support/mockControlPlane";

test.beforeEach(async ({ page }) => {
  await installMockApi(page);
});

test("waiting-question pause and resume flow", async ({ page }, testInfo) => {
  await bootstrapProject(page, "Waiting Flow Project");
  await page.evaluate(async () => {
    await fetch("http://127.0.0.1:8000/api/v1/questions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        task_id: "task-1",
        session_id: "session-1",
        prompt: "Should we pause deployment until legal approval?",
        blocked_reason: "Legal sign-off is pending",
        urgency: "high",
      }),
    });
  });
  await page.reload();

  await expect(page.getByRole("button", { name: "Waiting Inbox" })).toBeVisible();

  await page.getByRole("button", { name: "Waiting Inbox" }).click();
  await expect(page.getByPlaceholder("Reply to unblock the agent")).toBeVisible();

  await page.getByPlaceholder("Reply to unblock the agent").fill("Approved. Continue with the current plan.");
  await page.getByRole("button", { name: /send reply/i }).click();
  await expect(page.getByText("answered")).toBeVisible();

  await page.screenshot({ path: testInfo.outputPath("waiting-question-pause-resume-flow.png"), fullPage: true });
});
