import { useEffect, useState } from "react";
import { Command } from "cmdk";
import { Search } from "lucide-react";

export function CommandSearchTrigger({
  search,
  setSearch,
  onSearchActivate,
}: {
  search: string;
  setSearch: (value: string) => void;
  onSearchActivate: () => void;
}) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((value) => !value);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  return (
    <>
      <button type="button" className="btn-secondary min-w-[220px] justify-between" onClick={() => setOpen(true)}>
        <span className="inline-flex items-center gap-2 text-[color:var(--text-muted)]">
          <Search className="h-4 w-4" />
          {search.trim() ? search : "Search"}
        </span>
        <span className="text-[11px] text-[color:var(--text-faint)]">⌘K</span>
      </button>
      <Command.Dialog
        open={open}
        onOpenChange={setOpen}
        label="Global search"
        className="fixed left-1/2 top-[72px] z-[90] w-[min(640px,calc(100vw-32px))] -translate-x-1/2 overflow-hidden rounded-[8px] border border-[color:var(--border)] bg-[color:var(--surface)] shadow-[var(--shadow-panel)]"
      >
        <div className="sr-only">Global search</div>
        <div className="flex items-center gap-2 border-b border-[color:var(--border)] px-3">
          <Search className="h-4 w-4 text-[color:var(--text-muted)]" />
          <Command.Input
            value={search}
            onValueChange={(value) => {
              setSearch(value);
              if (value.trim().length > 0) {
                onSearchActivate();
              }
            }}
            placeholder="Search workspace"
            className="h-11 w-full border-0 bg-transparent outline-none"
          />
        </div>
        <Command.List className="max-h-[320px] overflow-auto px-3 py-2 text-sm text-[color:var(--text-muted)]">
          <Command.Empty>No results yet. Start typing to search the workspace.</Command.Empty>
          {search.trim().length > 0 ? (
            <Command.Item
              value={search}
              onSelect={() => {
                onSearchActivate();
                setOpen(false);
              }}
              className="rounded px-2 py-2 text-[color:var(--text)]"
            >
              Open search results for “{search}”
            </Command.Item>
          ) : null}
        </Command.List>
      </Command.Dialog>
    </>
  );
}
