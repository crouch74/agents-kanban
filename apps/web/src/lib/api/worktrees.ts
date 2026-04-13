import type { WorktreeStatus, WorktreeSummary } from "@acp/sdk";
import { patchJson, postJson } from "./httpClient";

/**
 * Purpose: Call `createWorktree` API endpoint.
 * Parameters: See function signature payload/query fields.
 * Returns: Promise resolving to the typed API response shape.
 * Raises: Rejects on transport errors or non-2xx API responses.
 */
export function createWorktree(payload: { repository_id: string; task_id?: string; label?: string }) {
  return postJson<WorktreeSummary>("/worktrees", payload);
}

/**
 * Purpose: Call `patchWorktree` API endpoint.
 * Parameters: See function signature payload/query fields.
 * Returns: Promise resolving to the typed API response shape.
 * Raises: Rejects on transport errors or non-2xx API responses.
 * WHY: Preserves workflow/event/idempotent behavior by delegating mutations to canonical backend services.
 */
export function patchWorktree(worktreeId: string, payload: { status: WorktreeStatus; lock_reason?: string }) {
  return patchJson<WorktreeSummary>(`/worktrees/${worktreeId}`, payload);
}
