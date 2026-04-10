import type {
  BoardView,
  ProjectSummary,
  RepositorySummary,
  SessionSummary,
  TaskSummary,
  WaitingQuestionSummary,
  WorktreeSummary,
} from "@acp/sdk";

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
  sessions: SessionSummary[];
  waiting_questions: WaitingQuestionSummary[];
};

export type SessionTail = {
  session: SessionSummary;
  lines: string[];
  recent_messages: Array<{
    id: string;
    session_id: string;
    message_type: string;
    source: string;
    body: string;
    payload_json: Record<string, unknown>;
    created_at: string;
  }>;
};

export type WaitingQuestionDetail = WaitingQuestionSummary & {
  replies: Array<{
    id: string;
    question_id: string;
    responder_name: string;
    body: string;
    payload_json: Record<string, unknown>;
    created_at: string;
  }>;
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

export function createSession(payload: {
  task_id: string;
  profile: string;
  repository_id?: string;
  worktree_id?: string;
  command?: string;
}) {
  return postJson<SessionSummary>("/sessions", payload);
}

export function getSessionTail(sessionId: string) {
  return fetchJson<SessionTail>(`/sessions/${sessionId}/tail`);
}

export function createQuestion(payload: {
  task_id: string;
  session_id?: string;
  prompt: string;
  blocked_reason?: string;
  urgency?: string;
  options_json?: Array<Record<string, unknown>>;
}) {
  return postJson<WaitingQuestionSummary>("/questions", payload);
}

export function getQuestion(questionId: string) {
  return fetchJson<WaitingQuestionDetail>(`/questions/${questionId}`);
}

export function answerQuestion(
  questionId: string,
  payload: { responder_name: string; body: string; payload_json?: Record<string, unknown> },
) {
  return postJson<WaitingQuestionDetail>(`/questions/${questionId}/replies`, payload);
}
