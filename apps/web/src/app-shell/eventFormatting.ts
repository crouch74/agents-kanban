import type { SearchHit, EventRecord } from "@/lib/api";
import { toDisplay } from "@/utils/display";

export function formatEvent(eventType: string) {
  return toDisplay(eventType.replaceAll(".", "_"));
}

export function summarizeEvent(event: EventRecord) {
  const payload = event.payload_json;
  const summaryFields = [
    payload.title,
    payload.name,
    payload.prompt,
    payload.summary,
    payload.local_path,
    payload.branch_name,
    payload.status,
  ];
  const summary = summaryFields.find(
    (value): value is string => typeof value === "string" && value.trim().length > 0,
  );
  if (summary) {
    return summary;
  }

  const addedColumnKeys = payload.added_column_keys;
  if (Array.isArray(addedColumnKeys) && addedColumnKeys.length > 0) {
    return `Added columns: ${addedColumnKeys.join(", ")}`;
  }

  return `${event.actor_name || "system"} updated ${event.entity_type}.`;
}

export function formatSearchSnippet(hit: SearchHit) {
  if (hit.entity_type === "event") {
    return `Audit event matched the query. ${formatEvent(hit.title)} · ${hit.secondary ?? "system"}`;
  }
  return hit.snippet;
}
