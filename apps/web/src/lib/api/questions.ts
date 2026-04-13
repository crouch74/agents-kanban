import type { Urgency, WaitingQuestionSummary } from "@acp/sdk";
import { fetchJson, postJson } from "./httpClient";
import type { WaitingQuestionDetail } from "./types";

export function getQuestions(params?: { projectId?: string; status?: string }) {
  const search = new URLSearchParams();
  if (params?.projectId) {
    search.set("project_id", params.projectId);
  }
  if (params?.status) {
    search.set("status", params.status);
  }
  const suffix = search.size ? `?${search.toString()}` : "";
  return fetchJson<WaitingQuestionSummary[]>(`/questions${suffix}`);
}

/**
 * Purpose: Call `createQuestion` API endpoint.
 * Parameters: See function signature payload/query fields.
 * Returns: Promise resolving to the typed API response shape.
 * Raises: Rejects on transport errors or non-2xx API responses.
 */
export function createQuestion(payload: {
  task_id: string;
  session_id?: string;
  prompt: string;
  blocked_reason?: string;
  urgency?: Urgency;
  options_json?: Array<Record<string, unknown>>;
}) {
  return postJson<WaitingQuestionSummary>("/questions", payload);
}

/**
 * Purpose: Call `getQuestion` API endpoint.
 * Parameters: See function signature payload/query fields.
 * Returns: Promise resolving to the typed API response shape.
 * Raises: Rejects on transport errors or non-2xx API responses.
 */
export function getQuestion(questionId: string) {
  return fetchJson<WaitingQuestionDetail>(`/questions/${questionId}`);
}

/**
 * Purpose: Call `answerQuestion` API endpoint.
 * Parameters: See function signature payload/query fields.
 * Returns: Promise resolving to the typed API response shape.
 * Raises: Rejects on transport errors or non-2xx API responses.
 * WHY: Preserves workflow/event/idempotent behavior by delegating mutations to canonical backend services.
 */
export function answerQuestion(
  questionId: string,
  payload: { responder_name: string; body: string; payload_json?: Record<string, unknown> },
) {
  return postJson<WaitingQuestionDetail>(`/questions/${questionId}/replies`, payload);
}
