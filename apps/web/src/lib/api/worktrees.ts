import type { WorktreeSummary } from "@acp/sdk";
import { patchJson, postJson } from "./httpClient";

export function createWorktree(payload: { repository_id: string; task_id?: string; label?: string }) {
  return postJson<WorktreeSummary>("/worktrees", payload);
}

export function patchWorktree(worktreeId: string, payload: { status: string; lock_reason?: string }) {
  return patchJson<WorktreeSummary>(`/worktrees/${worktreeId}`, payload);
}
