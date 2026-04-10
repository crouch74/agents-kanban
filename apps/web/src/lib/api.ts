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
  tmux_server_running: boolean;
  runtime_managed_session_count: number;
  orphan_runtime_session_count: number;
  orphan_runtime_sessions: string[];
  reconciled_session_count: number;
  stale_worktree_count: number;
  stale_worktrees: Array<{
    worktree_id: string;
    project_id?: string | null;
    task_id?: string | null;
    session_id?: string | null;
    branch_name: string;
    path: string;
    status: string;
    recommendation: "archive" | "prune" | "inspect";
    reasons: string[];
  }>;
  git_available: boolean;
  current_project_count: number;
  current_repository_count: number;
  current_task_count: number;
  current_worktree_count: number;
  current_session_count: number;
  current_open_question_count: number;
  current_event_count: number;
};

export type EventRecord = {
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
  waiting_questions: WaitingQuestionSummary[];
  blocked_tasks: TaskSummary[];
  active_sessions: SessionSummary[];
  waiting_count: number;
  blocked_count: number;
  running_sessions: number;
};

export type SearchResults = {
  query: string;
  hits: Array<{
    entity_type: string;
    entity_id: string;
    project_id?: string | null;
    title: string;
    snippet: string;
    secondary?: string | null;
    created_at: string;
  }>;
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

export type SessionTimeline = {
  session: SessionSummary;
  runs: Array<{
    id: string;
    session_id: string;
    attempt_number: number;
    status: string;
    summary?: string | null;
    runtime_metadata: Record<string, unknown>;
    created_at: string;
  }>;
  messages: SessionTail["recent_messages"];
  waiting_questions: WaitingQuestionSummary[];
  events: EventRecord[];
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

export type TaskDetail = TaskSummary & {
  description?: string | null;
  dependencies: Array<{
    id: string;
    task_id: string;
    depends_on_task_id: string;
    relationship_type: string;
    created_at: string;
  }>;
  comments: Array<{
    id: string;
    task_id: string;
    author_type: string;
    author_name: string;
    body: string;
    metadata_json: Record<string, unknown>;
    created_at: string;
  }>;
  checks: Array<{
    id: string;
    task_id: string;
    check_type: string;
    status: string;
    summary: string;
    payload_json: Record<string, unknown>;
    created_at: string;
  }>;
  artifacts: Array<{
    id: string;
    task_id: string;
    artifact_type: string;
    name: string;
    uri: string;
    payload_json: Record<string, unknown>;
    created_at: string;
  }>;
  waiting_questions: WaitingQuestionSummary[];
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

export function getEvents(params?: { projectId?: string; taskId?: string; sessionId?: string; limit?: number }) {
  const search = new URLSearchParams();
  if (params?.projectId) {
    search.set("project_id", params.projectId);
  }
  if (params?.taskId) {
    search.set("task_id", params.taskId);
  }
  if (params?.sessionId) {
    search.set("session_id", params.sessionId);
  }
  if (params?.limit) {
    search.set("limit", String(params.limit));
  }
  const suffix = search.size ? `?${search.toString()}` : "";
  return fetchJson<EventRecord[]>(`/events${suffix}`);
}

export function getDiagnostics() {
  return fetchJson<Diagnostics>("/diagnostics");
}

export function getProjects() {
  return fetchJson<ProjectSummary[]>("/projects");
}

export function searchContext(query: string, projectId?: string) {
  const params = new URLSearchParams({ q: query });
  if (projectId) {
    params.set("project_id", projectId);
  }
  return fetchJson<SearchResults>(`/search?${params.toString()}`);
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
  parent_task_id?: string;
  board_column_key?: string;
}) {
  return postJson<TaskSummary>("/tasks", payload);
}

export function patchTask(
  taskId: string,
  payload: {
    title?: string;
    description?: string;
    workflow_state?: string;
    board_column_id?: string;
    blocked_reason?: string | null;
    waiting_for_human?: boolean;
  },
) {
  return patchJson<TaskSummary>(`/tasks/${taskId}`, payload);
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

export function getSessionTimeline(sessionId: string) {
  return fetchJson<SessionTimeline>(`/sessions/${sessionId}/timeline`);
}

export function cancelSession(sessionId: string) {
  return postJson<SessionSummary>(`/sessions/${sessionId}/cancel`, {});
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

export function getTaskDetail(taskId: string) {
  return fetchJson<TaskDetail>(`/tasks/${taskId}/detail`);
}

export function addTaskComment(
  taskId: string,
  payload: { author_type?: string; author_name: string; body: string; metadata_json?: Record<string, unknown> },
) {
  return postJson<TaskDetail["comments"][number]>(`/tasks/${taskId}/comments`, payload);
}

export function addTaskCheck(
  taskId: string,
  payload: { check_type: string; status: string; summary: string; payload_json?: Record<string, unknown> },
) {
  return postJson<TaskDetail["checks"][number]>(`/tasks/${taskId}/checks`, payload);
}

export function addTaskArtifact(
  taskId: string,
  payload: { artifact_type: string; name: string; uri: string; payload_json?: Record<string, unknown> },
) {
  return postJson<TaskDetail["artifacts"][number]>(`/tasks/${taskId}/artifacts`, payload);
}

export function addTaskDependency(
  taskId: string,
  payload: { depends_on_task_id: string; relationship_type?: string },
) {
  return postJson<TaskDetail["dependencies"][number]>(`/tasks/${taskId}/dependencies`, payload);
}
