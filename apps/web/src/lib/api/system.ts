import { fetchJson } from "./httpClient";
import { postJson } from "./httpClient";
import type { Dashboard, Diagnostics, EventRecord, PurgeDatabaseResult, SearchResults } from "./types";

export function getDashboard() {
  return fetchJson<Dashboard>("/dashboard");
}

export function getEvents(params?: { projectId?: string; taskId?: string; limit?: number }) {
  const search = new URLSearchParams();
  if (params?.projectId) {
    search.set("project_id", params.projectId);
  }
  if (params?.taskId) {
    search.set("task_id", params.taskId);
  }
  if (params?.limit) {
    search.set("limit", String(params.limit));
  }
  const suffix = search.size ? `?${search.toString()}` : "";
  return fetchJson<EventRecord[]>(`/events${suffix}`);
}

export function searchContext(query: string, projectId?: string, status?: string) {
  const params = new URLSearchParams({ q: query });
  if (projectId) {
    params.set("project_id", projectId);
  }
  if (status) {
    params.set("status", status);
  }
  return fetchJson<SearchResults>(`/search?${params.toString()}`);
}

export function getDiagnostics() {
  return fetchJson<Diagnostics>("/settings/diagnostics");
}

export function purgeDatabase() {
  return postJson<PurgeDatabaseResult>("/settings/purge-db", {});
}
