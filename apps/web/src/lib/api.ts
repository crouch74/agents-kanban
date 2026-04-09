import type { BoardView, ProjectSummary, RepositorySummary, TaskSummary, WorktreeSummary } from "@acp/sdk";

const API_BASE = "http://127.0.0.1:8000/api/v1";

type Diagnostics = {
  app_name: string;
  environment: string;
  database_path: string;
  runtime_home: string;
  tmux_available: boolean;
  git_available: boolean;
  current_project_count: number;
  current_task_count: number;
};

type EventRecord = {
  id: string;
  actor_type: string;
  actor_name: string;
  entity_type: string;
  entity_id: string;
  event_type: string;
  created_at: string;
  payload_json: Record<string, unknown>;
};

export type Dashboard = {
  projects: ProjectSummary[];
  recent_events: EventRecord[];
  waiting_count: number;
  blocked_count: number;
  running_sessions: number;
};

type ProjectOverview = {
  project: ProjectSummary;
  board: BoardView;
  repositories: RepositorySummary[];
  worktrees: WorktreeSummary[];
};

export async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function patchJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export function getDashboard() {
  return fetchJson<Dashboard>("/dashboard");
}

export function getDiagnostics() {
  return fetchJson<Diagnostics>("/diagnostics");
}

export function getProjects() {
  return fetchJson<ProjectSummary[]>("/projects");
}

export function createProject(payload: { name: string; description?: string }) {
  return postJson<ProjectSummary>("/projects", payload);
}

export function getProject(projectId: string) {
  return fetchJson<ProjectOverview>(`/projects/${projectId}`);
}

export function createTask(payload: {
  project_id: string;
  title: string;
  description?: string;
  priority?: string;
  board_column_key?: string;
}) {
  return postJson<TaskSummary>("/tasks", payload);
}

export function createRepository(payload: { project_id: string; local_path: string; name?: string }) {
  return postJson<RepositorySummary>("/repositories", payload);
}

export function createWorktree(payload: { repository_id: string; task_id?: string; label?: string }) {
  return postJson<WorktreeSummary>("/worktrees", payload);
}

export function patchWorktree(worktreeId: string, payload: { status: string; lock_reason?: string }) {
  return patchJson<WorktreeSummary>(`/worktrees/${worktreeId}`, payload);
}
