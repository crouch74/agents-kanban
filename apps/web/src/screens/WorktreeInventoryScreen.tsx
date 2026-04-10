import { useMemo, useState, type ReactNode } from "react";
import { GitFork, Lock, Trash2 } from "lucide-react";
import type { SessionSummary, TaskSummary, WorktreeSummary, RepositorySummary } from "@acp/sdk";
import type { EventRecord } from "@/lib/api";
import { DataTable, type DataTableColumn } from "@/components/DataTable";
import { SectionFrame, SectionTitle } from "@/components/ui";
import { Badge, Button, SearchInput, Select } from "@/components/primitives";

type WorktreeInventoryScreenProps = {
  active: boolean;
  repositories: RepositorySummary[];
  worktrees: WorktreeSummary[];
  tasks: TaskSummary[];
  sessions: SessionSummary[];
  events: EventRecord[];
  loading?: boolean;
  error?: string | null;
  selectedWorktreeId?: string | null;
  onSelectWorktree?: (worktreeId: string) => void;
  onLock: (worktreeId: string) => void;
  onArchive: (worktreeId: string) => void;
  onPrune: (worktreeId: string) => void;
  controls?: ReactNode;
};

type WorktreeRow = {
  id: string;
  repository: string;
  branch: string;
  owner: string;
  lifecycle: string;
  path: string;
  recentActivity: string;
  raw: WorktreeSummary;
};

export function WorktreeInventoryScreen({
  active,
  repositories,
  worktrees,
  tasks,
  sessions,
  events,
  loading,
  error,
  selectedWorktreeId,
  onSelectWorktree,
  onLock,
  onArchive,
  onPrune,
  controls,
}: WorktreeInventoryScreenProps) {
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const repositoryById = useMemo(
    () => new Map(repositories.map((repo) => [repo.id, repo])),
    [repositories],
  );
  const taskById = useMemo(() => new Map(tasks.map((task) => [task.id, task])), [tasks]);

  const rows = useMemo<WorktreeRow[]>(() => {
    return worktrees.map((worktree) => {
      const owningTask = worktree.task_id ? taskById.get(worktree.task_id) : null;
      const owningSession = sessions.find((session) => session.worktree_id === worktree.id);
      const recent = events.find(
        (event) => event.entity_type === "worktree" && event.entity_id === worktree.id,
      );
      return {
        id: worktree.id,
        repository: repositoryById.get(worktree.repository_id)?.name ?? "unknown",
        branch: worktree.branch_name,
        owner: owningTask
          ? `task: ${owningTask.title}`
          : owningSession
            ? `session: ${owningSession.session_name}`
            : "unassigned",
        lifecycle: worktree.status,
        path: worktree.path,
        recentActivity: recent
          ? `${recent.event_type.replaceAll(".", " ")} · ${new Date(recent.created_at).toLocaleString()}`
          : "No recent event",
        raw: worktree,
      };
    });
  }, [events, repositoryById, sessions, taskById, worktrees]);

  const filteredRows = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return rows.filter((row) => {
      const matchesStatus = statusFilter === "all" || row.lifecycle === statusFilter;
      const matchesText =
        !normalized ||
        [row.repository, row.branch, row.owner, row.path, row.recentActivity]
          .join(" ")
          .toLowerCase()
          .includes(normalized);
      return matchesStatus && matchesText;
    });
  }, [query, rows, statusFilter]);

  const columns: DataTableColumn<WorktreeRow>[] = [
    { key: "repo", header: "Repo", render: (row) => row.repository },
    { key: "branch", header: "Branch", render: (row) => <span className="font-medium">{row.branch}</span> },
    { key: "owner", header: "Owner task/session", render: (row) => <span className="text-slate-300">{row.owner}</span> },
    {
      key: "lifecycle",
      header: "Lifecycle",
      render: (row) => <Badge variant="neutral">{row.lifecycle}</Badge>,
    },
    { key: "path", header: "Path", className: "w-[24%]", render: (row) => <span className="break-all text-xs text-slate-400">{row.path}</span> },
    { key: "recent", header: "Recent activity", className: "w-[24%]", render: (row) => <span className="text-xs text-slate-400">{row.recentActivity}</span> },
    {
      key: "actions",
      header: "Actions",
      render: (row) => (
        <div className="flex flex-wrap gap-2" onClick={(event) => event.stopPropagation()}>
          {row.raw.status === "active" ? (
            <>
              <Button onClick={() => onLock(row.id)} className="px-2.5 py-1 text-xs"><Lock className="h-3.5 w-3.5" />Lock</Button>
              <Button onClick={() => onArchive(row.id)} className="px-2.5 py-1 text-xs"><GitFork className="h-3.5 w-3.5" />Archive</Button>
            </>
          ) : null}
          {row.raw.status === "locked" || row.raw.status === "archived" ? (
            <Button variant="danger" onClick={() => onPrune(row.id)} className="px-2.5 py-1 text-xs"><Trash2 className="h-3.5 w-3.5" />Prune</Button>
          ) : null}
        </div>
      ),
    },
  ];

  if (!active) {
    return null;
  }

  return (
    <SectionFrame className="px-5 py-5">
      <SectionTitle>Worktree inventory</SectionTitle>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <SearchInput
          className="min-w-[280px] flex-1"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Filter by branch, owner, path, or activity"
          aria-label="Filter worktrees"
        />
        <Select
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
          className="max-w-56"
          aria-label="Filter lifecycle"
        >
          <option value="all">All lifecycle states</option>
          {[...new Set(worktrees.map((worktree) => worktree.status))].map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </Select>
      </div>
      <div className="mt-4">
        <DataTable
          columns={columns}
          rows={filteredRows}
          rowKey={(row) => row.id}
          rowClassName="align-top"
          onRowClick={onSelectWorktree ? (row) => onSelectWorktree(row.id) : undefined}
          selectedRowKey={selectedWorktreeId ?? null}
          state={{ loading, error, emptyMessage: "No worktrees match these filters yet." }}
        />
      </div>
      {controls ? <div className="mt-5">{controls}</div> : null}
    </SectionFrame>
  );
}
