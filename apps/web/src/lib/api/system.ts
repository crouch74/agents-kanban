import { fetchJson } from "./httpClient";
import type { Dashboard, Diagnostics, EventRecord, SearchResults } from "./types";

export function getDashboard() {
  return fetchJson<Dashboard>("/dashboard");
}

export function getEvents(params?: { projectId?: string; taskId?: string; sessionId?: string; limit?: number }) {
  const search = new URLSearchParams();
  if (params?.projectId) {
    search.set("project_id", params.projectId);
  }
  if (params?.taskId) {
    search.set("task_id", params.taskId);
  }
  if (params?.sessionId) {
    search.set("session_id", params.sessionId);
  }
  if (params?.limit) {
    search.set("limit", String(params.limit));
  }
  const suffix = search.size ? `?${search.toString()}` : "";
  return fetchJson<EventRecord[]>(`/events${suffix}`);
}

export function getDiagnostics() {
  return fetchJson<Diagnostics>("/diagnostics");
}

export function searchContext(query: string, projectId?: string) {
  const params = new URLSearchParams({ q: query });
  if (projectId) {
    params.set("project_id", projectId);
  }
  return fetchJson<SearchResults>(`/search?${params.toString()}`);
}
