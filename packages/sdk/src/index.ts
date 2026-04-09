export type WorkflowState =
  | "backlog"
  | "ready"
  | "in_progress"
  | "review"
  | "done"
  | "cancelled";

export interface BoardColumn {
  id: string;
  name: string;
  key: WorkflowState;
  position: number;
  wip_limit?: number | null;
}

export interface TaskSummary {
  id: string;
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
