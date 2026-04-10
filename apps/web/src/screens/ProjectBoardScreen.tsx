import type { ReactNode } from "react";
import { useDraggable, useDroppable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { Bot, FolderGit2, GitBranch, ShieldCheck } from "lucide-react";
import type { TaskSummary } from "@acp/sdk";
import { Pill } from "@/components/ui";

type ProjectBoardScreenProps = {
  children: ReactNode;
};

export function ProjectBoardScreen({ children }: ProjectBoardScreenProps) {
  return children;
}

export function DroppableBoardColumn({
  columnId,
  children,
}: {
  columnId: string;
  children: ReactNode;
}) {
  const { isOver, setNodeRef } = useDroppable({ id: columnId });

  return (
    <div
      ref={setNodeRef}
      className={[
        "rounded-[30px] transition",
        isOver
          ? "bg-[color:var(--color-accent-soft)]/70 p-1 ring-2 ring-[color:var(--color-accent-primary)]/75 shadow-lg shadow-[color:var(--color-accent-soft)]"
          : "p-0",
      ].join(" ")}
    >
      {children}
    </div>
  );
}

type TaskCardMeta = {
  sessions: number;
  worktree: boolean;
  checks: number;
  artifacts: number;
};

export function DraggableTaskCard({
  task,
  subtasks,
  selected,
  metadata,
  onInspect,
}: {
  task: TaskSummary;
  subtasks: TaskSummary[];
  selected: boolean;
  metadata: TaskCardMeta;
  onInspect: () => void;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: task.id,
    disabled: Boolean(task.parent_task_id),
  });

  return (
    <TaskCard
      task={task}
      selected={selected}
      subtasks={subtasks}
      metadata={metadata}
      setNodeRef={setNodeRef}
      onInspect={onInspect}
      isDragging={isDragging}
      dragTransform={transform ? CSS.Translate.toString(transform) : undefined}
      dragHandleProps={{ ...listeners, ...attributes }}
    />
  );
}

type TaskCardProps = {
  task: TaskSummary;
  selected: boolean;
  subtasks: TaskSummary[];
  metadata: TaskCardMeta;
  setNodeRef: (node: HTMLElement | null) => void;
  onInspect: () => void;
  isDragging: boolean;
  dragTransform?: string;
  dragHandleProps: Record<string, unknown>;
};

function TaskCard({
  task,
  selected,
  subtasks,
  metadata,
  setNodeRef,
  onInspect,
  isDragging,
  dragTransform,
  dragHandleProps,
}: TaskCardProps) {
  const stateTone = task.blocked_reason
    ? "border-rose-300/25 bg-rose-300/10 text-rose-100"
    : task.waiting_for_human
      ? "border-amber-300/25 bg-amber-300/10 text-amber-100"
      : "border-white/8 text-slate-300";
  const visibleSubtasks = subtasks.slice(0, 2);
  const hiddenSubtaskCount = Math.max(0, subtasks.length - visibleSubtasks.length);

  return (
    <button
      ref={setNodeRef}
      type="button"
      onClick={onInspect}
      style={{
        transform: dragTransform,
        opacity: isDragging ? 0.62 : 1,
      }}
      className={[
        "group w-full rounded-3xl border bg-white/4 px-5 py-4 text-left shadow-sm transition",
        selected
          ? "border-[color:var(--color-accent-primary)] bg-[color:var(--color-accent-soft)]/25"
          : "border-white/8 hover:border-white/20 hover:bg-white/7",
        task.parent_task_id ? "cursor-default" : "cursor-grab active:cursor-grabbing",
      ].join(" ")}
      {...dragHandleProps}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="text-sm font-semibold text-slate-100">{task.title}</div>
        <div className="flex items-center gap-2">
          {(task.waiting_for_human || task.blocked_reason) ? (
            <Pill className={stateTone}>{task.waiting_for_human ? "Waiting" : "Blocked"}</Pill>
          ) : null}
          <Pill className="border-white/8 text-slate-300">{task.priority}</Pill>
        </div>
      </div>

      <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
        <MetaBadge icon={Bot} label={`${metadata.sessions} sessions`} />
        <MetaBadge icon={GitBranch} label={metadata.worktree ? "worktree linked" : "no worktree"} />
        <div className="hidden items-center gap-2 opacity-0 transition group-hover:flex group-hover:opacity-100 group-focus-within:flex group-focus-within:opacity-100">
          <MetaBadge icon={ShieldCheck} label={`${metadata.checks} checks`} />
          <MetaBadge icon={FolderGit2} label={`${metadata.artifacts} artifacts`} />
        </div>
      </div>

      {visibleSubtasks.length ? (
        <div className="mt-4 rounded-2xl border border-white/10 bg-black/15 px-3 py-3">
          <div className="text-[11px] uppercase tracking-[0.18em] text-slate-500">Subtasks</div>
          <div className="mt-2 flex flex-col gap-1.5">
            {visibleSubtasks.map((subtask) => (
              <div key={subtask.id} className="truncate rounded-xl border border-white/8 bg-white/3 px-3 py-2 text-sm text-slate-200">
                {subtask.title}
              </div>
            ))}
            {hiddenSubtaskCount > 0 ? (
              <div className="text-xs text-slate-500">+{hiddenSubtaskCount} more…</div>
            ) : null}
          </div>
        </div>
      ) : null}
    </button>
  );
}

function MetaBadge({
  icon: Icon,
  label,
}: {
  icon: typeof Bot;
  label: string;
}) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-black/20 px-2.5 py-1 text-[11px] leading-none">
      <Icon className="h-3 w-3" />
      <span>{label}</span>
    </span>
  );
}
