import type { ProjectBootstrapResult, ProjectSummary, StackPreset } from "@acp/sdk";
import { fetchJson, postJson } from "./httpClient";
import type { ProjectOverview } from "./types";

/**
 * Purpose: Call `getProjects` API endpoint.
 * Parameters: See function signature payload/query fields.
 * Returns: Promise resolving to the typed API response shape.
 * Raises: Rejects on transport errors or non-2xx API responses.
 */
export function getProjects() {
  return fetchJson<ProjectSummary[]>("/projects");
}

/**
 * Purpose: Call `createProject` API endpoint.
 * Parameters: See function signature payload/query fields.
 * Returns: Promise resolving to the typed API response shape.
 * Raises: Rejects on transport errors or non-2xx API responses.
 */
export function createProject(payload: { name: string; description?: string }) {
  return postJson<ProjectSummary>("/projects", payload);
}

/**
 * Purpose: Call `bootstrapProject` API endpoint.
 * Parameters: See function signature payload/query fields.
 * Returns: Promise resolving to the typed API response shape.
 * Raises: Rejects on transport errors or non-2xx API responses.
 */
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

/**
 * Purpose: Call `getProject` API endpoint.
 * Parameters: See function signature payload/query fields.
 * Returns: Promise resolving to the typed API response shape.
 * Raises: Rejects on transport errors or non-2xx API responses.
 */
export function getProject(projectId: string) {
  return fetchJson<ProjectOverview>(`/projects/${projectId}`);
}
