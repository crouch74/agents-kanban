export enum WorkflowState {
  BACKLOG = "backlog",
  IN_PROGRESS = "in_progress",
  DONE = "done",
}

export enum TaskKind {
  KICKOFF = "kickoff",
  EXECUTE = "execute",
  REVIEW = "review",
  VERIFY = "verify",
  RESEARCH = "research",
  DOCS = "docs",
}

export enum AgentProfile {
  EXECUTOR = "executor",
  REVIEWER = "reviewer",
  VERIFIER = "verifier",
  RESEARCH = "research",
  DOCS = "docs",
}

export enum Permission {
  DANGER_FULL_ACCESS = "danger-full-access",
}

export enum OutputMode {
  JSON = "json",
  STREAM_JSON = "stream-json",
}

export enum FollowUpType {
  RETRY = "retry",
  REVIEW = "review",
  VERIFY = "verify",
  HANDOFF = "handoff",
}

export enum TaskPriority {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  URGENT = "urgent",
}

export enum Urgency {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  URGENT = "urgent",
}

export enum SessionStatus {
  QUEUED = "queued",
  RUNNING = "running",
  WAITING_HUMAN = "waiting_human",
  BLOCKED = "blocked",
  DONE = "done",
  FAILED = "failed",
  CANCELLED = "cancelled",
}

export enum WorktreeStatus {
  LOCKED = "locked",
  ARCHIVED = "archived",
  PRUNED = "pruned",
}

export enum WorktreeAction {
  CREATE = "create",
  CREATE_OR_UPDATE = "create_or_update",
  APPEND_LINE = "append_line",
  SCAFFOLD = "scaffold",
}

export enum WorktreeRecommendation {
  ARCHIVE = "archive",
  PRUNE = "prune",
  INSPECT = "inspect",
}

export enum DependencyRelationshipType {
  BLOCKS = "blocks",
  RELATES_TO = "relates_to",
}

export enum AuthorType {
  HUMAN = "human",
  AGENT = "agent",
  SYSTEM = "system",
}

export enum CheckStatus {
  PENDING = "pending",
  PASSED = "passed",
  FAILED = "failed",
  WARNING = "warning",
}

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
  priority: TaskPriority;
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
  status: WorktreeStatus;
  lock_reason?: string | null;
  metadata_json: Record<string, unknown>;
}

export interface SessionSummary {
  id: string;
  project_id: string;
  task_id: string;
  repository_id?: string | null;
  worktree_id?: string | null;
  profile: AgentProfile;
  status: SessionStatus;
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
  created_at?: string;
  updated_at?: string;
}

export interface ProjectBootstrapPlannedChange {
  path: string;
  action: WorktreeAction;
  description: string;
}

export interface ProjectBootstrapPreview {
  repo_path: string;
  stack_preset: StackPreset;
  stack_notes?: string | null;
  use_worktree: boolean;
  repo_initialized_on_confirm: boolean;
  scaffold_applied_on_confirm: boolean;
  has_existing_commits: boolean;
  confirmation_required: boolean;
  execution_path: string;
  execution_branch: string;
  planned_changes: ProjectBootstrapPlannedChange[];
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
