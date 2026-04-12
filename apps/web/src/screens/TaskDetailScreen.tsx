import type { ReactNode } from "react";

type TaskDetailScreenProps = {
  title: ReactNode;
  actions?: ReactNode;
  contextPanel?: ReactNode;
  sections: Array<{ id: string; label: string; content: ReactNode }>;
};

export function TaskDetailScreen({
  title,
  actions,
  contextPanel,
  sections,
}: TaskDetailScreenProps) {
  return (
    <section className="flex h-full flex-col bg-[color:var(--surface)]">
      <header className="border-b border-[color:var(--border)] px-4 py-3">
        <div className="text-base font-semibold text-[color:var(--text)]">{title}</div>
        {actions ? <div className="mt-3">{actions}</div> : null}
      </header>

      <div className="flex-1 overflow-auto px-4 py-3">
        {contextPanel ? <div>{contextPanel}</div> : null}
        <div className="mt-4 space-y-1">
          {sections.map((section) => (
            <div key={section.id}>{section.content}</div>
          ))}
        </div>
      </div>
    </section>
  );
}
