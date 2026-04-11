import type { RepositorySummary } from "@acp/sdk";
import { postJson } from "./httpClient";

export function createRepository(payload: { project_id: string; local_path: string; name?: string }) {
  return postJson<RepositorySummary>("/repositories", payload);
}
