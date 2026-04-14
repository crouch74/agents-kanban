import type { TaskPriority, WorkflowState } from "@acp/sdk";
import { fetchJson, patchJson, postJson } from "./httpClient";
import type { TaskComment, TaskDetail, TaskSummary } from "./types";

export function getTasks(params?: { projectId?: string; status?: string; q?: string }) {
  const search = new URLSearchParams();
  if (params?.projectId) {
    search.set("project_id", params.projectId);
  }
  if (params?.status) {
    search.set("status", params.status);
  }
  if (params?.q) {
    search.set("q", params.q);
  }
  const suffix = search.size ? `?${search.toString()}` : "";
  return fetchJson<TaskSummary[]>(`/tasks${suffix}`);
}

export function createTask(payload: {
  project_id: string;
  title: string;
  description?: string;
  priority?: TaskPriority;
  board_column_key?: WorkflowState;
  tags?: string[];
  assignee?: string;
  source?: string;
}) {
  return postJson<TaskSummary>("/tasks", payload);
}

export function patchTask(
  taskId: string,
  payload: {
    title?: string;
    description?: string;
    workflow_state?: WorkflowState;
    board_column_id?: string;
    priority?: TaskPriority;
    tags?: string[];
    assignee?: string | null;
  },
) {
  return patchJson<TaskSummary>(`/tasks/${taskId}`, payload);
}

export function getTaskDetail(taskId: string) {
  return fetchJson<TaskDetail>(`/tasks/${taskId}/detail`);
}

export function getTaskComments(taskId: string) {
  return fetchJson<TaskComment[]>(`/tasks/${taskId}/comments`);
}

export function addTaskComment(
  taskId: string,
  payload: { author_type?: string; author_name: string; source?: string; body: string; metadata_json?: Record<string, unknown> },
) {
  return postJson<TaskComment>(`/tasks/${taskId}/comments`, payload);
}
