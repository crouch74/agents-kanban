import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { expect, test, vi } from "vitest";
import { App } from "./App";

vi.stubGlobal(
  "fetch",
  vi.fn(async (input: string, init?: RequestInit) => {
    if (input.endsWith("/dashboard")) {
      return new Response(
        JSON.stringify({
          projects: [],
          recent_events: [],
          waiting_questions: [],
          blocked_tasks: [],
          active_sessions: [],
          waiting_count: 0,
          blocked_count: 0,
          running_sessions: 0,
        }),
      );
    }

    if (input.endsWith("/diagnostics")) {
      return new Response(
        JSON.stringify({
          app_name: "Agent Control Plane",
          environment: "test",
          database_path: ".acp/acp.sqlite3",
          runtime_home: ".acp",
          tmux_available: true,
          tmux_server_running: false,
          runtime_managed_session_count: 0,
          orphan_runtime_session_count: 0,
          orphan_runtime_sessions: [],
          reconciled_session_count: 0,
          stale_worktree_count: 0,
          stale_worktrees: [],
          git_available: true,
          current_project_count: 0,
          current_repository_count: 0,
          current_task_count: 0,
          current_worktree_count: 0,
          current_session_count: 0,
          current_open_question_count: 0,
          current_event_count: 0,
        }),
      );
    }

    if (input.endsWith("/projects")) {
      return new Response(JSON.stringify([]));
    }

    if (input.endsWith("/projects/bootstrap") && init?.method === "POST") {
      return new Response(
        JSON.stringify({
          project: {
            id: "project-1",
            name: "Bootstrap Demo",
            slug: "bootstrap-demo",
            description: "demo",
          },
          repository: {
            id: "repo-1",
            project_id: "project-1",
            name: "demo-repo",
            local_path: "/tmp/demo-repo",
            default_branch: "main",
            metadata_json: {},
          },
          kickoff_task: {
            id: "task-1",
            project_id: "project-1",
            title: "Kick off planning and board setup",
            workflow_state: "in_progress",
            board_column_id: "column-1",
            parent_task_id: null,
            blocked_reason: null,
            waiting_for_human: false,
            priority: "medium",
            tags: [],
          },
          kickoff_session: {
            id: "session-1",
            project_id: "project-1",
            task_id: "task-1",
            repository_id: "repo-1",
            worktree_id: null,
            profile: "executor",
            status: "running",
            session_name: "acp-project-1",
            runtime_metadata: {},
          },
          kickoff_worktree: null,
          execution_path: "/tmp/demo-repo",
          execution_branch: "main",
          stack_preset: "nextjs",
          stack_notes: "demo notes",
          use_worktree: false,
          repo_initialized: true,
          scaffold_applied: true,
        }),
      );
    }

    if (input.endsWith("/projects/project-1")) {
      return new Response(
        JSON.stringify({
          project: {
            id: "project-1",
            name: "Bootstrap Demo",
            slug: "bootstrap-demo",
            description: "demo",
          },
          board: { id: "board-1", project_id: "project-1", name: "Main Board", columns: [], tasks: [] },
          repositories: [],
          worktrees: [],
          sessions: [],
          waiting_questions: [],
        }),
      );
    }

    if (input.includes("/events")) {
      return new Response(JSON.stringify([]));
    }

    return new Response(JSON.stringify({ project: null, board: null }), { status: 200 });
  }),
);

test("renders the operator workspace heading", async () => {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <App />
    </QueryClientProvider>,
  );

  expect(await screen.findByText("Local operator workspace")).toBeInTheDocument();
});

test("submits the bootstrap wizard and shows the kickoff summary", async () => {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <App />
    </QueryClientProvider>,
  );

  fireEvent.change(screen.getByPlaceholderText("Acme migration program"), {
    target: { value: "Bootstrap Demo" },
  });
  fireEvent.change(screen.getByPlaceholderText("/absolute/path/to/repo"), {
    target: { value: "/tmp/demo-repo" },
  });
  fireEvent.change(
    screen.getByPlaceholderText(
      "Describe the work to kick off. ACP will ask the agent to clarify requirements and create tasks/subtasks.",
    ),
    {
      target: { value: "Plan the initial implementation and create tasks." },
    },
  );
  fireEvent.click(screen.getByRole("button", { name: /launch bootstrap/i }));

  await waitFor(() => {
    expect(screen.getByText("Bootstrap Demo is ready")).toBeInTheDocument();
  });
  expect(screen.getByText("Kickoff task: Kick off planning and board setup")).toBeInTheDocument();
});
