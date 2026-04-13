import { ChevronRight } from "lucide-react";
import { CommandSearchTrigger } from "@/components/ui";

export function AppHeader({
  breadcrumbs,
  search,
  setSearch,
  onSearchActivate,
}: {
  breadcrumbs: Array<{
    label: string;
    onActivate?: () => void;
  }>;
  search: string;
  setSearch: (value: string) => void;
  onSearchActivate: () => void;
}) {
  return (
    <div className="flex min-w-0 items-center justify-between gap-3">
      <div className="flex min-w-0 items-center gap-4">
        <div className="shrink-0 text-sm font-semibold text-[color:var(--text)]">
          Agent Control Plane
        </div>
        <div className="hidden min-w-0 items-center gap-2 text-sm text-[color:var(--text-muted)] md:flex">
          {breadcrumbs.map((crumb, index) => (
            <span
              key={`${crumb.label}-${index}`}
              className="inline-flex items-center gap-2 truncate"
            >
              {index ? <ChevronRight className="h-3.5 w-3.5 text-[color:var(--text-faint)]" /> : null}
              {crumb.onActivate ? (
                <button
                  type="button"
                  onClick={crumb.onActivate}
                  className="truncate text-left text-[color:var(--accent)] hover:underline"
                >
                  {crumb.label}
                </button>
              ) : (
                <span className="truncate">{crumb.label}</span>
              )}
            </span>
          ))}
        </div>
      </div>
      <div className="flex items-center gap-3">
        <CommandSearchTrigger
          search={search}
          setSearch={setSearch}
          onSearchActivate={onSearchActivate}
        />
        <div className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-zinc-900 text-xs font-semibold text-white">
          OP
        </div>
      </div>
    </div>
  );
}
