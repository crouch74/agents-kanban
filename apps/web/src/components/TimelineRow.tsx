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
  return eventType.replaceAll(".", " ").replaceAll("_", " ");
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
    <div className="rounded-2xl border border-white/7 bg-white/3 px-4 py-3.5">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 rounded-full border border-white/10 bg-black/15 p-1.5 text-slate-300">
          <Icon className="h-4 w-4" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <div className="text-sm font-medium text-slate-100">
              {friendlyEvent(event.event_type)}
            </div>
            <Pill className="border-white/8 bg-black/10 text-slate-300">
              {event.entity_type}
            </Pill>
            <Pill className="border-white/8 bg-black/10 text-slate-400">
              {event.entity_id.slice(0, 8)}
            </Pill>
          </div>
          <div className="mt-1 text-xs text-slate-500">
            {event.actor_name || "system"} · {new Date(event.created_at).toLocaleString()}
          </div>
          <div className="mt-2 text-sm text-slate-300">{eventSummary(event)}</div>
        </div>
      </div>
    </div>
  );
}
