import type { TaskSummary } from "@acp/sdk";
import { fetchJson, patchJson, postJson } from "./httpClient";
import type { TaskDetail } from "./types";

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
