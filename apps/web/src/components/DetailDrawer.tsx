import type { ReactNode } from "react";
import { ArrowUpRight, X } from "lucide-react";
import { Button } from "@/components/primitives";

export type DetailDrawerSection = {
  id: string;
  label: string;
  content: ReactNode;
};

type DetailDrawerProps = {
  title: string;
  subtitle?: string;
  sections: DetailDrawerSection[];
  onOpenFullDetail: () => void;
  onClose: () => void;
  openActionLabel?: string;
};

export function DetailDrawer({
  title,
  subtitle,
  sections,
  onOpenFullDetail,
  onClose,
  openActionLabel = "Open full detail",
}: DetailDrawerProps) {
  return (
    <section className="sticky top-6 rounded-3xl border border-white/8 bg-black/15">
      <header className="border-b border-white/8 px-4 py-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
              Quick inspect
            </div>
            <h3 className="mt-1 text-base font-semibold text-slate-100">{title}</h3>
            {subtitle ? <p className="mt-1 text-sm text-slate-400">{subtitle}</p> : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-white/10 p-1.5 text-slate-400 hover:text-slate-200"
            aria-label="Close quick inspect drawer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-3 flex flex-wrap gap-2">
          <Button onClick={onOpenFullDetail} className="px-3 py-1.5 text-xs">
            {openActionLabel}
            <ArrowUpRight className="ml-1 h-3.5 w-3.5" />
          </Button>
        </div>
      </header>

      <div className="px-4 py-3">
        <div className="mb-3 flex flex-wrap gap-1.5">
          {sections.map((section) => (
            <a
              key={section.id}
              href={`#drawer-${section.id}`}
              className="rounded-full border border-white/10 bg-black/20 px-2.5 py-1 text-[11px] uppercase tracking-[0.14em] text-slate-400 hover:text-slate-200"
            >
              {section.label}
            </a>
          ))}
        </div>

        <div className="max-h-[calc(100vh-15rem)] space-y-3 overflow-auto pr-1 scrollbar-thin">
          {sections.map((section) => (
            <section
              key={section.id}
              id={`drawer-${section.id}`}
              className="rounded-2xl border border-white/8 bg-white/3 p-3"
            >
              <div className="text-xs uppercase tracking-[0.16em] text-slate-500">{section.label}</div>
              <div className="mt-2 text-sm text-slate-200">{section.content}</div>
            </section>
          ))}
        </div>
      </div>
    </section>
  );
}
