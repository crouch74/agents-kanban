import { expect, test } from "@playwright/test";

const now = "2026-04-10T12:00:00Z";

const project = {
  id: "project-dummy-1",
  name: "Dummy Project",
  slug: "dummy-project",
  description: "Synthetic project used for UI screenshot capture.",
};

const boardColumns = [
  { id: "column-backlog", board_id: "board-1", name: "Backlog", position: 0, metadata_json: {} },
  { id: "column-ready", board_id: "board-1", name: "Ready", position: 1, metadata_json: {} },
  { id: "column-progress", board_id: "board-1", name: "In Progress", position: 2, metadata_json: {} },
  { id: "column-review", board_id: "board-1", name: "Review", position: 3, metadata_json: {} },
  { id: "column-done", board_id: "board-1", name: "Done", position: 4, metadata_json: {} },
];

const boardTasks = [
  {
    id: "task-1",
    project_id: project.id,
    title: "Map current repositories and migration paths",
    workflow_state: "in_progress",
    board_column_id: "column-progress",
    parent_task_id: null,
    blocked_reason: null,
    waiting_for_human: false,
    priority: "high",
    tags: ["migration", "planning"],
  },
  {
    id: "task-2",
    project_id: project.id,
    title: "Draft rollout runbook for agents",
    workflow_state: "review",
    board_column_id: "column-review",
    parent_task_id: null,
    blocked_reason: null,
    waiting_for_human: false,
    priority: "medium",
    tags: ["runbook"],
  },
];

test("capture operator UI screenshots with a dummy project", async ({ page }) => {
  await page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    const json = (payload: unknown) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(payload) });

    if (path.endsWith("/dashboard")) {
      return json({
        projects: [project],
        recent_events: [],
        waiting_questions: [],
        blocked_tasks: [],
        active_sessions: [],
        waiting_count: 0,
        blocked_count: 0,
        running_sessions: 1,
      });
    }

    if (path.endsWith("/diagnostics")) {
      return json({
        app_name: "Agent Control Plane",
        environment: "test",
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
      });
    }

    if (path.endsWith("/projects")) {
      return json([project]);
    }

    if (path.endsWith(`/projects/${project.id}`)) {
      return json({
        project,
        board: {
          id: "board-1",
          project_id: project.id,
          name: "Main Board",
          columns: boardColumns,
          tasks: boardTasks,
        },
        repositories: [
          {
            id: "repo-1",
            project_id: project.id,
            name: "dummy-repo",
            local_path: "/workspace/dummy-repo",
            default_branch: "main",
            metadata_json: {},
          },
        ],
        worktrees: [
          {
            id: "worktree-1",
            project_id: project.id,
            task_id: "task-1",
            repository_id: "repo-1",
            branch_name: "task-1",
            path: "/workspace/dummy-repo/.worktrees/task-1",
            status: "active",
            metadata_json: {},
          },
        ],
        sessions: [
          {
            id: "session-1",
            project_id: project.id,
            task_id: "task-1",
            repository_id: "repo-1",
            worktree_id: "worktree-1",
            profile: "executor",
            status: "running",
            session_name: "acp-dummy-project",
            runtime_metadata: {},
          },
        ],
        waiting_questions: [],
      });
    }

    if (path.endsWith("/events")) {
      return json([
        {
          id: "event-1",
          actor_type: "system",
          actor_name: "acp",
          entity_type: "task",
          entity_id: "task-1",
          event_type: "task.updated",
          created_at: now,
          payload_json: { workflow_state: "in_progress" },
        },
      ]);
    }

    if (path.endsWith("/search")) {
      return json({ query: url.searchParams.get("q") ?? "", hits: [] });
    }

    if (path.includes("/sessions/") && path.endsWith("/tail")) {
      return json({ session: null, lines: [], recent_messages: [] });
    }

    if (path.includes("/sessions/") && path.endsWith("/timeline")) {
      return json({ session: null, runs: [], messages: [], waiting_questions: [], events: [], related_sessions: [] });
    }

    if (path.includes("/tasks/")) {
      return json({
        ...boardTasks[0],
        description: "Dummy task details",
        dependencies: [],
        comments: [],
        checks: [],
        artifacts: [],
        waiting_questions: [],
      });
    }

    return json({});
  });

  await page.goto("http://127.0.0.1:5173");
  await expect(page.getByText("Local operator workspace")).toBeVisible();

  await page.screenshot({ path: "artifacts/screenshots/dashboard-dummy-project.png", fullPage: true });

  await page.getByRole("button", { name: "Projects" }).click();
  await expect(page.getByText("Dummy Project")).toBeVisible();
  await page.screenshot({ path: "artifacts/screenshots/projects-dummy-project.png", fullPage: true });

  await page.getByRole("button", { name: "Runtime" }).click();
  await expect(page.getByText("Agent sessions")).toBeVisible();
  await page.screenshot({ path: "artifacts/screenshots/runtime-dummy-project.png", fullPage: true });
});
