import type { ComponentPropsWithoutRef, PropsWithChildren, ReactNode } from "react";
import { Search } from "lucide-react";
import { cn } from "@/lib/utils";

export function Card({
  className,
  ...props
}: ComponentPropsWithoutRef<"div">) {
  return (
    <div
      className={cn(
        "card-surface",
        className,
      )}
      {...props}
    />
  );
}

export function Panel({
  className,
  ...props
}: ComponentPropsWithoutRef<"section">) {
  return (
    <section
      className={cn("rounded-[8px] border border-[color:var(--border)] bg-[color:var(--surface)] p-4", className)}
      {...props}
    />
  );
}

const controlBase =
  "w-full rounded-[4px] border border-[color:var(--border)] bg-[color:var(--surface)] px-3 py-2 text-sm text-[color:var(--text)] outline-none placeholder:text-[color:var(--text-faint)] focus-visible:border-[color:var(--accent)]";

export function Input({ className, ...props }: ComponentPropsWithoutRef<"input">) {
  return <input className={cn(controlBase, className)} {...props} />;
}

export function Select({ className, ...props }: ComponentPropsWithoutRef<"select">) {
  return <select className={cn(controlBase, "pr-8", className)} {...props} />;
}

export function Textarea({ className, ...props }: ComponentPropsWithoutRef<"textarea">) {
  return <textarea className={cn(controlBase, "min-h-24", className)} {...props} />;
}

export function SearchInput({
  className,
  inputClassName,
  ...props
}: ComponentPropsWithoutRef<"input"> & { inputClassName?: string }) {
  return (
    <div className={cn("relative", className)}>
      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[color:var(--text-faint)]" />
      <Input className={cn("pl-9", inputClassName)} {...props} />
    </div>
  );
}

export function Button({
  className,
  variant = "secondary",
  ...props
}: ComponentPropsWithoutRef<"button"> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
}) {
  const variantClass =
    variant === "primary"
      ? "btn-primary"
      : variant === "ghost"
        ? "btn-ghost"
        : variant === "danger"
          ? "btn-secondary border-rose-200 text-rose-600"
          : "btn-secondary";

  return <button className={cn("inline-flex items-center justify-center gap-1.5", variantClass, className)} {...props} />;
}

export function Badge({
  className,
  variant = "neutral",
  children,
}: PropsWithChildren<{
  className?: string;
  variant?: "neutral" | "info" | "success" | "warning" | "danger" | "waiting" | "blocked";
}>) {
  const tone = {
    neutral: "bg-zinc-100 text-zinc-700",
    info: "bg-blue-50 text-blue-700",
    success: "bg-emerald-50 text-emerald-700",
    warning: "bg-amber-50 text-amber-700",
    danger: "bg-rose-50 text-rose-700",
    waiting: "bg-violet-50 text-violet-700",
    blocked: "bg-rose-50 text-rose-700",
  }[variant];
  return <span className={cn("inline-flex items-center rounded-[4px] px-1.5 py-0.5 text-[11px] font-medium", tone, className)}>{children}</span>;
}

export function FilterBar({
  className,
  children,
}: PropsWithChildren<{ className?: string }>) {
  return <div className={cn("flex flex-wrap items-center gap-2 rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)] p-2", className)}>{children}</div>;
}

export function EmptyState({
  title,
  description,
  className,
}: {
  title: string;
  description?: string;
  className?: string;
}) {
  return (
    <Card className={cn("px-4 py-5 text-sm text-[color:var(--text-muted)]", className)}>
      <div className="font-medium text-[color:var(--text)]">{title}</div>
      {description ? <div className="mt-1">{description}</div> : null}
    </Card>
  );
}

export function LoadingState({
  label = "Loading…",
  className,
}: {
  label?: string;
  className?: string;
}) {
  return <Card className={cn("px-4 py-5 text-sm text-[color:var(--text-muted)]", className)}>{label}</Card>;
}

export function Drawer({
  className,
  title,
  children,
}: PropsWithChildren<{ className?: string; title?: ReactNode }>) {
  return (
    <aside className={cn("panel-surface p-4", className)}>
      {title ? <div className="mb-3 text-sm font-semibold text-[color:var(--text)]">{title}</div> : null}
      {children}
    </aside>
  );
}

export function PageHeader({
  title,
  subtitle,
  actions,
  className,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <header className={cn("flex flex-wrap items-start justify-between gap-3", className)}>
      <div>
        <h2 className="text-[20px] font-semibold text-[color:var(--text)]">{title}</h2>
        {subtitle ? <div className="mt-1 text-sm text-[color:var(--text-muted)]">{subtitle}</div> : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}
