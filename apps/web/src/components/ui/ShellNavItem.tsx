import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export function ShellNavItem({
  active,
  icon: Icon,
  label,
  compact = false,
  onClick,
}: {
  active: boolean;
  icon: LucideIcon;
  label: string;
  compact?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex h-8 items-center gap-2 rounded px-3 text-sm",
        active
          ? "bg-[rgba(37,99,235,0.08)] text-[color:var(--accent)]"
          : "text-[color:var(--text-muted)] hover:bg-black/4 hover:text-[color:var(--text)]",
        compact ? "justify-center px-0" : "w-full",
      )}
    >
      <Icon className="h-4 w-4 shrink-0" />
      {compact ? null : <span>{label}</span>}
    </button>
  );
}

