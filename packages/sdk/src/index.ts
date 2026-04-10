export type WorkflowState =
  | "backlog"
  | "ready"
  | "in_progress"
  | "review"
  | "done"
  | "cancelled";

export type StackPreset =
  | "node-library"
  | "react-vite"
  | "nextjs"
  | "python-package"
  | "fastapi-service";

export interface BoardColumn {
  id: string;
  name: string;
  key: WorkflowState;
  position: number;
  wip_limit?: number | null;
}

export interface TaskSummary {
  id: string;
  project_id: string;
  title: string;
  workflow_state: WorkflowState;
  board_column_id: string;
  parent_task_id?: string | null;
  blocked_reason?: string | null;
  waiting_for_human: boolean;
  priority: string;
  tags: string[];
}

export interface BoardView {
  id: string;
  project_id: string;
  name: string;
  columns: BoardColumn[];
  tasks: TaskSummary[];
}

export interface ProjectSummary {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
}

export interface RepositorySummary {
  id: string;
  project_id: string;
  name: string;
  local_path: string;
  default_branch?: string | null;
  metadata_json: Record<string, unknown>;
}

export interface WorktreeSummary {
  id: string;
  repository_id: string;
  task_id?: string | null;
  branch_name: string;
  path: string;
  status: string;
  lock_reason?: string | null;
  metadata_json: Record<string, unknown>;
}

export interface SessionSummary {
  id: string;
  project_id: string;
  task_id: string;
  repository_id?: string | null;
  worktree_id?: string | null;
  profile: string;
  status: string;
  session_name: string;
  runtime_metadata: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
}

export interface WaitingQuestionSummary {
  id: string;
  project_id: string;
  task_id: string;
  session_id?: string | null;
  status: string;
  prompt: string;
  blocked_reason?: string | null;
  urgency?: string | null;
  options_json: Array<Record<string, unknown>>;
}

export interface ProjectBootstrapResult {
  project: ProjectSummary;
  repository: RepositorySummary;
  kickoff_task: TaskSummary;
  kickoff_session: SessionSummary;
  kickoff_worktree?: WorktreeSummary | null;
  execution_path: string;
  execution_branch: string;
  stack_preset: StackPreset;
  stack_notes?: string | null;
  use_worktree: boolean;
  repo_initialized: boolean;
  scaffold_applied: boolean;
}
