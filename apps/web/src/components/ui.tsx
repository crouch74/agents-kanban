import type { PropsWithChildren, HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

export function Pill({
  children,
  className,
}: PropsWithChildren<{ className?: string }>) {
  return (
    <span
      className={cn(
        "inline-flex min-h-[var(--space-row-height)] items-center rounded-full border px-[var(--space-3)] py-[var(--space-1)] text-[length:var(--type-caption-size)] leading-[var(--type-caption-line-height)] font-medium tracking-[0.08em]",
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
        "surface rounded-3xl px-[var(--space-page-gutter)] py-[var(--space-card-padding)] [&>*+*]:mt-[var(--space-section-gap)]",
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
    <h2
      className={cn(
        "text-[length:var(--type-section-title-size)] leading-[var(--type-section-title-line-height)] font-semibold uppercase tracking-[0.2em] text-slate-400",
        className,
      )}
    >
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
        "rounded-2xl border border-white/8 bg-white/3 px-[var(--space-card-padding)] py-[calc(var(--space-card-padding)-var(--space-2))]",
        className,
      )}
    >
      <div className="text-[length:var(--type-metadata-size)] leading-[var(--type-metadata-line-height)] uppercase tracking-[0.16em] text-slate-500">
        {label}
      </div>
      <div className="mt-[var(--space-form-gap)] text-[length:var(--type-display-size)] leading-[var(--type-display-line-height)] font-semibold text-slate-50">
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
        "min-w-[250px] rounded-3xl border border-white/7 bg-black/12 px-[var(--space-card-padding)] py-[var(--space-card-padding)] [&>*+*]:mt-[var(--space-section-gap)]",
        className,
      )}
    >
      {children}
    </div>
  );
}
