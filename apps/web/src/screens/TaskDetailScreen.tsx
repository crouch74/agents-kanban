import type { ReactNode } from "react";
import { Pill } from "@/components/ui";

type TaskDetailSection = {
  id: string;
  label: string;
  content: ReactNode;
};

type TaskDetailScreenProps = {
  title: ReactNode;
  state: string;
  priority?: string | null;
  description?: ReactNode;
  actions?: ReactNode;
  contextPanel?: ReactNode;
  sections: TaskDetailSection[];
  quickInspect?: boolean;
};

export function TaskDetailScreen({
  title,
  state,
  priority,
  description,
  actions,
  contextPanel,
  sections,
  quickInspect = false,
}: TaskDetailScreenProps) {
  return (
    <section
      className={[
        "rounded-3xl border border-white/7 bg-black/10",
        quickInspect ? "max-h-[calc(100vh-12rem)] overflow-hidden" : "",
      ].join(" ")}
    >
      <header className="sticky top-0 z-10 border-b border-white/8 bg-slate-950/95 px-5 py-4 backdrop-blur">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
              {quickInspect ? "Task quick inspect" : "Task detail"}
            </div>
            <h2 className="mt-1 text-xl font-semibold text-slate-100">
              {title}
            </h2>
            {description ? (
              <div className="mt-2 text-sm text-slate-400">{description}</div>
            ) : null}
          </div>
          <div className="flex items-center gap-2">
            <Pill className="border-white/8 text-slate-300">{state}</Pill>
            {priority ? (
              <Pill className="border-white/8 text-slate-300">{priority}</Pill>
            ) : null}
          </div>
        </div>
        {actions ? (
          <div className="mt-3 flex flex-wrap gap-2">{actions}</div>
        ) : null}
      </header>

      <div className="space-y-4 overflow-auto px-5 py-4">
        {contextPanel ? (
          <div className="rounded-2xl border border-white/8 bg-white/4 p-4">
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
              Primary context
            </div>
            <div className="mt-3">{contextPanel}</div>
          </div>
        ) : null}

        <div className="grid gap-4 lg:grid-cols-2">
          {sections.map((section) => (
            <section
              key={section.id}
              className="rounded-2xl border border-white/8 bg-white/4 p-4"
            >
              <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
                {section.label}
              </div>
              <div className="mt-3">{section.content}</div>
            </section>
          ))}
        </div>
      </div>
    </section>
  );
}
