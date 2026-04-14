import type { ProjectSummary } from "@acp/sdk";
import { fetchJson, postJson } from "./httpClient";
import type { ProjectOverview } from "./types";

export function getProjects() {
  return fetchJson<ProjectSummary[]>("/projects");
}

export function createProject(payload: { name: string; description?: string }) {
  return postJson<ProjectSummary>("/projects", payload);
}

export function archiveProject(projectId: string) {
  return postJson<ProjectSummary>(`/projects/${projectId}/archive`, {});
}

export function getProject(projectId: string) {
  return fetchJson<ProjectOverview>(`/projects/${projectId}`);
}
