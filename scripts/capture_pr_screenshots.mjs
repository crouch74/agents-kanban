import { mkdir } from "node:fs/promises";
import path from "node:path";
import { chromium } from "@playwright/test";

const baseUrl = process.env.ACP_SCREENSHOT_BASE_URL ?? "http://127.0.0.1:5173";
const outputDir = path.resolve(".artifacts/pr-screenshots");

const views = [
  { name: "dashboard-home", section: "home" },
  { name: "project-board-tasks", section: "projects" },
  { name: "activity-stream", section: "activity" },
];

async function capture() {
  await mkdir(outputDir, { recursive: true });

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page = await context.newPage();

  try {
    for (const view of views) {
      const url = `${baseUrl}/?section=${view.section}`;
      await page.goto(url, { waitUntil: "networkidle" });
      await page.getByText("Local operator workspace").waitFor({ timeout: 15000 });
      const targetPath = path.join(outputDir, `${view.name}.png`);
      await page.screenshot({ path: targetPath, fullPage: true });
      console.log(`Captured ${view.name} -> ${targetPath}`);
    }
  } finally {
    await context.close();
    await browser.close();
  }
}

capture().catch((error) => {
  console.error("Failed to capture PR screenshots.", error);
  process.exit(1);
});
