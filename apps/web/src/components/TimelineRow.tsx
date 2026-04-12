import {
  AlertCircle,
  CheckCircle2,
  CircleDot,
  GitBranch,
  MessageCircleMore,
  PlayCircle,
} from "lucide-react";
import type { EventRecord } from "@/lib/api";
import { Pill } from "@/components/ui";
import { toDisplay } from "@/utils/display";

function iconForEvent(eventType: string) {
  if (eventType.includes("session")) {
    return PlayCircle;
  }
  if (eventType.includes("worktree") || eventType.includes("repository")) {
    return GitBranch;
  }
  if (eventType.includes("question") || eventType.includes("reply")) {
    return MessageCircleMore;
  }
  if (eventType.includes("check") || eventType.includes("complete")) {
    return CheckCircle2;
  }
  if (eventType.includes("error") || eventType.includes("fail")) {
    return AlertCircle;
  }
  return CircleDot;
}

function friendlyEvent(eventType: string) {
  return toDisplay(eventType.replaceAll(".", "_"));
}

function eventSummary(event: EventRecord) {
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

type TimelineRowProps = {
  event: EventRecord;
};

export function TimelineRow({ event }: TimelineRowProps) {
  const Icon = iconForEvent(event.event_type);
  return (
    <div className="rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3.5">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 rounded-full border border-[color:var(--border)] bg-[color:var(--surface-2)] p-1.5 text-[color:var(--text-muted)]">
          <Icon className="h-4 w-4" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <div className="text-sm font-medium text-[color:var(--text)]">
              {friendlyEvent(event.event_type)}
            </div>
            <Pill>
              {toDisplay(event.entity_type)}
            </Pill>
            <Pill className="text-[color:var(--text-faint)]">
              {event.entity_id.slice(0, 8)}
            </Pill>
          </div>
          <div className="mt-1 text-xs text-[color:var(--text-muted)]">
            {event.actor_name || "system"} · {new Date(event.created_at).toLocaleString()}
          </div>
          <div className="mt-2 text-sm text-[color:var(--text)]">{eventSummary(event)}</div>
        </div>
      </div>
    </div>
  );
}
