import type { ReactNode } from "react";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

export function CollapsibleSection({
  title,
  count,
  open,
  onToggle,
  children,
}: {
  title: string;
  count?: number;
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
}) {
  return (
    <section className="border-b border-[color:var(--border)] py-3">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-3 text-left"
      >
        <span className="flex items-center gap-2 text-sm font-medium text-[color:var(--text)]">
          <ChevronRight className={cn("h-4 w-4 text-[color:var(--text-muted)] transition", open && "rotate-90")} />
          {title}
          {count && count > 0 ? (
            <span className="text-[color:var(--text-muted)]">({count})</span>
          ) : null}
        </span>
      </button>
      {open ? <div className="mt-3 space-y-2">{children}</div> : null}
    </section>
  );
}

