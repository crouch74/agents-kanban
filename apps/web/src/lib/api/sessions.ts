import type { SessionSummary } from "@acp/sdk";
import { fetchJson, postJson } from "./httpClient";
import type { SessionTail, SessionTimeline } from "./types";

export function createSession(payload: {
  task_id: string;
  profile: string;
  repository_id?: string;
  worktree_id?: string;
  command?: string;
}) {
  return postJson<SessionSummary>("/sessions", payload);
}

export function createFollowUpSession(
  sessionId: string,
  payload: {
    profile: string;
    follow_up_type?: "retry" | "review" | "verify" | "handoff";
    reuse_worktree?: boolean;
    reuse_repository?: boolean;
    command?: string;
  },
) {
  return postJson<SessionSummary>(`/sessions/${sessionId}/follow-up`, payload);
}

export function getSessionTail(sessionId: string) {
  return fetchJson<SessionTail>(`/sessions/${sessionId}/tail`);
}

export function getSessionTimeline(sessionId: string) {
  return fetchJson<SessionTimeline>(`/sessions/${sessionId}/timeline`);
}

export function cancelSession(sessionId: string) {
  return postJson<SessionSummary>(`/sessions/${sessionId}/cancel`, {});
}
