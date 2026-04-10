import { useMemo, useState } from "react";
import type { EventRecord } from "@/lib/api";
import { SectionFrame, SectionTitle } from "@/components/ui";
import { TimelineRow } from "@/components/TimelineRow";

type Option = { value: string; label: string };

type ActivityScreenProps = {
  active: boolean;
  events: EventRecord[];
  loading?: boolean;
  error?: string | null;
  projectOptions: Option[];
  taskOptions: Option[];
  sessionOptions: Option[];
};

function eventWithLinks(event: EventRecord) {
  const payload = event.payload_json;
  const projectId = typeof payload.project_id === "string" ? payload.project_id : undefined;
  const taskId =
    typeof payload.task_id === "string"
      ? payload.task_id
      : event.entity_type === "task"
        ? event.entity_id
        : undefined;
  const sessionId =
    typeof payload.session_id === "string"
      ? payload.session_id
      : event.entity_type === "session"
        ? event.entity_id
        : undefined;
  return { event, projectId, taskId, sessionId };
}

export function ActivityScreen({
  active,
  events,
  loading,
  error,
  projectOptions,
  taskOptions,
  sessionOptions,
}: ActivityScreenProps) {
  const [projectFilter, setProjectFilter] = useState("all");
  const [taskFilter, setTaskFilter] = useState("all");
  const [sessionFilter, setSessionFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");

  const typeOptions = useMemo(
    () => ["all", ...new Set(events.map((event) => event.event_type))],
    [events],
  );

  const filtered = useMemo(() => {
    return events
      .map(eventWithLinks)
      .filter((row) => {
        const projectPass = projectFilter === "all" || row.projectId === projectFilter;
        const taskPass = taskFilter === "all" || row.taskId === taskFilter;
        const sessionPass = sessionFilter === "all" || row.sessionId === sessionFilter;
        const typePass = typeFilter === "all" || row.event.event_type === typeFilter;
        return projectPass && taskPass && sessionPass && typePass;
      })
      .map((row) => row.event);
  }, [events, projectFilter, sessionFilter, taskFilter, typeFilter]);

  if (!active) {
    return null;
  }

  return (
    <SectionFrame className="px-5 py-5">
      <SectionTitle>Activity timeline</SectionTitle>
      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <select value={projectFilter} onChange={(event) => setProjectFilter(event.target.value)} className="rounded-2xl border border-white/8 bg-black/15 px-3 py-2 text-sm outline-none">
          <option value="all">All projects</option>
          {projectOptions.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select value={taskFilter} onChange={(event) => setTaskFilter(event.target.value)} className="rounded-2xl border border-white/8 bg-black/15 px-3 py-2 text-sm outline-none">
          <option value="all">All tasks</option>
          {taskOptions.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select value={sessionFilter} onChange={(event) => setSessionFilter(event.target.value)} className="rounded-2xl border border-white/8 bg-black/15 px-3 py-2 text-sm outline-none">
          <option value="all">All sessions</option>
          {sessionOptions.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)} className="rounded-2xl border border-white/8 bg-black/15 px-3 py-2 text-sm outline-none">
          {typeOptions.map((option) => (
            <option key={option} value={option}>{option === "all" ? "All event types" : option}</option>
          ))}
        </select>
      </div>

      <div className="mt-4 flex flex-col gap-3">
        {loading ? <div className="rounded-2xl border border-white/7 bg-white/3 px-4 py-4 text-sm text-slate-500">Loading timeline events…</div> : null}
        {error ? <div className="rounded-2xl border border-rose-300/30 bg-rose-300/10 px-4 py-4 text-sm text-rose-100">{error}</div> : null}
        {!loading && !error && filtered.map((event) => <TimelineRow key={event.id} event={event} />)}
        {!loading && !error && !filtered.length ? (
          <div className="rounded-2xl border border-white/7 bg-white/3 px-4 py-4 text-sm text-slate-500">
            No timeline activity matches the current filters.
          </div>
        ) : null}
      </div>
    </SectionFrame>
  );
}
