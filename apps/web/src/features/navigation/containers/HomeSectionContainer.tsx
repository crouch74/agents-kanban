import { Activity } from "lucide-react";
import { DashboardScreen } from "@/screens/DashboardScreen";
import { Pill, SectionTitle, StatTile } from "@/components/ui";
import type { EventRecord } from "@/lib/api";
import { toDisplay } from "@/utils/display";

export function HomeSectionContainer({
  environment,
  dashboard,
  events,
  projectName,
  onOpenQuestion,
  onOpenTask,
  onOpenSession,
  formatEvent,
  summarizeEvent,
}: {
  environment: string;
  dashboard: any;
  events: EventRecord[];
  projectName: string;
  onOpenQuestion: (questionId: string, projectId: string) => void;
  onOpenTask: (taskId: string, projectId: string) => void;
  onOpenSession: (sessionId: string, projectId: string) => void;
  formatEvent: (eventType: string) => string;
  summarizeEvent: (event: EventRecord) => string;
}) {
  return (
    <DashboardScreen>
      <section className="rounded-[8px] border border-[color:var(--border)] bg-[color:var(--surface)] px-6 py-6">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <div>
            <p className="text-sm text-[color:var(--text-muted)]">Operational overview</p>
            <h2 className="mt-2 text-[20px] font-semibold tracking-tight text-[color:var(--text)]">Observe, steer, resume.</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-[color:var(--text-muted)]">
              The control plane keeps project state, board flow, runtime context, and future agent sessions in one local-first workspace.
            </p>
          </div>
          <div className="flex items-center gap-3 text-sm text-[color:var(--text-muted)]">
            <Activity className="h-4 w-4 text-[color:var(--accent)]" />
            {environment} environment
          </div>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-4">
          <StatTile label="Projects" value={dashboard?.projects.length ?? 0} />
          <StatTile label="Waiting" value={dashboard?.waiting_count ?? 0} />
          <StatTile label="Blocked" value={dashboard?.blocked_count ?? 0} />
          <StatTile label="Running Sessions" value={dashboard?.running_sessions ?? 0} />
        </div>

        <div className="mt-8 grid gap-4 xl:grid-cols-3">
          <div className="rounded-[8px] border border-[color:var(--border)] bg-[color:var(--surface)] p-5">
            <SectionTitle>Waiting Across Projects</SectionTitle>
            <div className="mt-4 flex flex-col gap-3">
              {dashboard?.waiting_questions.map((question: any) => (
                <button key={question.id} onClick={() => onOpenQuestion(question.id, question.project_id)} className="rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface-2)] px-4 py-3 text-left hover:bg-zinc-50">
                  <div className="text-sm font-semibold text-[color:var(--text)]">{question.prompt}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-[8px] border border-[color:var(--border)] bg-[color:var(--surface)] p-5">
            <SectionTitle>Blocked Tasks</SectionTitle>
            <div className="mt-4 flex flex-col gap-3">
              {dashboard?.blocked_tasks.map((task: any) => (
                <button key={task.id} onClick={() => onOpenTask(task.id, task.project_id)} className="rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface-2)] px-4 py-3 text-left hover:bg-zinc-50">
                  <div className="text-sm font-semibold text-[color:var(--text)]">{task.title}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-[8px] border border-[color:var(--border)] bg-[color:var(--surface)] p-5">
            <SectionTitle>Running Sessions</SectionTitle>
            <div className="mt-4 flex flex-col gap-3">
              {dashboard?.active_sessions.map((session: any) => (
                <button key={session.id} onClick={() => onOpenSession(session.id, session.project_id)} className="rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface-2)] px-4 py-3 text-left hover:bg-zinc-50">
                  <div className="text-sm font-semibold text-[color:var(--text)]">{toDisplay(session.profile)}</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-8 rounded-[8px] border border-[color:var(--border)] bg-[color:var(--surface)] p-5">
          <div className="flex items-center justify-between gap-4">
            <SectionTitle>Activity Feed</SectionTitle>
            <Pill>{events.length} visible</Pill>
          </div>
          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            {events.map((event) => (
              <div key={event.id} className="rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface-2)] px-4 py-4">
                <div className="text-sm font-semibold text-[color:var(--text)]">{formatEvent(event.event_type)}</div>
                <div className="mt-2 text-sm text-[color:var(--text-muted)]">{summarizeEvent(event)}</div>
              </div>
            ))}
            {!events.length ? <div className="text-sm text-[color:var(--text-muted)]">No events recorded yet for {projectName}.</div> : null}
          </div>
        </div>
      </section>
    </DashboardScreen>
  );
}
