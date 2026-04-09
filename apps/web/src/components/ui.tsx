import type { PropsWithChildren, HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Pill({
  children,
  className,
}: PropsWithChildren<{ className?: string }>) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium tracking-wide",
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
    <section className={cn("surface rounded-3xl", className)}>
      {children}
    </section>
  );
}

export function SectionTitle({
  children,
  className,
}: PropsWithChildren<{ className?: string }>) {
  return (
    <h2 className={cn("text-sm font-semibold uppercase tracking-[0.24em] text-slate-400", className)}>
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
    <div className={cn("rounded-2xl border border-white/8 bg-white/3 p-4", className)}>
      <div className="text-[11px] uppercase tracking-[0.22em] text-slate-500">{label}</div>
      <div className="mt-3 text-3xl font-semibold text-slate-50">{value}</div>
    </div>
  );
}

export function ColumnShell({
  children,
  className,
}: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return (
    <div className={cn("min-w-[250px] rounded-3xl border border-white/7 bg-black/12 p-4", className)}>
      {children}
    </div>
  );
}

