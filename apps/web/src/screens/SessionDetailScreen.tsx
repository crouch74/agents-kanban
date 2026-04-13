import type { ReactNode } from "react";
import type { AgentProfile, SessionStatus } from "@acp/sdk";
import { Pill } from "@/components/ui";
import { toDisplay } from "@/utils/display";

type SessionDetailPanel = {
  id: string;
  label: string;
  content: ReactNode;
};

type SessionDetailScreenProps = {
  profile: AgentProfile;
  status: SessionStatus;
  summary?: ReactNode;
  actions?: ReactNode;
  outputPanel: ReactNode;
  structuredPanels: SessionDetailPanel[];
};

export function SessionDetailScreen({
  profile,
  status,
  summary,
  actions,
  outputPanel,
  structuredPanels,
}: SessionDetailScreenProps) {
  return (
    <section className="rounded-[8px] border border-[color:var(--border)] bg-[color:var(--surface)] px-5 py-5">
      <header className="rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface-2)] p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-xs text-[color:var(--text-muted)]">
              Session detail
            </div>
            <h2 className="mt-1 text-xl font-semibold text-[color:var(--text)]">
              {toDisplay(profile)}
            </h2>
            {summary ? (
              <div className="mt-2 text-sm text-[color:var(--text-muted)]">{summary}</div>
            ) : null}
          </div>
          <Pill>{toDisplay(status)}</Pill>
        </div>
        {actions ? (
          <div className="mt-3 flex flex-wrap gap-2">{actions}</div>
        ) : null}
      </header>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1.3fr,1fr]">
        <section className="min-w-0 rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
          <div className="text-xs text-[color:var(--text-muted)]">
            Output + runtime logs
          </div>
          <div className="mt-3">{outputPanel}</div>
        </section>

        <div className="min-w-0 space-y-4">
          {structuredPanels.map((panel) => (
            <section
              key={panel.id}
              className="min-w-0 rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)] p-4"
            >
              <div className="text-xs text-[color:var(--text-muted)]">
                {panel.label}
              </div>
              <div className="mt-3">{panel.content}</div>
            </section>
          ))}
        </div>
      </div>
    </section>
  );
}
