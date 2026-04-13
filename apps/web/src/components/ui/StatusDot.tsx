import { cn } from "@/lib/utils";
import { type WorkflowState, type SessionStatus, type WorktreeStatus } from "@acp/sdk";

type StatusKey = WorkflowState | SessionStatus | WorktreeStatus | string;

const statusClassByKey: Record<StatusKey, string> = {
  backlog: "bg-[color:var(--status-backlog)]",
  ready: "bg-[color:var(--status-ready)]",
  in_progress: "bg-[color:var(--status-progress)]",
  review: "bg-[color:var(--status-review)]",
  done: "bg-[color:var(--status-done)]",
  cancelled: "bg-[color:var(--text-faint)]",
};

export function StatusDot({
  status,
  className,
}: {
  status: StatusKey;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-block h-2.5 w-2.5 rounded-full",
        statusClassByKey[status] ?? "bg-[color:var(--text-faint)]",
        className,
      )}
    />
  );
}
