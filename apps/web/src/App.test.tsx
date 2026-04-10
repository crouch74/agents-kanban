import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { expect, test, vi } from "vitest";
import { App } from "./App";

vi.stubGlobal(
  "fetch",
  vi.fn(async (input: string) => {
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
