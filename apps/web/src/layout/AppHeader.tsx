import { ChevronRight, Search, SlidersHorizontal } from "lucide-react";
import { QuickCreateMenu } from "@/components/QuickCreateMenu";

export function AppHeader({
  breadcrumbs,
  sectionTitle,
  search,
  setSearch,
  onSearchActivate,
  quickCreateOpen,
  selectedProjectId,
  onToggleQuickCreate,
  onQuickCreateTask,
  onQuickCreateBootstrap,
}: {
  breadcrumbs: string[];
  sectionTitle: string;
  search: string;
  setSearch: (value: string) => void;
  onSearchActivate: () => void;
  quickCreateOpen: boolean;
  selectedProjectId: string | null;
  onToggleQuickCreate: () => void;
  onQuickCreateTask: () => void;
  onQuickCreateBootstrap: () => void;
}) {
  return (
    <section className="surface rounded-[28px] px-5 py-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-slate-500">
            {breadcrumbs.map((crumb, index) => (
              <span key={crumb} className="inline-flex items-center gap-2">
                {index ? <ChevronRight className="h-3 w-3" /> : null}
                {crumb}
              </span>
            ))}
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-slate-100">{sectionTitle}</h2>
        </div>
        <div className="flex items-center gap-2">
          <label className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/15 px-3 py-2 text-sm text-slate-400">
            <Search className="h-4 w-4" />
            <input
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                if (event.target.value.trim().length > 0) {
                  onSearchActivate();
                }
              }}
              className="w-52 border-0 bg-transparent p-0 text-sm outline-none placeholder:text-slate-600"
              placeholder="Search workspace"
            />
          </label>
          <QuickCreateMenu
            quickCreateOpen={quickCreateOpen}
            selectedProjectId={selectedProjectId}
            onToggle={onToggleQuickCreate}
            onCreateTask={onQuickCreateTask}
            onBootstrap={onQuickCreateBootstrap}
          />
          <button className="inline-flex items-center gap-2 rounded-full border border-white/10 px-4 py-2 text-sm text-slate-300">
            <SlidersHorizontal className="h-4 w-4" />
            View controls
          </button>
        </div>
      </div>
    </section>
  );
}
