import { Pill, SectionFrame, SectionTitle } from "@/components/ui";
import type { SearchHit } from "@/lib/api";
import { toDisplay } from "@/utils/display";

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
      <div className="mt-2 text-sm text-[color:var(--text-muted)]">
        Workspace-wide results across projects, tasks, questions, sessions, and events.
      </div>
      <div className="mt-4 flex flex-col gap-3">
        {deferredSearch.trim().length < 2 ? (
          <div className="text-sm text-[color:var(--text-muted)]">Type at least two characters to search the entire workspace.</div>
        ) : null}
        {hits.map((hit) => (
          <button
            key={`${hit.entity_type}-${hit.entity_id}`}
            onClick={() => onSelectHit(hit)}
            className="rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3 text-left hover:bg-[color:var(--surface-2)]"
          >
            <div className="flex items-center justify-between gap-3">
              <div className="text-sm font-semibold text-[color:var(--text)]">{hit.title}</div>
              <Pill>{toDisplay(hit.entity_type)}</Pill>
            </div>
            <div className="mt-2 line-clamp-2 text-sm text-[color:var(--text-muted)]">{formatSearchSnippet(hit)}</div>
            {hit.project_id ? (
              <div className="mt-2 text-xs text-[color:var(--text-faint)]">
                Project · {projectNameById.get(hit.project_id) ?? hit.project_id.slice(0, 8)}
              </div>
            ) : null}
          </button>
        ))}
      </div>
    </SectionFrame>
  );
}
