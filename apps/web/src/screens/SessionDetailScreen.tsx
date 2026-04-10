import type { ReactNode } from "react";
import { Pill } from "@/components/ui";

type SessionDetailPanel = {
  id: string;
  label: string;
  content: ReactNode;
};

type SessionDetailScreenProps = {
  profile: string;
  status: string;
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
    <section className="rounded-3xl border border-white/7 bg-black/10 px-5 py-5">
      <header className="rounded-2xl border border-white/8 bg-white/4 p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
              Session detail
            </div>
            <h2 className="mt-1 text-xl font-semibold text-slate-100">
              {profile}
            </h2>
            {summary ? (
              <div className="mt-2 text-sm text-slate-400">{summary}</div>
            ) : null}
          </div>
          <Pill className="border-white/8 text-slate-300">{status}</Pill>
        </div>
        {actions ? (
          <div className="mt-3 flex flex-wrap gap-2">{actions}</div>
        ) : null}
      </header>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1.3fr,1fr]">
        <section className="rounded-2xl border border-white/8 bg-black/15 p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
            Output + runtime logs
          </div>
          <div className="mt-3">{outputPanel}</div>
        </section>

        <div className="space-y-4">
          {structuredPanels.map((panel) => (
            <section
              key={panel.id}
              className="rounded-2xl border border-white/8 bg-white/4 p-4"
            >
              <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
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
