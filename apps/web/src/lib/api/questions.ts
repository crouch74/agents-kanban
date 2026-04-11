import type { WaitingQuestionSummary } from "@acp/sdk";
import { fetchJson, postJson } from "./httpClient";
import type { WaitingQuestionDetail } from "./types";

export function createQuestion(payload: {
  task_id: string;
  session_id?: string;
  prompt: string;
  blocked_reason?: string;
  urgency?: string;
  options_json?: Array<Record<string, unknown>>;
}) {
  return postJson<WaitingQuestionSummary>("/questions", payload);
}

export function getQuestion(questionId: string) {
  return fetchJson<WaitingQuestionDetail>(`/questions/${questionId}`);
}

export function answerQuestion(
  questionId: string,
  payload: { responder_name: string; body: string; payload_json?: Record<string, unknown> },
) {
  return postJson<WaitingQuestionDetail>(`/questions/${questionId}/replies`, payload);
}
