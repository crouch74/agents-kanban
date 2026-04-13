import type {
  BoardView,
  ProjectSummary,
  RepositorySummary,
  SessionSummary,
  TaskSummary,
  WaitingQuestionSummary,
  WorktreeSummary,
  WorktreeRecommendation,
  WorktreeStatus,
  DependencyRelationshipType,
  AuthorType,
  CheckStatus,
  SessionStatus,
} from "@acp/sdk";

export type Diagnostics = {
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
    status: WorktreeStatus;
    recommendation: WorktreeRecommendation;
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

export type RuntimeOrphanCleanup = {
  removed_runtime_session_count: number;
  removed_runtime_sessions: string[];
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

export type SearchHit = SearchResults["hits"][number];

export type ProjectOverview = {
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
    status: SessionStatus;
    summary?: string | null;
    runtime_metadata: Record<string, unknown>;
    created_at: string;
  }>;
  messages: SessionTail["recent_messages"];
  waiting_questions: WaitingQuestionSummary[];
  events: EventRecord[];
  related_sessions: SessionSummary[];
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
    relationship_type: DependencyRelationshipType;
    created_at: string;
  }>;
  comments: Array<{
    id: string;
    task_id: string;
    author_type: AuthorType;
    author_name: string;
    body: string;
    metadata_json: Record<string, unknown>;
    created_at: string;
  }>;
  checks: Array<{
    id: string;
    task_id: string;
    check_type: string;
    status: CheckStatus;
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
