import type { ReactNode } from "react";
import { useDraggable, useDroppable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import type { TaskSummary } from "@acp/sdk";
import { AvatarStack, StatusDot } from "@/components/ui";
import { toDisplay } from "@/utils/display";

type ProjectBoardScreenProps = {
  children: ReactNode;
};

export function ProjectBoardScreen({ children }: ProjectBoardScreenProps) {
  return <>{children}</>;
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
      className={isOver ? "rounded-[8px] ring-2 ring-[color:var(--accent)]/30" : undefined}
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
  assignees?: string[];
};

export function DraggableTaskCard({
  task,
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

  const priorityTone = priorityToneByValue(task.priority ?? "");

  return (
    <button
      ref={setNodeRef}
      type="button"
      onClick={onInspect}
      style={{
        transform: transform ? CSS.Translate.toString(transform) : undefined,
        opacity: isDragging ? 0.7 : 1,
      }}
      className={[
        "card-surface w-full p-3 text-left transition",
        selected ? "border-[color:var(--accent)]" : "hover:border-zinc-300",
        task.parent_task_id ? "cursor-default" : "cursor-grab active:cursor-grabbing",
      ].join(" ")}
      {...listeners}
      {...attributes}
    >
      {task.priority ? (
        <div
          className="inline-flex rounded-[4px] px-1.5 py-0.5 text-[11px] font-medium"
          style={priorityTone}
        >
          {toDisplay(task.priority)}
        </div>
      ) : null}
      <div className="mt-1.5 text-sm font-medium text-[color:var(--text)]">
        {task.title}
      </div>
      <div className="mt-3 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-[11px] text-[color:var(--text-muted)]">
          {metadata.sessions > 0 ? <span>🔁 {metadata.sessions}</span> : null}
        </div>
        <AvatarStack names={metadata.assignees ?? []} />
      </div>
    </button>
  );
}

export function BoardColumnHeader({
  title,
  status,
  count,
  wipLimit,
}: {
  title: string;
  status: string;
  count: number;
  wipLimit?: number | null;
}) {
  return (
    <div className="flex items-center gap-2 text-[13px] text-[color:var(--text-muted)]">
      <StatusDot status={status} className="h-3 w-3" />
      <span className="font-medium text-[color:var(--text)]">{toDisplay(title)}</span>
      <span>
        · {count}
        {wipLimit ? ` / ${wipLimit}` : ""}
      </span>
    </div>
  );
}

function priorityToneByValue(priority: string) {
  switch (priority.toLowerCase()) {
    case "urgent":
      return { background: "rgba(239,68,68,0.1)", color: "#b91c1c" };
    case "high":
      return { background: "rgba(245,158,11,0.1)", color: "#b45309" };
    case "medium":
      return { background: "rgba(59,130,246,0.1)", color: "#1d4ed8" };
    default:
      return { background: "rgba(161,161,170,0.16)", color: "#52525b" };
  }
}
