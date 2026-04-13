import type { SessionSummary } from "@acp/sdk";
import { fetchJson, postJson } from "./httpClient";
import type { SessionTail, SessionTimeline } from "./types";

/**
 * Purpose: Call `createSession` API endpoint.
 * Parameters: See function signature payload/query fields.
 * Returns: Promise resolving to the typed API response shape.
 * Raises: Rejects on transport errors or non-2xx API responses.
 * WHY: Preserves workflow/event/idempotent behavior by delegating mutations to canonical backend services.
 */
export function createSession(payload: {
  task_id: string;
  profile: string;
  agent_name?: string;
  repository_id?: string;
  worktree_id?: string;
  command?: string;
}) {
  return postJson<SessionSummary>("/sessions", payload);
}

/**
 * Purpose: Call `createFollowUpSession` API endpoint.
 * Parameters: See function signature payload/query fields.
 * Returns: Promise resolving to the typed API response shape.
 * Raises: Rejects on transport errors or non-2xx API responses.
 * WHY: Preserves workflow/event/idempotent behavior by delegating mutations to canonical backend services.
 */
export function createFollowUpSession(
  sessionId: string,
  payload: {
    profile: string;
    agent_name?: string;
    follow_up_type?: "retry" | "review" | "verify" | "handoff";
    reuse_worktree?: boolean;
    reuse_repository?: boolean;
    command?: string;
  },
) {
  return postJson<SessionSummary>(`/sessions/${sessionId}/follow-up`, payload);
}

/**
 * Purpose: Call `getSessionTail` API endpoint.
 * Parameters: See function signature payload/query fields.
 * Returns: Promise resolving to the typed API response shape.
 * Raises: Rejects on transport errors or non-2xx API responses.
 */
export function getSessionTail(sessionId: string) {
  return fetchJson<SessionTail>(`/sessions/${sessionId}/tail`);
}

/**
 * Purpose: Call `getSessionTimeline` API endpoint.
 * Parameters: See function signature payload/query fields.
 * Returns: Promise resolving to the typed API response shape.
 * Raises: Rejects on transport errors or non-2xx API responses.
 * WHY: Preserves workflow/event/idempotent behavior by delegating mutations to canonical backend services.
 */
export function getSessionTimeline(sessionId: string) {
  return fetchJson<SessionTimeline>(`/sessions/${sessionId}/timeline`);
}

/**
 * Purpose: Call `cancelSession` API endpoint.
 * Parameters: See function signature payload/query fields.
 * Returns: Promise resolving to the typed API response shape.
 * Raises: Rejects on transport errors or non-2xx API responses.
 */
export function cancelSession(sessionId: string) {
  return postJson<SessionSummary>(`/sessions/${sessionId}/cancel`, {});
}
