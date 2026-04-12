import { expect, test } from "@playwright/test";
import { bootstrapProject, installMockApi } from "./support/mockControlPlane";

test("creates a calculator project through the default bootstrap dialog flow", async ({ page }) => {
  await installMockApi(page);
  await bootstrapProject(page, "Simple Calculator");

  await expect(page.getByRole("heading", { name: "Simple Calculator" })).toBeVisible();
  await expect(page.getByText("Kick off planning and board setup").first()).toBeVisible();
});

test("requires explicit confirm when preview indicates an existing repository", async ({ page }) => {
  await installMockApi(page, { requireBootstrapConfirmation: true });

  await page.goto("/?section=projects");
  await page.getByRole("button", { name: "Projects" }).click();
  await page.getByRole("button", { name: /\+ new project/i }).click();
  await page.getByPlaceholder("Acme migration program").fill("Calculator Confirmed");
  await page.getByPlaceholder("/absolute/path/to/repo").fill("/tmp/calculator-confirmed");
  await page
    .getByPlaceholder(
      "Describe the work to kick off. ACP will ask the agent to clarify requirements and create tasks/subtasks.",
    )
    .fill("Plan and implement calculator operations with tests.");

  await page.getByRole("button", { name: "Review bootstrap" }).click();

  await expect(page.getByText("Review planned repo changes before kickoff")).toBeVisible();
  await expect(page.getByText(".acp/project.local.json")).toBeVisible();
  await expect(page.getByRole("button", { name: "Confirm + launch bootstrap" })).toBeVisible();

  await page.getByRole("button", { name: "Confirm + launch bootstrap" }).click();

  await expect(page.getByRole("dialog", { name: "New Project" })).not.toBeVisible();
  await expect(page.getByRole("heading", { name: "Calculator Confirmed" })).toBeVisible();
});

test("supports api-only project creation contract via browser fetch", async ({ page }) => {
  await installMockApi(page);
  await page.goto("/?section=projects");

  const responseStatus = await page.evaluate(async () => {
    const response = await fetch("/api/v1/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: "Calculator API Only",
        description: "Create project without bootstrap kickoff",
      }),
    });
    return response.status;
  });

  expect(responseStatus).toBe(201);

  await page.reload();
  await page.getByRole("button", { name: "Projects" }).click();
  await expect(page.getByRole("button", { name: "Calculator API Only" })).toBeVisible();
  await expect(page.getByText("Board")).toBeVisible();
});
