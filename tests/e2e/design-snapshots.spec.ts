import { expect, test } from "@playwright/test";

const PROJECT_ID = "project-1";

const json = (payload: unknown) => ({
  status: 200,
  contentType: "application/json",
  body: JSON.stringify(payload),
});

test("captures dashboard, project board, and activity screenshots", async ({ page }, testInfo) => {
  await page.route("http://127.0.0.1:8000/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());

    if (url.pathname.endsWith("/dashboard")) {
      await route.fulfill(
        json({
          projects: [
            { id: PROJECT_ID, name: "Dummy Project", slug: "dummy-project", description: "Pipeline screenshots fixture" },
          ],
          recent_events: [],
          waiting_questions: [],
          blocked_tasks: [],
          active_sessions: [],
          waiting_count: 0,
          blocked_count: 0,
          running_sessions: 1,
        }),
      );
      return;
    }

    if (url.pathname.endsWith("/diagnostics")) {
      await route.fulfill(
        json({
          app_name: "Agent Control Plane",
          environment: "ci",
          database_path: ".acp/acp.sqlite3",
          runtime_home: ".acp",
          tmux_available: true,
          tmux_server_running: true,
          runtime_managed_session_count: 1,
          orphan_runtime_session_count: 0,
          orphan_runtime_sessions: [],
          reconciled_session_count: 1,
          stale_worktree_count: 0,
          stale_worktrees: [],
          git_available: true,
          current_project_count: 1,
          current_repository_count: 1,
          current_task_count: 2,
          current_worktree_count: 1,
          current_session_count: 1,
          current_open_question_count: 0,
          current_event_count: 2,
        }),
      );
      return;
    }

    if (url.pathname.endsWith("/projects")) {
      await route.fulfill(
        json([
          { id: PROJECT_ID, name: "Dummy Project", slug: "dummy-project", description: "Pipeline screenshots fixture" },
        ]),
      );
      return;
    }

    if (url.pathname.endsWith(`/projects/${PROJECT_ID}`)) {
      await route.fulfill(
        json({
          project: {
            id: PROJECT_ID,
            name: "Dummy Project",
            slug: "dummy-project",
            description: "Pipeline screenshots fixture",
          },
          board: {
            id: "board-1",
            project_id: PROJECT_ID,
            name: "Main Board",
            columns: [
              { id: "col-1", board_id: "board-1", name: "Backlog", position: 1 },
              { id: "col-2", board_id: "board-1", name: "In Progress", position: 2 },
              { id: "col-3", board_id: "board-1", name: "Done", position: 3 },
            ],
            tasks: [
              {
                id: "task-1",
                project_id: PROJECT_ID,
                title: "Create dummy workflow tasks",
                workflow_state: "ready",
                board_column_id: "col-1",
                parent_task_id: null,
                blocked_reason: null,
                waiting_for_human: false,
                priority: "medium",
                tags: ["demo"],
              },
              {
                id: "task-2",
                project_id: PROJECT_ID,
                title: "Capture pipeline screenshots",
                workflow_state: "in_progress",
                board_column_id: "col-2",
                parent_task_id: null,
                blocked_reason: null,
                waiting_for_human: false,
                priority: "high",
                tags: ["ci"],
              },
            ],
          },
          repositories: [
            {
              id: "repo-1",
              project_id: PROJECT_ID,
              name: "dummy-repo",
              local_path: "/workspace/dummy-repo",
              default_branch: "main",
              metadata_json: {},
            },
          ],
          worktrees: [
            {
              id: "wt-1",
              project_id: PROJECT_ID,
              repository_id: "repo-1",
              task_id: "task-2",
              path: "/workspace/dummy-repo/.worktrees/task-2",
              branch_name: "task/task-2",
              status: "active",
              is_ephemeral: false,
              metadata_json: {},
            },
          ],
          sessions: [
            {
              id: "session-1",
              project_id: PROJECT_ID,
              task_id: "task-2",
              repository_id: "repo-1",
              worktree_id: "wt-1",
              profile: "executor",
              status: "running",
              session_name: "acp-dummy-project-task-2",
              runtime_metadata: {},
            },
          ],
          waiting_questions: [],
        }),
      );
      return;
    }

    if (url.pathname.endsWith("/events")) {
      await route.fulfill(
        json([
          {
            id: "event-1",
            actor_type: "system",
            actor_name: "acp",
            entity_type: "task",
            entity_id: "task-2",
            event_type: "task.updated",
            created_at: "2026-04-10T00:00:00Z",
            payload_json: { project_id: PROJECT_ID },
          },
        ]),
      );
      return;
    }

    await route.fulfill(json({}));
  });

  await page.goto("http://127.0.0.1:5173");
  await expect(page.getByText("Local operator workspace")).toBeVisible();

  await page.setViewportSize({ width: 1720, height: 1000 });
  await page.screenshot({ path: testInfo.outputPath("design-overview.png"), fullPage: true });

  await page.getByRole("button", { name: "Projects" }).click();
  await expect(page.getByText("Dummy Project")).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("design-projects.png"), fullPage: true });

  await page.getByRole("button", { name: "Activity" }).click();
  await expect(page.getByText("Event stream")).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("design-activity.png"), fullPage: true });
});
