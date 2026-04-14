import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  DndContext,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import * as Drawer from "vaul";
import { MoreHorizontal, X } from "lucide-react";
import { WorkflowState } from "@acp/sdk";
import { AppShell } from "@/layout/AppShell";
import { SidebarNavigation } from "@/layout/SidebarNavigation";
import { AppHeader } from "@/layout/AppHeader";
import { useUIStore } from "@/store/ui";
import {
  addTaskComment,
  createProject,
  createTask,
  getDashboard,
  getDiagnostics,
  getEvents,
  getProject,
  getProjects,
  getTaskDetail,
  patchTask,
  purgeDatabase,
  searchContext,
} from "@/lib/api";
import type { EventRecord, SearchHit, TaskSummary } from "@/lib/api";
import { Button } from "@/components/primitives";
import { DialogFrame, StatusDot } from "@/components/ui";
import { ProjectBootstrapWizard } from "@/components/project-bootstrap-wizard";
import {
  BoardColumnHeader,
  DraggableTaskCard,
  DroppableBoardColumn,
} from "@/screens/ProjectBoardScreen";
import { TaskDetailScreen } from "@/screens/TaskDetailScreen";
import { useAppUrlState } from "@/app-shell/useAppUrlState";

function sectionTitle(section: "home" | "projects" | "search" | "activity" | "settings" | "howto"): string {
  if (section === "home") return "Home";
  if (section === "projects") return "Projects";
  if (section === "search") return "Search";
  if (section === "settings") return "Settings";
  if (section === "howto") return "How-To";
  return "Activity";
}

function formatEvent(eventType: string): string {
  return eventType.replaceAll(".", " ").replaceAll("_", " ");
}

function socketBase(): string {
  const env = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env ?? {};
  return env.VITE_WS_BASE?.trim() || "ws://127.0.0.1:8000/api/v1/ws";
}

export function App() {
  const queryClient = useQueryClient();
  const { selectedProjectId, setSelectedProjectId } = useUIStore();
  const [activeSection, setActiveSection] = useState<"home" | "projects" | "search" | "activity" | "settings" | "howto">("projects");
  const [search, setSearch] = useState("");
  const [draftTaskTitle, setDraftTaskTitle] = useState("");
  const [inspectedTaskId, setInspectedTaskId] = useState<string | null>(null);
  const [projectDialogOpen, setProjectDialogOpen] = useState(false);
  const [mobileTaskPanelOpen, setMobileTaskPanelOpen] = useState(false);
  const [draftCommentBody, setDraftCommentBody] = useState("");
  const deferredSearch = useDeferredValue(search);
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 8 } }));

  useAppUrlState({
    activeSection,
    selectedProjectId,
    inspectedTaskId,
    setActiveSection,
    setSelectedProjectId,
    setInspectedTaskId,
    setDrawerSelection: (selection) => {
      setInspectedTaskId(selection?.type === "task" ? selection.id : null);
    },
  });

  const projectsQuery = useQuery({ queryKey: ["projects"], queryFn: getProjects });
  const dashboardQuery = useQuery({ queryKey: ["dashboard"], queryFn: getDashboard });
  const projectDetailQuery = useQuery({
    queryKey: ["project", selectedProjectId],
    queryFn: () => getProject(selectedProjectId!),
    enabled: Boolean(selectedProjectId),
  });
  const taskDetailQuery = useQuery({
    queryKey: ["task", inspectedTaskId],
    queryFn: () => getTaskDetail(inspectedTaskId!),
    enabled: Boolean(inspectedTaskId),
  });
  const eventsQuery = useQuery({
    queryKey: ["events", selectedProjectId],
    queryFn: () => getEvents({ projectId: selectedProjectId ?? undefined, limit: 40 }),
  });
  const searchQuery = useQuery({
    queryKey: ["search", deferredSearch, selectedProjectId],
    queryFn: () => searchContext(deferredSearch, selectedProjectId ?? undefined),
    enabled: deferredSearch.trim().length >= 2,
  });
  const diagnosticsQuery = useQuery({ queryKey: ["settings", "diagnostics"], queryFn: getDiagnostics });

  useEffect(() => {
    if (!selectedProjectId && projectsQuery.data?.[0]) {
      setSelectedProjectId(projectsQuery.data[0].id);
    }
  }, [projectsQuery.data, selectedProjectId, setSelectedProjectId]);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.WebSocket === "undefined") {
      return;
    }
    const socket = new window.WebSocket(socketBase());
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as { type?: string };
      if (payload.type === "system.connected" || payload.type === "system.ping") {
        return;
      }
      queryClient.invalidateQueries();
    };
    return () => socket.close();
  }, [queryClient]);

  const createProjectMutation = useMutation({
    mutationFn: createProject,
    onSuccess: (project) => {
      setSelectedProjectId(project.id);
      setProjectDialogOpen(false);
      setActiveSection("projects");
      queryClient.invalidateQueries();
    },
  });

  const createTaskMutation = useMutation({
    mutationFn: createTask,
    onSuccess: () => {
      setDraftTaskTitle("");
      queryClient.invalidateQueries();
    },
  });

  const moveTaskMutation = useMutation({
    mutationFn: ({ taskId, boardColumnId }: { taskId: string; boardColumnId: string }) =>
      patchTask(taskId, { board_column_id: boardColumnId }),
    onSuccess: () => queryClient.invalidateQueries(),
  });

  const patchDescriptionMutation = useMutation({
    mutationFn: ({ taskId, description }: { taskId: string; description: string }) =>
      patchTask(taskId, { description }),
    onSuccess: () => queryClient.invalidateQueries(),
  });

  const addCommentMutation = useMutation({
    mutationFn: ({ taskId, body }: { taskId: string; body: string }) =>
      addTaskComment(taskId, { author_name: "operator", author_type: "human", source: "web", body }),
    onSuccess: () => {
      setDraftCommentBody("");
      queryClient.invalidateQueries();
    },
  });
  const purgeDatabaseMutation = useMutation({
    mutationFn: purgeDatabase,
    onSuccess: () => {
      setSelectedProjectId(null);
      setInspectedTaskId(null);
      queryClient.invalidateQueries();
    },
  });

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

  const filteredProjects = useMemo(() => {
    const projects = projectsQuery.data ?? [];
    const needle = deferredSearch.trim().toLowerCase();
    if (!needle) return projects;
    return projects.filter((project) =>
      project.name.toLowerCase().includes(needle) ||
      project.slug.toLowerCase().includes(needle) ||
      (project.description ?? "").toLowerCase().includes(needle),
    );
  }, [deferredSearch, projectsQuery.data]);

  const breadcrumbs = useMemo(
    () => [
      { label: sectionTitle(activeSection), onActivate: () => setActiveSection(activeSection) },
      ...(projectDetailQuery.data?.project
        ? [{ label: projectDetailQuery.data.project.name, onActivate: () => setActiveSection("projects") }]
        : []),
      ...(taskDetailQuery.data?.title ? [{ label: taskDetailQuery.data.title }] : []),
    ],
    [activeSection, projectDetailQuery.data?.project, taskDetailQuery.data?.title],
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || !projectDetailQuery.data) return;
    const taskId = String(active.id);
    const boardColumnId = String(over.id);
    const task = projectDetailQuery.data.board.tasks.find((candidate) => candidate.id === taskId);
    const column = projectDetailQuery.data.board.columns.find((candidate) => candidate.id === boardColumnId);
    if (!task || !column || task.board_column_id === column.id) return;
    moveTaskMutation.mutate({ taskId, boardColumnId: column.id });
  };

  const mainContent = (() => {
    if (activeSection === "home") {
      return (
        <div className="page-frame p-4">
          <h2 className="text-lg font-semibold">Workspace summary</h2>
          <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(dashboardQuery.data?.task_counts ?? {}).map(([state, count]) => (
              <div key={state} className="rounded border border-[color:var(--border)] bg-[color:var(--surface)] p-3">
                <div className="text-sm text-[color:var(--text-muted)]">{state}</div>
                <div className="text-2xl font-semibold">{count}</div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    if (activeSection === "search") {
      const hits = searchQuery.data?.hits ?? [];
      return (
        <div className="page-frame p-4">
          <h2 className="text-lg font-semibold">Search</h2>
          <div className="mt-3 space-y-2">
            {hits.map((hit: SearchHit) => (
              <button
                key={`${hit.entity_type}:${hit.entity_id}`}
                type="button"
                onClick={() => {
                  if (hit.project_id) setSelectedProjectId(hit.project_id);
                  if (hit.entity_type === "task") {
                    setInspectedTaskId(hit.entity_id);
                    setActiveSection("projects");
                  } else {
                    setActiveSection("activity");
                  }
                }}
                className="w-full rounded border border-[color:var(--border)] bg-[color:var(--surface)] p-3 text-left"
              >
                <div className="text-sm font-medium">{hit.title}</div>
                <div className="text-xs text-[color:var(--text-muted)]">{hit.snippet}</div>
              </button>
            ))}
          </div>
        </div>
      );
    }

    if (activeSection === "activity") {
      return (
        <div className="page-frame p-4">
          <h2 className="text-lg font-semibold">Activity</h2>
          <div className="mt-3 space-y-2">
            {(eventsQuery.data ?? []).map((event: EventRecord) => (
              <div key={event.id} className="rounded border border-[color:var(--border)] bg-[color:var(--surface)] p-3">
                <div className="text-sm font-medium">{formatEvent(event.event_type)}</div>
                <div className="text-xs text-[color:var(--text-muted)]">{new Date(event.created_at).toLocaleString()}</div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    if (activeSection === "settings") {
      const diagnostics = diagnosticsQuery.data;
      return (
        <div className="page-frame p-4 space-y-4">
          <h2 className="text-lg font-semibold">Settings</h2>
          <div className="rounded border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
            <div className="text-sm font-medium">Service diagnostics</div>
            <div className="mt-3 grid gap-2">
              {Object.entries(diagnostics?.services ?? {}).map(([name, service]) => (
                <div key={name} className="rounded border border-[color:var(--border)] p-3 text-sm">
                  <div className="font-medium">{name}</div>
                  <div className="text-[color:var(--text-muted)]">{service.status}</div>
                  {service.detail ? <div className="text-xs text-[color:var(--text-faint)]">{service.detail}</div> : null}
                </div>
              ))}
            </div>
          </div>
          <div className="rounded border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
            <div className="text-sm font-medium">Database and data paths</div>
            <div className="mt-3 space-y-2 text-sm">
              {Object.entries(diagnostics?.paths ?? {}).map(([key, value]) => (
                <div key={key} className="rounded border border-[color:var(--border)] p-2">
                  <div className="font-medium">{key}</div>
                  <div className="font-mono text-xs text-[color:var(--text-muted)]">{value}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded border border-rose-200 bg-rose-50 p-4">
            <div className="text-sm font-medium text-rose-700">Danger zone</div>
            <div className="mt-1 text-xs text-rose-700">Purges all board data from the local database.</div>
            <Button
              className="mt-3"
              variant="danger"
              onClick={() => {
                if (typeof window !== "undefined") {
                  const confirmed = window.confirm(
                    "Purge all projects, tasks, comments, and events from the local database? This cannot be undone.",
                  );
                  if (!confirmed) {
                    return;
                  }
                }
                purgeDatabaseMutation.mutate();
              }}
              disabled={purgeDatabaseMutation.isPending}
            >
              {purgeDatabaseMutation.isPending ? "Purging database..." : "Purge database"}
            </Button>
          </div>
        </div>
      );
    }

    if (activeSection === "howto") {
      return (
        <div className="page-frame p-4 space-y-4">
          <h2 className="text-lg font-semibold">How-To</h2>
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="space-y-4 rounded border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
              <div>
                <div className="text-base font-semibold">Pane 1: MCP Integration</div>
                <div className="text-xs text-[color:var(--text-muted)]">
                  Connect directly to the local MCP server for project, task, and workflow tooling.
                </div>
              </div>
              <div className="rounded border border-[color:var(--border)] bg-[color:var(--panel)] p-4">
                <div className="text-sm font-medium">Codex</div>
                <pre className="mt-2 overflow-auto rounded bg-zinc-950 p-3 text-xs text-zinc-100">{`# ~/.codex/config.toml
[mcp_servers.kanban_task_board]
command = "bash"
args = ["-lc", "cd /Users/aeid/git_tree/kanban && export PYTHONPATH=/Users/aeid/git_tree/kanban/packages/core/src:/Users/aeid/git_tree/kanban/packages/mcp-server/src:\${PYTHONPATH:-} && /Users/aeid/git_tree/kanban/.venv/bin/python -c 'from acp_mcp_server.server import mcp; mcp.run()'"]`}</pre>
              </div>
              <div className="rounded border border-[color:var(--border)] bg-[color:var(--panel)] p-4">
                <div className="text-sm font-medium">Claude Code / Claude Desktop</div>
                <pre className="mt-2 overflow-auto rounded bg-zinc-950 p-3 text-xs text-zinc-100">{`{
  "mcpServers": {
    "kanban_task_board": {
      "command": "bash",
      "args": [
        "-lc",
        "cd /Users/aeid/git_tree/kanban && export PYTHONPATH=/Users/aeid/git_tree/kanban/packages/core/src:/Users/aeid/git_tree/kanban/packages/mcp-server/src:\${PYTHONPATH:-} && /Users/aeid/git_tree/kanban/.venv/bin/python -c 'from acp_mcp_server.server import mcp; mcp.run()'"
      ]
    }
  }
}`}</pre>
              </div>
              <div className="rounded border border-[color:var(--border)] bg-[color:var(--panel)] p-4">
                <div className="text-sm font-medium">Cursor</div>
                <pre className="mt-2 overflow-auto rounded bg-zinc-950 p-3 text-xs text-zinc-100">{`{
  "mcpServers": {
    "kanban_task_board": {
      "command": "bash",
      "args": [
        "-lc",
        "cd /Users/aeid/git_tree/kanban && export PYTHONPATH=/Users/aeid/git_tree/kanban/packages/core/src:/Users/aeid/git_tree/kanban/packages/mcp-server/src:\${PYTHONPATH:-} && /Users/aeid/git_tree/kanban/.venv/bin/python -c 'from acp_mcp_server.server import mcp; mcp.run()'"
      ]
    }
  }
}`}</pre>
              </div>
              <div className="rounded border border-[color:var(--border)] bg-[color:var(--panel)] p-4 text-sm">
                <div className="font-medium">Generic MCP-capable Agent</div>
                <div className="mt-2 text-[color:var(--text-muted)]">
                  Register a stdio MCP server named <span className="font-mono">kanban_task_board</span> using:
                  <span className="mt-1 block rounded bg-zinc-950 p-2 font-mono text-xs text-zinc-100">
                    bash -lc "cd /Users/aeid/git_tree/kanban && export
                    PYTHONPATH=/Users/aeid/git_tree/kanban/packages/core/src:/Users/aeid/git_tree/kanban/packages/mcp-server/src:$PYTHONPATH
                    && /Users/aeid/git_tree/kanban/.venv/bin/python -c 'from acp_mcp_server.server import mcp; mcp.run()'"
                  </span>
                </div>
              </div>
            </div>
            <div className="space-y-4 rounded border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
              <div>
                <div className="text-base font-semibold">Pane 2: Skill Integration</div>
                <div className="text-xs text-[color:var(--text-muted)]">
                  Use a local skill file so prompts can call this board API consistently.
                </div>
              </div>
              <div className="rounded border border-[color:var(--border)] bg-[color:var(--panel)] p-4">
                <div className="text-sm font-medium">Codex</div>
                <pre className="mt-2 overflow-auto rounded bg-zinc-950 p-3 text-xs text-zinc-100">{`# ~/.codex/config.toml
[[skills.config]]
path = "/Users/aeid/git_tree/kanban/skills/agent-control-plane-api/SKILL.md"
enabled = true`}</pre>
              </div>
              <div className="rounded border border-[color:var(--border)] bg-[color:var(--panel)] p-4">
                <div className="text-sm font-medium">Claude Code</div>
                <pre className="mt-2 overflow-auto rounded bg-zinc-950 p-3 text-xs text-zinc-100">{`# Use this skill in system prompt or project instructions:
- Read and follow /Users/aeid/git_tree/kanban/skills/agent-control-plane-api/SKILL.md
- Prefer board writes through MCP/API tools exposed by that skill
- Keep task status + comments synchronized on each major step`}</pre>
              </div>
              <div className="rounded border border-[color:var(--border)] bg-[color:var(--panel)] p-4">
                <div className="text-sm font-medium">Aider</div>
                <pre className="mt-2 overflow-auto rounded bg-zinc-950 p-3 text-xs text-zinc-100">{`# Add to your Aider instructions file:
- Follow the ACP skill contract at /Users/aeid/git_tree/kanban/skills/agent-control-plane-api/SKILL.md
- Start work by reading current board tasks
- Post progress comments to the linked task after code edits`}</pre>
              </div>
              <div className="rounded border border-[color:var(--border)] bg-[color:var(--panel)] p-4 text-sm">
                <div className="font-medium">Generic Agent With Prompt/Memory Support</div>
                <div className="mt-2 text-[color:var(--text-muted)]">
                  Add this instruction to your agent profile: "Always follow
                  <span className="font-mono"> /Users/aeid/git_tree/kanban/skills/agent-control-plane-api/SKILL.md</span>
                  , use board tools first, and keep tasks/comments updated while implementing."
                </div>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="page-frame p-4">
        <div className="project-workspace">
          <aside className="project-switcher">
            <div className="flex items-center justify-between gap-2">
              <div className="text-sm font-medium text-[color:var(--text)]">Projects</div>
              <button
                type="button"
                className="btn-ghost btn-dashed"
                onClick={() => setProjectDialogOpen(true)}
              >
                + New Project
              </button>
            </div>
            <div className="mt-3 space-y-1">
              {filteredProjects.map((project) => (
                <button
                  key={project.id}
                  type="button"
                  onClick={() => setSelectedProjectId(project.id)}
                  className={[
                    "flex h-9 w-full items-center justify-between gap-2 rounded px-3 text-left text-sm",
                    selectedProjectId === project.id
                      ? "bg-[rgba(37,99,235,0.08)] text-[color:var(--accent)]"
                      : "text-[color:var(--text)] hover:bg-black/4",
                  ].join(" ")}
                >
                  <div className="flex min-w-0 items-center gap-2">
                    <StatusDot status={selectedProjectId === project.id ? WorkflowState.IN_PROGRESS : WorkflowState.BACKLOG} />
                    <span className="truncate">{project.name}</span>
                  </div>
                </button>
              ))}
            </div>
          </aside>

          <div className="board-region">
            <h2 className="text-lg font-semibold">{projectDetailQuery.data?.project.name ?? "Projects"}</h2>
            <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
              <div className="board-scroll mt-4 scrollbar-thin">
                {(projectDetailQuery.data?.board.columns ?? []).map((column) => (
                  <DroppableBoardColumn key={column.id} columnId={column.id}>
                    <div className="flex flex-col gap-3 rounded border border-[color:var(--border)] bg-[color:var(--surface)] p-3">
                      <BoardColumnHeader
                        title={column.name}
                        status={column.key}
                        count={groupedTasks.get(column.id)?.length ?? 0}
                        wipLimit={column.wip_limit}
                      />
                      <div className="space-y-2">
                        {(groupedTasks.get(column.id) ?? []).map((task) => (
                          <DraggableTaskCard
                            key={task.id}
                            task={task as never}
                            subtasks={[]}
                            selected={inspectedTaskId === task.id}
                            metadata={{ sessions: 0, worktree: false, checks: 0, artifacts: 0, assignees: [] }}
                            onInspect={() => {
                              setInspectedTaskId(task.id);
                              setMobileTaskPanelOpen(true);
                            }}
                          />
                        ))}
                      </div>
                      <div className="space-y-2">
                        <input
                          value={draftTaskTitle}
                          onChange={(event) => setDraftTaskTitle(event.target.value)}
                          placeholder="Add task title"
                          className="w-full rounded-[4px] border border-[color:var(--border)] px-3 py-2 text-sm"
                        />
                        <button
                          type="button"
                          className="btn-ghost btn-dashed w-full justify-start"
                          onClick={() =>
                            selectedProjectId
                              ? createTaskMutation.mutate({
                                  project_id: selectedProjectId,
                                  title: draftTaskTitle,
                                  board_column_key: column.key,
                                  source: "web",
                                })
                              : null
                          }
                          disabled={!selectedProjectId || !draftTaskTitle.trim() || createTaskMutation.isPending}
                        >
                          + Add task
                        </button>
                      </div>
                    </div>
                  </DroppableBoardColumn>
                ))}
              </div>
            </DndContext>
          </div>
        </div>
      </div>
    );
  })();

  return (
    <AppShell
      sidebar={<SidebarNavigation activeSection={activeSection} setActiveSection={setActiveSection} />}
      header={<AppHeader breadcrumbs={breadcrumbs} search={search} setSearch={setSearch} onSearchActivate={() => setActiveSection("search")} />}
      main={
        <>
          {mainContent}
          <DialogFrame open={projectDialogOpen} onOpenChange={setProjectDialogOpen} title="New Project">
            <ProjectBootstrapWizard
              isPending={createProjectMutation.isPending}
              errorMessage={createProjectMutation.error instanceof Error ? createProjectMutation.error.message : undefined}
              onCreate={async (payload) => {
                await createProjectMutation.mutateAsync(payload);
              }}
            />
          </DialogFrame>
        </>
      }
      drawer={
        taskDetailQuery.data ? (
          <>
            <div className="detail-panel max-lg:hidden">
              <TaskDetailScreen
                title={
                  <div className="flex items-center justify-between gap-3">
                    <button
                      type="button"
                      className="btn-ghost !px-0"
                      onClick={() => setInspectedTaskId(null)}
                    >
                      <X className="h-4 w-4" />
                      Back to board
                    </button>
                    <button type="button" className="btn-ghost" aria-label="Task actions">
                      <MoreHorizontal className="h-4 w-4" />
                    </button>
                  </div>
                }
                actions={<div className="text-sm font-medium">{taskDetailQuery.data.title}</div>}
                contextPanel={
                  <div className="space-y-4">
                    <textarea
                      value={taskDetailQuery.data.description ?? ""}
                      onChange={(event) =>
                        patchDescriptionMutation.mutate({ taskId: taskDetailQuery.data.id, description: event.target.value })
                      }
                      className="min-h-24 w-full rounded border border-[color:var(--border)] p-2"
                    />
                    <div>
                      <div className="mb-2 text-sm font-medium">Comments</div>
                      <div className="space-y-2">
                        {taskDetailQuery.data.comments.map((comment) => (
                          <div key={comment.id} className="rounded border border-[color:var(--border)] p-2">
                            <div className="text-xs text-[color:var(--text-muted)]">
                              {comment.author_name} · {comment.source ?? "ui"}
                            </div>
                            <div className="text-sm">{comment.body}</div>
                          </div>
                        ))}
                      </div>
                      <textarea
                        value={draftCommentBody}
                        onChange={(event) => setDraftCommentBody(event.target.value)}
                        placeholder="Leave progress comment"
                        className="mt-2 min-h-20 w-full rounded border border-[color:var(--border)] p-2"
                      />
                      <Button
                        variant="primary"
                        onClick={() => addCommentMutation.mutate({ taskId: taskDetailQuery.data.id, body: draftCommentBody })}
                        disabled={!draftCommentBody.trim() || addCommentMutation.isPending}
                      >
                        Post comment
                      </Button>
                    </div>
                  </div>
                }
                sections={[]}
              />
            </div>
            <Drawer.Root open={mobileTaskPanelOpen} onOpenChange={setMobileTaskPanelOpen}>
              <Drawer.Portal>
                <Drawer.Overlay className="fixed inset-0 z-[70] bg-black/20 lg:hidden" />
                <Drawer.Content className="fixed bottom-0 left-0 right-0 z-[80] h-[85vh] rounded-t-[8px] border border-[color:var(--border)] bg-[color:var(--surface)] lg:hidden">
                  <div className="h-full overflow-auto p-4">
                    <div className="mb-3 text-base font-semibold">{taskDetailQuery.data.title}</div>
                    <div className="text-sm text-[color:var(--text-muted)]">
                      {taskDetailQuery.data.description ?? "No task description yet."}
                    </div>
                  </div>
                </Drawer.Content>
              </Drawer.Portal>
            </Drawer.Root>
          </>
        ) : null
      }
    />
  );
}
