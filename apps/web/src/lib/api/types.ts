import type { ProjectSummary, TaskPriority, WorkflowState } from "@acp/sdk";

export type BoardColumn = {
  id: string;
  key: WorkflowState;
  name: string;
  position: number;
  wip_limit?: number | null;
};

export type TaskSummary = {
  id: string;
  project_id: string;
  board_column_id: string;
  title: string;
  description?: string | null;
  workflow_state: WorkflowState;
  priority: TaskPriority;
  tags: string[];
  assignee?: string | null;
  source?: string | null;
  created_at: string;
  updated_at: string;
};

export type TaskComment = {
  id: string;
  task_id: string;
  author_type: string;
  author_name: string;
  source?: string | null;
  body: string;
  metadata_json: Record<string, unknown>;
  created_at: string;
};

export type TaskDetail = TaskSummary & {
  comments: TaskComment[];
};

export type BoardView = {
  id: string;
  project_id: string;
  name: string;
  columns: BoardColumn[];
  tasks: TaskSummary[];
};

export type ProjectOverview = {
  project: ProjectSummary;
  board: BoardView;
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
  task_counts: Record<string, number>;
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

export type Diagnostics = {
  app_name: string;
  environment: string;
  services: Record<string, { status: string; detail?: string | null }>;
  paths: Record<string, string>;
  row_counts: Record<string, number>;
};

export type PurgeDatabaseResult = {
  status: string;
  purged_tables: number;
  rows_deleted: number;
  database_path: string;
};

// Legacy compatibility placeholders for non-active control-plane modules.
export type RuntimeOrphanCleanup = {
  removed_runtime_session_count: number;
  removed_runtime_sessions: string[];
};

export type SessionTail = {
  session: Record<string, unknown>;
  lines: string[];
  recent_messages: Array<Record<string, unknown>>;
};

export type SessionTimeline = {
  session: Record<string, unknown>;
  runs: Array<Record<string, unknown>>;
  messages: Array<Record<string, unknown>>;
  waiting_questions: Array<Record<string, unknown>>;
  events: EventRecord[];
  related_sessions: Array<Record<string, unknown>>;
};

export type WaitingQuestionDetail = {
  id: string;
  prompt: string;
  replies: Array<{
    id: string;
    responder_name: string;
    body: string;
    created_at: string;
  }>;
};
