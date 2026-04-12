import type { HTMLAttributes, PropsWithChildren } from "react";
import { cn } from "@/lib/utils";

export { AvatarStack } from "@/components/ui/AvatarStack";
export { CollapsibleSection } from "@/components/ui/CollapsibleSection";
export { CommandSearchTrigger } from "@/components/ui/CommandSearchTrigger";
export { DialogFrame } from "@/components/ui/DialogFrame";
export { ShellNavItem } from "@/components/ui/ShellNavItem";
export { StatusDot } from "@/components/ui/StatusDot";

export function Pill({
  children,
  className,
}: PropsWithChildren<{ className?: string }>) {
  return (
    <span
      className={cn(
        "inline-flex min-h-6 items-center rounded border border-[color:var(--border)] px-2 py-0.5 text-[11px] font-medium text-[color:var(--text-muted)]",
        className,
      )}
    >
      {children}
    </span>
  );
}

export function SectionFrame({
  children,
  className,
}: PropsWithChildren<{ className?: string }>) {
  return (
    <section
      className={cn(
        "rounded-[8px] border border-[color:var(--border)] bg-[color:var(--surface)] p-4",
        className,
      )}
    >
      {children}
    </section>
  );
}

export function SectionTitle({
  children,
  className,
}: PropsWithChildren<{ className?: string }>) {
  return (
    <h2 className={cn("text-[20px] font-semibold text-[color:var(--text)]", className)}>
      {children}
    </h2>
  );
}

export function StatTile({
  label,
  value,
  className,
}: {
  label: string;
  value: string | number;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3",
        className,
      )}
    >
      <div className="text-xs text-[color:var(--text-muted)]">{label}</div>
      <div className="mt-1 text-xl font-semibold text-[color:var(--text)]">
        {value}
      </div>
    </div>
  );
}

export function ColumnShell({
  children,
  className,
}: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return (
    <div
      className={cn(
        "min-w-[260px] max-w-[260px] shrink-0 scroll-ml-4 snap-start rounded-[8px] border border-[color:var(--border)] bg-[color:var(--surface-2)] p-3",
        className,
      )}
    >
      {children}
    </div>
  );
}
