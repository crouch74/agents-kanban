import type { ProjectBootstrapResult, ProjectSummary, StackPreset } from "@acp/sdk";
import { fetchJson, postJson } from "./httpClient";
import type { ProjectOverview } from "./types";

export function getProjects() {
  return fetchJson<ProjectSummary[]>("/projects");
}

export function createProject(payload: { name: string; description?: string }) {
  return postJson<ProjectSummary>("/projects", payload);
}

export function bootstrapProject(payload: {
  name: string;
  description?: string;
  repo_path: string;
  initialize_repo?: boolean;
  stack_preset: StackPreset;
  stack_notes?: string;
  initial_prompt: string;
  use_worktree?: boolean;
}) {
  return postJson<ProjectBootstrapResult>("/projects/bootstrap", payload);
}

export function getProject(projectId: string) {
  return fetchJson<ProjectOverview>(`/projects/${projectId}`);
}
