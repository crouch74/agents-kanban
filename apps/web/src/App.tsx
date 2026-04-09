import { useDeferredValue, useEffect, useMemo, useState, startTransition } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  ArrowRight,
  Bot,
  FolderGit2,
  GitBranch,
  GitFork,
  Lock,
  MessageSquareText,
  Search,
  ShieldCheck,
  Trash2,
} from "lucide-react";
import type { TaskSummary } from "@acp/sdk";
import {
  createProject,
  createRepository,
  createTask,
  createWorktree,
  getDashboard,
  getDiagnostics,
  getProject,
  getProjects,
  patchWorktree,
} from "@/lib/api";
import { ColumnShell, Pill, SectionFrame, SectionTitle, StatTile } from "@/components/ui";
import { useUIStore } from "@/store/ui";

function formatEvent(eventType: string) {
  return eventType.replaceAll(".", " ").replaceAll("_", " ");
}

export function App() {
  const queryClient = useQueryClient();
  const { selectedProjectId, setSelectedProjectId } = useUIStore();
  const [search, setSearch] = useState("");
  const [draftProjectName, setDraftProjectName] = useState("");
  const [draftTaskTitle, setDraftTaskTitle] = useState("");
  const [draftRepoPath, setDraftRepoPath] = useState("");
  const [draftRepoName, setDraftRepoName] = useState("");
  const [draftWorktreeLabel, setDraftWorktreeLabel] = useState("");
  const [selectedRepositoryId, setSelectedRepositoryId] = useState<string | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string>("");
  const deferredSearch = useDeferredValue(search);

  const dashboardQuery = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
  });
  const diagnosticsQuery = useQuery({
    queryKey: ["diagnostics"],
    queryFn: getDiagnostics,
  });
  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: getProjects,
  });

  useEffect(() => {
    if (!selectedProjectId && projectsQuery.data?.[0]) {
      setSelectedProjectId(projectsQuery.data[0].id);
    }
  }, [projectsQuery.data, selectedProjectId, setSelectedProjectId]);

  const projectDetailQuery = useQuery({
    queryKey: ["project", selectedProjectId],
    queryFn: () => getProject(selectedProjectId!),
    enabled: Boolean(selectedProjectId),
  });

  useEffect(() => {
    setSelectedRepositoryId(null);
    setSelectedTaskId("");
  }, [selectedProjectId]);

  useEffect(() => {
    const repositories = projectDetailQuery.data?.repositories ?? [];
    if (!selectedRepositoryId && repositories[0]) {
      setSelectedRepositoryId(repositories[0].id);
    }
  }, [projectDetailQuery.data?.repositories, selectedRepositoryId]);

  const createProjectMutation = useMutation({
    mutationFn: createProject,
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      startTransition(() => {
        setSelectedProjectId(project.id);
        setDraftProjectName("");
      });
    },
  });

  const createTaskMutation = useMutation({
    mutationFn: createTask,
    onSuccess: () => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({ queryKey: ["project", selectedProjectId] });
      }
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      setDraftTaskTitle("");
    },
  });

  const createRepositoryMutation = useMutation({
    mutationFn: createRepository,
    onSuccess: (repository) => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({ queryKey: ["project", selectedProjectId] });
      }
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      setSelectedRepositoryId(repository.id);
      setDraftRepoPath("");
      setDraftRepoName("");
    },
  });

  const createWorktreeMutation = useMutation({
    mutationFn: createWorktree,
    onSuccess: () => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({ queryKey: ["project", selectedProjectId] });
      }
      setDraftWorktreeLabel("");
      setSelectedTaskId("");
    },
  });

  const patchWorktreeMutation = useMutation({
    mutationFn: ({ worktreeId, status }: { worktreeId: string; status: string }) =>
      patchWorktree(worktreeId, { status }),
    onSuccess: () => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({ queryKey: ["project", selectedProjectId] });
      }
    },
  });

  const filteredProjects = useMemo(() => {
    const projects = projectsQuery.data ?? [];
    const needle = deferredSearch.trim().toLowerCase();
    if (!needle) {
      return projects;
    }

    return projects.filter((project) => {
      return (
        project.name.toLowerCase().includes(needle) ||
        project.slug.toLowerCase().includes(needle) ||
        (project.description ?? "").toLowerCase().includes(needle)
      );
    });
  }, [deferredSearch, projectsQuery.data]);

  const groupedTasks = useMemo(() => {
    const board = projectDetailQuery.data?.board;
    if (!board) {
      return new Map<string, TaskSummary[]>();
    }

    const map = new Map<string, TaskSummary[]>();
    board.columns.forEach((column) => map.set(column.id, []));
    board.tasks.forEach((task) => {
      const entry = map.get(task.board_column_id);
      if (entry) {
        entry.push(task);
      }
    });
    return map;
  }, [projectDetailQuery.data]);

  const topLevelTasks = useMemo(() => {
    return (projectDetailQuery.data?.board.tasks ?? []).filter((task) => !task.parent_task_id);
  }, [projectDetailQuery.data]);

  return (
    <div className="grid-shell">
      <aside className="border-r border-white/8 px-6 py-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Agent Control Plane</p>
            <h1 className="mt-3 text-2xl font-semibold tracking-tight">Local operator workspace</h1>
          </div>
          <Pill className="border-emerald-400/20 bg-emerald-400/10 text-emerald-200">v0.1</Pill>
        </div>

        <div className="mt-8 rounded-3xl border border-white/7 bg-white/3 px-4 py-3">
          <label className="flex items-center gap-3 text-sm text-slate-300">
            <Search className="h-4 w-4 text-slate-500" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              className="w-full border-0 bg-transparent p-0 text-sm outline-none placeholder:text-slate-600"
              placeholder="Search projects"
            />
          </label>
        </div>

        <div className="mt-8">
          <SectionTitle>Projects</SectionTitle>
          <div className="mt-4 flex flex-col gap-3">
            {filteredProjects.map((project) => (
              <button
                key={project.id}
                onClick={() => setSelectedProjectId(project.id)}
                className={[
                  "rounded-3xl border px-4 py-4 text-left transition",
                  selectedProjectId === project.id
                    ? "border-[color:var(--accent)] bg-[color:var(--accent-soft)]"
                    : "border-white/7 bg-white/2 hover:bg-white/5",
                ].join(" ")}
              >
                <div className="text-sm font-semibold text-slate-100">{project.name}</div>
                <div className="mt-1 text-sm text-slate-500">{project.description ?? project.slug}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="mt-8 rounded-3xl border border-white/7 bg-white/2 p-4">
          <SectionTitle>Create Project</SectionTitle>
          <input
            value={draftProjectName}
            onChange={(event) => setDraftProjectName(event.target.value)}
            placeholder="Acme migration program"
            className="mt-4 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
          />
          <button
            onClick={() => createProjectMutation.mutate({ name: draftProjectName })}
            disabled={!draftProjectName.trim() || createProjectMutation.isPending}
            className="mt-3 inline-flex items-center gap-2 rounded-full bg-[color:var(--accent)] px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Create
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </aside>

      <main className="px-6 py-6">
        <section className="surface rounded-[32px] px-6 py-6">
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Operational overview</p>
              <h2 className="mt-3 text-4xl font-semibold tracking-tight">Observe, steer, resume.</h2>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
                The control plane keeps project state, board flow, runtime context, and future agent
                sessions in one local-first workspace.
              </p>
            </div>
            <div className="flex items-center gap-3 text-sm text-slate-400">
              <Activity className="h-4 w-4 text-[color:var(--accent)]" />
              {diagnosticsQuery.data?.environment ?? "development"} environment
            </div>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-4">
            <StatTile label="Projects" value={dashboardQuery.data?.projects.length ?? 0} />
            <StatTile label="Waiting" value={dashboardQuery.data?.waiting_count ?? 0} />
            <StatTile label="Blocked" value={dashboardQuery.data?.blocked_count ?? 0} />
            <StatTile label="Running Sessions" value={dashboardQuery.data?.running_sessions ?? 0} />
          </div>
        </section>

        <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
          <SectionFrame className="px-5 py-5">
            <div className="flex items-center justify-between gap-4">
              <div>
                <SectionTitle>Project Board</SectionTitle>
                <h3 className="mt-2 text-2xl font-semibold">
                  {projectDetailQuery.data?.project.name ?? "Select or create a project"}
                </h3>
              </div>
              {selectedProjectId ? (
                <div className="flex items-center gap-3">
                  <input
                    value={draftTaskTitle}
                    onChange={(event) => setDraftTaskTitle(event.target.value)}
                    placeholder="Add a task"
                    className="rounded-full border border-white/8 bg-black/15 px-4 py-2 text-sm outline-none"
                  />
                  <button
                    onClick={() =>
                      createTaskMutation.mutate({
                        project_id: selectedProjectId,
                        title: draftTaskTitle,
                      })
                    }
                    disabled={!draftTaskTitle.trim() || createTaskMutation.isPending}
                    className="rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    New task
                  </button>
                </div>
              ) : null}
            </div>

            <div className="mt-6 flex gap-4 overflow-x-auto pb-2 scrollbar-thin">
              {projectDetailQuery.data?.board.columns.map((column) => (
                <ColumnShell key={column.id} className="flex flex-col gap-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <div className="text-sm font-semibold">{column.name}</div>
                      <div className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-500">
                        {column.key}
                      </div>
                    </div>
                    <Pill className="border-white/8 text-slate-300">
                      {groupedTasks.get(column.id)?.length ?? 0}
                      {column.wip_limit ? ` / ${column.wip_limit}` : ""}
                    </Pill>
                  </div>

                  <div className="space-y-3">
                    {(groupedTasks.get(column.id) ?? []).map((task) => (
                      <div key={task.id} className="rounded-2xl border border-white/8 bg-white/4 p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div className="text-sm font-semibold text-slate-100">{task.title}</div>
                          <Pill
                            className={
                              task.waiting_for_human
                                ? "border-amber-300/25 bg-amber-300/10 text-amber-100"
                                : task.blocked_reason
                                  ? "border-rose-300/25 bg-rose-300/10 text-rose-100"
                                  : "border-white/8 text-slate-300"
                            }
                          >
                            {task.waiting_for_human ? "Waiting" : task.blocked_reason ? "Blocked" : task.priority}
                          </Pill>
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
                          {task.tags.map((tag) => (
                            <span key={tag}>#{tag}</span>
                          ))}
                          {!task.tags.length ? <span>No tags yet</span> : null}
                        </div>
                      </div>
                    ))}
                    {!groupedTasks.get(column.id)?.length ? (
                      <div className="rounded-2xl border border-dashed border-white/8 px-4 py-6 text-sm text-slate-500">
                        No tasks in this column yet.
                      </div>
                    ) : null}
                  </div>
                </ColumnShell>
              ))}
            </div>
          </SectionFrame>

          <div className="flex flex-col gap-6">
            <SectionFrame className="px-5 py-5">
              <SectionTitle>Repository Inventory</SectionTitle>
              <div className="mt-4 flex flex-col gap-3">
                {projectDetailQuery.data?.repositories.map((repository) => (
                  <div key={repository.id} className="rounded-2xl border border-white/7 bg-white/3 px-4 py-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-slate-100">{repository.name}</div>
                        <div className="mt-1 break-all text-xs text-slate-500">{repository.local_path}</div>
                      </div>
                      <Pill className="border-white/8 text-slate-300">
                        {repository.default_branch ?? "detached"}
                      </Pill>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
                      <span>dirty: {String(repository.metadata_json.is_dirty ?? false)}</span>
                      <span>remotes: {Array.isArray(repository.metadata_json.remotes) ? repository.metadata_json.remotes.length : 0}</span>
                    </div>
                  </div>
                ))}
                {!projectDetailQuery.data?.repositories.length ? (
                  <div className="text-sm text-slate-500">Attach a local git repo to unlock worktrees.</div>
                ) : null}
              </div>

              {selectedProjectId ? (
                <div className="mt-5 rounded-2xl border border-white/7 bg-black/10 p-4">
                  <div className="text-sm font-medium text-slate-200">Attach repository</div>
                  <input
                    value={draftRepoPath}
                    onChange={(event) => setDraftRepoPath(event.target.value)}
                    placeholder="/absolute/path/to/repo"
                    className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                  />
                  <input
                    value={draftRepoName}
                    onChange={(event) => setDraftRepoName(event.target.value)}
                    placeholder="Optional display name"
                    className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                  />
                  <button
                    onClick={() =>
                      createRepositoryMutation.mutate({
                        project_id: selectedProjectId,
                        local_path: draftRepoPath,
                        name: draftRepoName || undefined,
                      })
                    }
                    disabled={!draftRepoPath.trim() || createRepositoryMutation.isPending}
                    className="mt-3 rounded-full bg-[color:var(--accent)] px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Attach repo
                  </button>
                </div>
              ) : null}
            </SectionFrame>

            <SectionFrame className="px-5 py-5">
              <SectionTitle>Worktree Fleet</SectionTitle>
              <div className="mt-4 flex flex-col gap-3">
                {projectDetailQuery.data?.worktrees.map((worktree) => (
                  <div key={worktree.id} className="rounded-2xl border border-white/7 bg-white/3 px-4 py-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 text-sm font-semibold text-slate-100">
                          <GitBranch className="h-4 w-4 text-slate-400" />
                          <span className="truncate">{worktree.branch_name}</span>
                        </div>
                        <div className="mt-1 break-all text-xs text-slate-500">{worktree.path}</div>
                      </div>
                      <Pill className="border-white/8 text-slate-300">{worktree.status}</Pill>
                    </div>
                    <div className="mt-3 flex gap-2">
                      {worktree.status === "active" ? (
                        <>
                          <button
                            onClick={() => patchWorktreeMutation.mutate({ worktreeId: worktree.id, status: "locked" })}
                            className="inline-flex items-center gap-2 rounded-full border border-white/8 px-3 py-1.5 text-xs text-slate-200"
                          >
                            <Lock className="h-3.5 w-3.5" />
                            Lock
                          </button>
                          <button
                            onClick={() => patchWorktreeMutation.mutate({ worktreeId: worktree.id, status: "archived" })}
                            className="inline-flex items-center gap-2 rounded-full border border-white/8 px-3 py-1.5 text-xs text-slate-200"
                          >
                            <GitFork className="h-3.5 w-3.5" />
                            Archive
                          </button>
                        </>
                      ) : null}
                      {worktree.status === "locked" || worktree.status === "archived" ? (
                        <button
                          onClick={() => patchWorktreeMutation.mutate({ worktreeId: worktree.id, status: "pruned" })}
                          className="inline-flex items-center gap-2 rounded-full border border-rose-300/20 px-3 py-1.5 text-xs text-rose-100"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          Prune
                        </button>
                      ) : null}
                    </div>
                  </div>
                ))}
                {!projectDetailQuery.data?.worktrees.length ? (
                  <div className="text-sm text-slate-500">No worktrees allocated yet.</div>
                ) : null}
              </div>

              {selectedProjectId ? (
                <div className="mt-5 rounded-2xl border border-white/7 bg-black/10 p-4">
                  <div className="text-sm font-medium text-slate-200">Allocate worktree</div>
                  <select
                    value={selectedRepositoryId ?? ""}
                    onChange={(event) => setSelectedRepositoryId(event.target.value || null)}
                    className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                  >
                    <option value="">Choose repository</option>
                    {(projectDetailQuery.data?.repositories ?? []).map((repository) => (
                      <option key={repository.id} value={repository.id}>
                        {repository.name}
                      </option>
                    ))}
                  </select>
                  <select
                    value={selectedTaskId}
                    onChange={(event) => setSelectedTaskId(event.target.value)}
                    className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                  >
                    <option value="">No task linkage</option>
                    {topLevelTasks.map((task) => (
                      <option key={task.id} value={task.id}>
                        {task.title}
                      </option>
                    ))}
                  </select>
                  <input
                    value={draftWorktreeLabel}
                    onChange={(event) => setDraftWorktreeLabel(event.target.value)}
                    placeholder="Optional label for an unlinked worktree"
                    className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                  />
                  <button
                    onClick={() =>
                      createWorktreeMutation.mutate({
                        repository_id: selectedRepositoryId!,
                        task_id: selectedTaskId || undefined,
                        label: selectedTaskId ? undefined : draftWorktreeLabel || undefined,
                      })
                    }
                    disabled={!selectedRepositoryId || createWorktreeMutation.isPending}
                    className="mt-3 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Allocate
                  </button>
                </div>
              ) : null}
            </SectionFrame>

            <SectionFrame className="px-5 py-5">
              <SectionTitle>Runtime readiness</SectionTitle>
              <div className="mt-5 grid gap-3">
                <Signal label="tmux" ready={Boolean(diagnosticsQuery.data?.tmux_available)} icon={Bot} />
                <Signal label="git" ready={Boolean(diagnosticsQuery.data?.git_available)} icon={FolderGit2} />
                <Signal label="audit log" ready icon={ShieldCheck} />
                <Signal label="waiting inbox" ready icon={MessageSquareText} />
              </div>
            </SectionFrame>

            <SectionFrame className="px-5 py-5">
              <SectionTitle>Recent events</SectionTitle>
              <div className="mt-4 flex flex-col gap-3">
                {dashboardQuery.data?.recent_events.map((event) => (
                  <div key={event.id} className="rounded-2xl border border-white/7 bg-white/3 px-4 py-3">
                    <div className="text-sm font-medium text-slate-100">{formatEvent(event.event_type)}</div>
                    <div className="mt-1 text-sm text-slate-500">
                      {event.actor_name} on {event.entity_type}
                    </div>
                  </div>
                ))}
                {!dashboardQuery.data?.recent_events.length ? (
                  <div className="text-sm text-slate-500">Events will appear here as work is created and updated.</div>
                ) : null}
              </div>
            </SectionFrame>
          </div>
        </div>
      </main>
    </div>
  );
}

function Signal({
  label,
  ready,
  icon: Icon,
}: {
  label: string;
  ready: boolean;
  icon: typeof Activity;
}) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-white/7 bg-white/3 px-4 py-3">
      <div className="flex items-center gap-3">
        <Icon className="h-4 w-4 text-slate-400" />
        <span className="text-sm text-slate-300">{label}</span>
      </div>
      <Pill
        className={
          ready
            ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-100"
            : "border-amber-400/20 bg-amber-400/10 text-amber-100"
        }
      >
        {ready ? "ready" : "pending"}
      </Pill>
    </div>
  );
}
