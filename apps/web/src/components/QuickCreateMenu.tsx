import { Plus, WandSparkles } from "lucide-react";
import { Button } from "@/components/primitives";

export function QuickCreateMenu({
  quickCreateOpen,
  selectedProjectId,
  onToggle,
  onCreateTask,
  onBootstrap,
}: {
  quickCreateOpen: boolean;
  selectedProjectId: string | null;
  onToggle: () => void;
  onCreateTask: () => void;
  onBootstrap: () => void;
}) {
  return (
    <div className="relative">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={quickCreateOpen}
        className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900"
      >
        <Plus className="h-4 w-4" />
        Quick create
      </button>
      {quickCreateOpen ? (
        <div className="absolute right-0 z-20 mt-2 w-64 rounded-3xl border border-white/10 bg-slate-950/95 p-3 shadow-2xl backdrop-blur">
          <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Quick create</div>
          <div className="mt-3 flex flex-col gap-2">
            <Button
              variant="secondary"
              disabled={!selectedProjectId}
              onClick={onCreateTask}
              className="justify-start rounded-2xl px-4 py-3"
            >
              <Plus className="h-4 w-4" />
              New task
            </Button>
            {!selectedProjectId ? (
              <div className="px-1 text-xs text-slate-500">Select a project first to create a task.</div>
            ) : null}
            <Button
              variant="secondary"
              onClick={onBootstrap}
              className="justify-start rounded-2xl px-4 py-3"
            >
              <WandSparkles className="h-4 w-4" />
              New project bootstrap
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
