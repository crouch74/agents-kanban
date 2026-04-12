import { expect, type Page } from "@playwright/test";

type MockState = {
  project: any | null;
  board: { id: string; project_id: string; name: string; columns: any[]; tasks: any[] };
  sessions: any[];
  waitingQuestions: any[];
  repliesByQuestionId: Record<string, any[]>;
  events: any[];
};

type MockApiOptions = {
  requireBootstrapConfirmation?: boolean;
};

function nowIso() {
  return "2026-04-11T10:00:00Z";
}

function createInitialState(): MockState {
  return {
    project: null,
    board: {
      id: "board-bootstrap",
      project_id: "project-bootstrap",
      name: "Main Board",
      columns: [
        { id: "col-todo", key: "todo", name: "Todo", order_index: 0, wip_limit: null },
        { id: "col-in-progress", key: "in_progress", name: "In Progress", order_index: 1, wip_limit: null },
        { id: "col-done", key: "done", name: "Done", order_index: 2, wip_limit: null },
      ],
      tasks: [],
    },
    sessions: [],
    waitingQuestions: [],
    repliesByQuestionId: {},
    events: [],
  };
}

export async function installMockApi(page: Page, options: MockApiOptions = {}) {
  const state = createInitialState();
  let taskCounter = 1;
  let sessionCounter = 1;
  let questionCounter = 1;
  const requireBootstrapConfirmation = Boolean(options.requireBootstrapConfirmation);

  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const method = request.method();
    const url = new URL(request.url());
    const path = url.pathname;

    const json = (body: unknown, status = 200) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });

    if (path.endsWith("/dashboard")) {
      return json({
        projects: state.project ? [state.project] : [],
        recent_events: state.events.slice(0, 10),
        waiting_questions: state.waitingQuestions.filter((q) => q.status === "open"),
        blocked_tasks: state.board.tasks.filter((t) => t.waiting_for_human),
        active_sessions: state.sessions.filter((s) => s.status === "running"),
        waiting_count: state.waitingQuestions.filter((q) => q.status === "open").length,
        blocked_count: state.board.tasks.filter((t) => t.waiting_for_human).length,
        running_sessions: state.sessions.filter((s) => s.status === "running").length,
      });
    }

    if (path.endsWith("/diagnostics")) {
      return json({
        app_name: "Agent Control Plane",
        environment: "test",
        database_path: ".acp/acp.sqlite3",
        runtime_home: ".acp",
        tmux_available: true,
        tmux_server_running: false,
        runtime_managed_session_count: state.sessions.length,
        orphan_runtime_session_count: 0,
        orphan_runtime_sessions: [],
        reconciled_session_count: state.sessions.length,
        stale_worktree_count: 0,
        stale_worktrees: [],
        git_available: true,
        current_project_count: state.project ? 1 : 0,
        current_repository_count: 1,
        current_task_count: state.board.tasks.length,
        current_worktree_count: 0,
        current_session_count: state.sessions.length,
        current_open_question_count: state.waitingQuestions.filter((q) => q.status === "open").length,
        current_event_count: state.events.length,
      });
    }

    if (path.endsWith("/projects") && method === "GET") {
      return json(state.project ? [state.project] : []);
    }

    if (path.endsWith("/projects") && method === "POST") {
      const payload = request.postDataJSON() as any;
      state.project = {
        id: "project-created",
        name: payload.name,
        slug: String(payload.name).toLowerCase().replace(/\s+/g, "-"),
        description: payload.description ?? null,
        archived: false,
        created_at: nowIso(),
      };
      state.board = {
        id: "board-created",
        project_id: state.project.id,
        name: "Main Board",
        columns: [
          { id: "col-backlog", key: "backlog", name: "Backlog", order_index: 0, wip_limit: null },
          { id: "col-ready", key: "ready", name: "Ready", order_index: 1, wip_limit: null },
          { id: "col-in-progress", key: "in_progress", name: "In Progress", order_index: 2, wip_limit: null },
          { id: "col-review", key: "review", name: "Review", order_index: 3, wip_limit: null },
          { id: "col-done", key: "done", name: "Done", order_index: 4, wip_limit: null },
        ],
        tasks: [],
      };
      return json(state.project, 201);
    }

    if (path.endsWith("/projects/bootstrap/preview") && method === "POST") {
      const payload = request.postDataJSON() as any;
      return json({
        repo_path: payload.repo_path,
        stack_preset: payload.stack_preset,
        stack_notes: payload.stack_notes ?? null,
        use_worktree: Boolean(payload.use_worktree),
        repo_initialized_on_confirm: Boolean(payload.initialize_repo),
        scaffold_applied_on_confirm: true,
        has_existing_commits: requireBootstrapConfirmation,
        confirmation_required: requireBootstrapConfirmation,
        execution_path: payload.repo_path,
        execution_branch: "main",
        planned_changes: requireBootstrapConfirmation
          ? [
              {
                path: `${payload.repo_path}/.acp/project.local.json`,
                action: "create_or_update",
                description: "Write local ACP project context for kickoff.",
              },
            ]
          : [],
      });
    }

    if (path.endsWith("/events")) {
      return json(state.events.slice().reverse());
    }

    if (path.endsWith("/projects/bootstrap") && method === "POST") {
      const payload = request.postDataJSON() as any;
      if (requireBootstrapConfirmation && !payload.confirm_existing_repo) {
        return json(
          { detail: "Existing repositories require preview confirmation before bootstrap can modify ACP-managed files" },
          400,
        );
      }
      state.project = {
        id: "project-bootstrap",
        name: payload.name,
        slug: "bootstrap-demo",
        description: payload.description ?? null,
      };

      const kickoffTask = {
        id: `task-${taskCounter++}`,
        project_id: state.project.id,
        title: "Kick off planning and board setup",
        workflow_state: "in_progress",
        board_column_id: "col-in-progress",
        parent_task_id: null,
        blocked_reason: null,
        waiting_for_human: false,
        priority: "medium",
        tags: [],
      };
      state.board.tasks.push(kickoffTask);

      const kickoffSession = {
        id: `session-${sessionCounter++}`,
        project_id: state.project.id,
        task_id: kickoffTask.id,
        repository_id: "repo-bootstrap",
        worktree_id: null,
        profile: "executor",
        status: "running",
        session_name: "acp-bootstrap-kickoff",
        runtime_metadata: {},
      };
      state.sessions.push(kickoffSession);

      state.events.push({
        id: `event-${state.events.length + 1}`,
        actor_type: "human",
        actor_name: "operator",
        entity_type: "project",
        entity_id: state.project.id,
        event_type: "project.bootstrap",
        created_at: nowIso(),
        payload_json: { title: payload.name },
      });

      return json({
        project: state.project,
        repository: {
          id: "repo-bootstrap",
          project_id: state.project.id,
          name: "demo-repo",
          local_path: payload.repo_path,
          default_branch: "main",
          metadata_json: {},
        },
        kickoff_task: kickoffTask,
        kickoff_session: kickoffSession,
        kickoff_worktree: null,
        execution_path: payload.repo_path,
        execution_branch: "main",
        stack_preset: payload.stack_preset,
        stack_notes: payload.stack_notes ?? null,
        use_worktree: Boolean(payload.use_worktree),
        repo_initialized: Boolean(payload.initialize_repo),
        scaffold_applied: true,
      });
    }

    if (path.match(/\/api\/v1\/projects\/[^/]+$/) && method === "GET") {
      return json({
        project: state.project,
        board: state.board,
        repositories: [
          {
            id: "repo-bootstrap",
            project_id: "project-bootstrap",
            name: "demo-repo",
            local_path: "/tmp/demo-repo",
            default_branch: "main",
            metadata_json: {},
          },
        ],
        worktrees: [],
        sessions: state.sessions,
        waiting_questions: state.waitingQuestions,
      });
    }

    if (path.endsWith("/questions") && method === "GET") {
      return json(state.waitingQuestions);
    }

    if (path.endsWith("/tasks") && method === "POST") {
      const payload = request.postDataJSON() as any;
      const task = {
        id: `task-${taskCounter++}`,
        project_id: payload.project_id,
        title: payload.title,
        workflow_state: "todo",
        board_column_id: "col-todo",
        parent_task_id: null,
        blocked_reason: null,
        waiting_for_human: false,
        priority: payload.priority ?? "medium",
        tags: [],
      };
      state.board.tasks.push(task);
      return json(task, 201);
    }

    if (path.match(/\/api\/v1\/tasks\/[^/]+$/) && method === "PATCH") {
      const taskId = path.split("/").at(-1)!;
      const payload = request.postDataJSON() as any;
      const task = state.board.tasks.find((item) => item.id === taskId);
      if (!task) return json({ detail: "not found" }, 404);
      if (payload.board_column_id) {
        task.board_column_id = payload.board_column_id;
      }
      if (payload.waiting_for_human !== undefined) {
        task.waiting_for_human = payload.waiting_for_human;
      }
      const columnKey = state.board.columns.find((c) => c.id === task.board_column_id)?.key;
      if (columnKey === "done") task.workflow_state = "done";
      if (columnKey === "in_progress") task.workflow_state = "in_progress";
      if (columnKey === "todo") task.workflow_state = "todo";
      return json(task);
    }

    if (path.match(/\/api\/v1\/tasks\/[^/]+\/detail$/) && method === "GET") {
      const taskId = path.split("/")[4]!;
      const task = state.board.tasks.find((item) => item.id === taskId);
      if (!task) return json({ detail: "not found" }, 404);
      return json({
        ...task,
        description: "Mocked task detail",
        dependencies: [],
        comments: [],
        checks: [],
        artifacts: [],
        waiting_questions: state.waitingQuestions.filter((q) => q.task_id === taskId),
      });
    }

    if (path.endsWith("/questions") && method === "POST") {
      const payload = request.postDataJSON() as any;
      const question = {
        id: `question-${questionCounter++}`,
        project_id: "project-bootstrap",
        task_id: payload.task_id,
        session_id: payload.session_id ?? null,
        prompt: payload.prompt,
        blocked_reason: payload.blocked_reason ?? null,
        urgency: payload.urgency ?? "medium",
        status: "open",
        created_at: nowIso(),
      };
      state.waitingQuestions.push(question);
      const task = state.board.tasks.find((item) => item.id === payload.task_id);
      if (task) task.waiting_for_human = true;
      state.repliesByQuestionId[question.id] = [];
      return json(question, 201);
    }

    if (path.match(/\/api\/v1\/questions\/[^/]+$/) && method === "GET") {
      const questionId = path.split("/").at(-1)!;
      const question = state.waitingQuestions.find((item) => item.id === questionId);
      if (!question) return json({ detail: "not found" }, 404);
      return json({ ...question, replies: state.repliesByQuestionId[questionId] ?? [] });
    }

    if (path.match(/\/api\/v1\/questions\/[^/]+\/replies$/) && method === "POST") {
      const questionId = path.split("/")[4]!;
      const payload = request.postDataJSON() as any;
      const question = state.waitingQuestions.find((item) => item.id === questionId);
      if (!question) return json({ detail: "not found" }, 404);
      const reply = {
        id: `reply-${(state.repliesByQuestionId[questionId]?.length ?? 0) + 1}`,
        question_id: questionId,
        responder_name: payload.responder_name,
        body: payload.body,
        payload_json: {},
        created_at: nowIso(),
      };
      state.repliesByQuestionId[questionId] = [...(state.repliesByQuestionId[questionId] ?? []), reply];
      question.status = "closed";
      const task = state.board.tasks.find((item) => item.id === question.task_id);
      if (task) {
        task.waiting_for_human = state.waitingQuestions.some(
          (item) => item.task_id === question.task_id && item.status === "open" && item.id !== questionId,
        );
      }
      return json({ ...question, replies: state.repliesByQuestionId[questionId] });
    }

    if (path.match(/\/api\/v1\/sessions\/[^/]+\/tail$/) && method === "GET") {
      const sessionId = path.split("/")[4]!;
      const session = state.sessions.find((item) => item.id === sessionId);
      if (!session) return json({ detail: "not found" }, 404);
      return json({
        session,
        lines: ["[agent] planning", "[agent] progressing"],
        recent_messages: [],
      });
    }

    if (path.match(/\/api\/v1\/sessions\/[^/]+\/timeline$/) && method === "GET") {
      const sessionId = path.split("/")[4]!;
      const session = state.sessions.find((item) => item.id === sessionId);
      if (!session) return json({ detail: "not found" }, 404);
      return json({
        session,
        runs: [],
        messages: [{ id: "msg-1", session_id: sessionId, message_type: "comment", source: "agent", body: "Implemented slice", payload_json: {}, created_at: nowIso() }],
        waiting_questions: state.waitingQuestions.filter((q) => q.session_id === sessionId),
        events: [{ id: "event-session", actor_type: "system", actor_name: "system", entity_type: "session", entity_id: sessionId, event_type: "session.started", created_at: nowIso(), payload_json: {} }],
        related_sessions: state.sessions.filter((s) => s.task_id === session.task_id),
      });
    }

    if (path.match(/\/api\/v1\/sessions\/[^/]+\/follow-up$/) && method === "POST") {
      const baseSessionId = path.split("/")[4]!;
      const baseSession = state.sessions.find((item) => item.id === baseSessionId);
      if (!baseSession) return json({ detail: "not found" }, 404);
      const followUp = {
        ...baseSession,
        id: `session-${sessionCounter++}`,
        status: "running",
        session_name: `${baseSession.session_name}-retry`,
      };
      state.sessions.push(followUp);
      return json(followUp, 201);
    }

    return json({ ok: true });
  });
}

export async function bootstrapProject(page: Page, name: string) {
  await page.goto("/?section=projects");
  await expect(page.getByText("Agent Control Plane")).toBeVisible();
  await page.getByRole("button", { name: "Projects" }).click();
  await page.getByRole("button", { name: /\+ new project/i }).click();
  await page.getByPlaceholder("Acme migration program").fill(name);
  await page.getByPlaceholder("/absolute/path/to/repo").fill(`/tmp/${name.toLowerCase().replace(/\s+/g, "-")}`);
  await page
    .getByPlaceholder(
      "Describe the work to kick off. ACP will ask the agent to clarify requirements and create tasks/subtasks.",
    )
    .fill("Kick off a stable deterministic plan.");
  await page.getByRole("button", { name: "Review bootstrap" }).click();
  await expect(page.getByRole("dialog", { name: "New Project" })).not.toBeVisible();
  await expect(page.getByRole("heading", { name })).toBeVisible();
  await expect(page.getByText("Kick off planning and board setup").first()).toBeVisible();
}
