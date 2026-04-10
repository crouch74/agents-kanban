import type { ComponentPropsWithoutRef, PropsWithChildren, ReactNode } from "react";
import { Search } from "lucide-react";
import { cn } from "@/lib/utils";

type Tone = "default" | "subtle" | "danger";

function surfaceTone(tone: Tone) {
  if (tone === "subtle") return "bg-[color:var(--color-surface-fill-subtle)]";
  if (tone === "danger") return "bg-rose-100/20";
  return "bg-[color:var(--color-surface-panel)]";
}

export function Card({ className, tone = "default", ...props }: ComponentPropsWithoutRef<"div"> & { tone?: Tone }) {
  return (
    <div
      className={cn(
        "rounded-[var(--radius-lg)] border border-[color:var(--color-stroke-default)] shadow-[var(--shadow-sm)]",
        surfaceTone(tone),
        className,
      )}
      {...props}
    />
  );
}

export function Panel({ className, ...props }: ComponentPropsWithoutRef<"section">) {
  return <section className={cn("rounded-[var(--radius-md)] border border-[color:var(--color-stroke-default)] bg-[color:var(--color-surface-panel-elevated)] p-4", className)} {...props} />;
}

const controlBase =
  "w-full rounded-[var(--radius-md)] border border-[color:var(--color-stroke-default)] bg-[color:var(--color-surface-panel)] px-3 py-2 text-sm text-[color:var(--color-text-primary)] outline-none transition duration-[var(--motion-duration-fast)] ease-[var(--motion-ease-standard)] placeholder:text-[color:var(--color-text-muted)] hover:border-[color:var(--color-text-muted)] focus-visible:border-[color:var(--color-accent-primary)] focus-visible:ring-2 focus-visible:ring-[color:var(--color-focus-ring)] disabled:cursor-not-allowed disabled:opacity-60";

export function Input({ className, ...props }: ComponentPropsWithoutRef<"input">) {
  return <input className={cn(controlBase, className)} {...props} />;
}

export function Select({ className, ...props }: ComponentPropsWithoutRef<"select">) {
  return <select className={cn(controlBase, "pr-8", className)} {...props} />;
}

export function Textarea({ className, ...props }: ComponentPropsWithoutRef<"textarea">) {
  return <textarea className={cn(controlBase, "min-h-24 py-2.5", className)} {...props} />;
}

export function SearchInput({ className, inputClassName, ...props }: ComponentPropsWithoutRef<"input"> & { inputClassName?: string }) {
  return (
    <div className={cn("relative", className)}>
      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[color:var(--color-text-muted)]" />
      <Input className={cn("pl-9", inputClassName)} {...props} />
    </div>
  );
}

export function Button({ className, variant = "secondary", ...props }: ComponentPropsWithoutRef<"button"> & { variant?: "primary" | "secondary" | "ghost" | "danger" }) {
  const variantClass =
    variant === "primary"
      ? "border-transparent bg-[color:var(--color-accent-primary)] text-[color:var(--color-text-inverse)] hover:brightness-95"
      : variant === "ghost"
        ? "border-transparent bg-transparent text-[color:var(--color-text-secondary)] hover:bg-[color:var(--color-surface-fill-subtle)]"
        : variant === "danger"
          ? "border-rose-400/40 bg-rose-500/10 text-rose-200 hover:bg-rose-500/20"
          : "border-[color:var(--color-stroke-default)] bg-[color:var(--color-surface-panel-elevated)] text-[color:var(--color-text-secondary)] hover:border-[color:var(--color-text-muted)]";
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-1.5 rounded-full border px-3.5 py-2 text-sm font-medium outline-none transition duration-[var(--motion-duration-fast)] focus-visible:ring-2 focus-visible:ring-[color:var(--color-focus-ring)] disabled:cursor-not-allowed disabled:opacity-60",
        variantClass,
        className,
      )}
      {...props}
    />
  );
}

export function Badge({ className, variant = "neutral", children }: PropsWithChildren<{ className?: string; variant?: "neutral" | "info" | "success" | "warning" | "danger" | "waiting" | "blocked" }>) {
  const tone = {
    neutral: "border-[color:var(--color-stroke-default)] text-[color:var(--color-text-secondary)]",
    info: "border-blue-300/40 bg-blue-500/10 text-blue-100",
    success: "border-emerald-300/40 bg-emerald-500/10 text-emerald-100",
    warning: "border-amber-300/40 bg-amber-500/10 text-amber-100",
    danger: "border-rose-300/40 bg-rose-500/10 text-rose-100",
    waiting: "border-violet-300/40 bg-violet-500/10 text-violet-100",
    blocked: "border-rose-300/40 bg-rose-500/10 text-rose-100",
  }[variant];
  return <span className={cn("inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] uppercase tracking-[0.14em]", tone, className)}>{children}</span>;
}

export function FilterBar({ className, children }: PropsWithChildren<{ className?: string }>) {
  return <div className={cn("flex flex-wrap items-center gap-2 rounded-[var(--radius-md)] border border-[color:var(--color-stroke-default)] bg-[color:var(--color-surface-fill-subtle)] p-2", className)}>{children}</div>;
}

export function EmptyState({ title, description, className }: { title: string; description?: string; className?: string }) {
  return (
    <Card className={cn("px-4 py-5 text-sm text-[color:var(--color-text-muted)]", className)}>
      <div className="font-medium text-[color:var(--color-text-secondary)]">{title}</div>
      {description ? <div className="mt-1">{description}</div> : null}
    </Card>
  );
}

export function LoadingState({ label = "Loading…", className }: { label?: string; className?: string }) {
  return <Card className={cn("px-4 py-5 text-sm text-[color:var(--color-text-muted)]", className)}>{label}</Card>;
}

export function Drawer({ className, title, children }: PropsWithChildren<{ className?: string; title?: ReactNode }>) {
  return (
    <aside className={cn("rounded-[var(--radius-lg)] border border-[color:var(--color-stroke-default)] bg-[color:var(--color-surface-panel)] p-4 shadow-[var(--shadow-md)]", className)}>
      {title ? <div className="mb-3 text-sm font-semibold text-[color:var(--color-text-secondary)]">{title}</div> : null}
      {children}
    </aside>
  );
}

export function PageHeader({ title, subtitle, actions, className }: { title: ReactNode; subtitle?: ReactNode; actions?: ReactNode; className?: string }) {
  return (
    <header className={cn("flex flex-wrap items-start justify-between gap-3", className)}>
      <div>
        <h2 className="text-[length:var(--type-page-title-size)] leading-[var(--type-page-title-line-height)] font-semibold text-[color:var(--color-text-primary)]">{title}</h2>
        {subtitle ? <div className="mt-1 text-sm text-[color:var(--color-text-muted)]">{subtitle}</div> : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}
