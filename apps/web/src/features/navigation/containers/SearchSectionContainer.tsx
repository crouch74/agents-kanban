import { Pill, SectionFrame, SectionTitle } from "@/components/ui";
import type { SearchHit } from "@/lib/api";

export function SearchSectionContainer({
  deferredSearch,
  hits,
  formatSearchSnippet,
  projectNameById,
  onSelectHit,
}: {
  deferredSearch: string;
  hits: SearchHit[];
  formatSearchSnippet: (hit: SearchHit) => string;
  projectNameById: Map<string, string>;
  onSelectHit: (hit: SearchHit) => void;
}) {
  return (
    <SectionFrame className="px-5 py-5">
      <SectionTitle>Search Results</SectionTitle>
      <div className="mt-2 text-sm text-slate-500">
        Workspace-wide results across projects, tasks, questions, sessions, and events.
      </div>
      <div className="mt-4 flex flex-col gap-3">
        {deferredSearch.trim().length < 2 ? (
          <div className="text-sm text-slate-500">Type at least two characters to search the entire workspace.</div>
        ) : null}
        {hits.map((hit) => (
          <button
            key={`${hit.entity_type}-${hit.entity_id}`}
            onClick={() => onSelectHit(hit)}
            className="rounded-2xl border border-white/7 bg-white/3 px-4 py-3 text-left"
          >
            <div className="flex items-center justify-between gap-3">
              <div className="text-sm font-semibold text-slate-100">{hit.title}</div>
              <Pill className="border-white/8 text-slate-300">{hit.entity_type}</Pill>
            </div>
            <div className="mt-2 line-clamp-2 text-sm text-slate-500">{formatSearchSnippet(hit)}</div>
            {hit.project_id ? (
              <div className="mt-2 text-xs uppercase tracking-[0.16em] text-slate-600">
                Project · {projectNameById.get(hit.project_id) ?? hit.project_id.slice(0, 8)}
              </div>
            ) : null}
          </button>
        ))}
      </div>
    </SectionFrame>
  );
}
