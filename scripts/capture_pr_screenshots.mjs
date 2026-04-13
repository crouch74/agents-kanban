import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { chromium } from '@playwright/test';

const BASE_URL = process.env.PR_SCREENSHOT_BASE_URL ?? 'http://127.0.0.1:5173';
const OUTPUT_DIR = path.resolve('.artifacts/pr-screenshots');

const targets = [
  { route: '/', fileName: 'dashboard-home.png' },
  { route: '/projects', fileName: 'project-board-tasks.png' },
  { route: '/activity', fileName: 'activity-stream.png' },
];

async function capture() {
  await mkdir(OUTPUT_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });

  try {
    const page = await context.newPage();

    for (const target of targets) {
      const url = `${BASE_URL}${target.route}`;
      await page.goto(url, { waitUntil: 'networkidle', timeout: 30_000 });
      await page.screenshot({
        path: path.join(OUTPUT_DIR, target.fileName),
        fullPage: true,
      });
    }
  } finally {
    await context.close();
    await browser.close();
  }
}

capture().catch((error) => {
  console.error('Failed to capture PR screenshots.', error);
  process.exitCode = 1;
});
