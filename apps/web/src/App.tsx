import {
  useDeferredValue,
  useEffect,
  useMemo,
  useState,
  startTransition,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  DndContext,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  Activity,
  Bot,
  ChevronRight,
  FolderGit2,
  GitBranch,
  GitFork,
  Home,
  Lock,
  MessageSquareText,
  Plus,
  Play,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Terminal,
  Trash2,
} from "lucide-react";
import type { TaskSummary } from "@acp/sdk";
import { ProjectBootstrapWizard } from "@/components/project-bootstrap-wizard";
import {
  ColumnShell,
  Pill,
  SectionFrame,
  SectionTitle,
  StatTile,
} from "@/components/ui";
import { useUIStore } from "@/store/ui";
import { AppShell } from "@/layout/AppShell";
import { DashboardScreen } from "@/screens/DashboardScreen";
import {
  DraggableTaskCard,
  DroppableBoardColumn,
  ProjectBoardScreen,
} from "@/screens/ProjectBoardScreen";
import { TaskDetailScreen } from "@/screens/TaskDetailScreen";
import { SessionDetailScreen } from "@/screens/SessionDetailScreen";
import { WaitingInboxScreen } from "@/screens/WaitingInboxScreen";
import { WorktreeInventoryScreen } from "@/screens/WorktreeInventoryScreen";
import { ActivityScreen } from "@/screens/ActivityScreen";
import { DiagnosticsScreen } from "@/screens/DiagnosticsScreen";
import { ProjectOverviewScreen } from "@/screens/ProjectOverviewScreen";
import {
  useAddTaskArtifactMutation,
  useAddTaskCheckMutation,
  useAddTaskCommentMutation,
  useAddTaskDependencyMutation,
  useAnswerQuestionMutation,
  useBootstrapProjectMutation,
  useCancelSessionMutation,
  useCreateFollowUpSessionMutation,
  useCreateQuestionMutation,
  useCreateRepositoryMutation,
  useCreateSessionMutation,
  useCreateTaskMutation,
  useCreateWorktreeMutation,
  useDashboardQuery,
  useDiagnosticsQuery,
  useEventsQuery,
  useLiveInvalidationSocket,
  usePatchTaskMutation,
  usePatchWorktreeMutation,
  useProjectDetailQuery,
  useProjectsQuery,
  useQuestionDetailQuery,
  useSearchQuery,
  useSessionTailQuery,
  useSessionTimelineQuery,
  useTaskDetailQuery,
} from "@/features/control-plane/hooks";

function formatEvent(eventType: string) {
  return eventType.replaceAll(".", " ").replaceAll("_", " ");
}

function getSessionRelationLabel(
  session: {
    id: string;
    profile: string;
    runtime_metadata: Record<string, unknown>;
  },
  selectedSessionId: string | null,
) {
  if (session.id === selectedSessionId) {
    return "selected";
  }

  const followUpType = session.runtime_metadata.follow_up_type;
  if (typeof followUpType === "string" && followUpType.length > 0) {
    return followUpType;
  }

  return "origin";
}

type NavSection =
  | "home"
  | "projects"
  | "waiting"
  | "sessions"
  | "worktrees"
  | "search"
  | "activity"
  | "diagnostics";

export function App() {
  const queryClient = useQueryClient();
  const { selectedProjectId, setSelectedProjectId } = useUIStore();
  const [search, setSearch] = useState("");
  const [draftTaskTitle, setDraftTaskTitle] = useState("");
  const [draftRepoPath, setDraftRepoPath] = useState("");
  const [draftRepoName, setDraftRepoName] = useState("");
  const [draftWorktreeLabel, setDraftWorktreeLabel] = useState("");
  const [selectedRepositoryId, setSelectedRepositoryId] = useState<
    string | null
  >(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string>("");
  const [selectedSessionTaskId, setSelectedSessionTaskId] =
    useState<string>("");
  const [selectedSessionWorktreeId, setSelectedSessionWorktreeId] =
    useState<string>("");
  const [sessionProfile, setSessionProfile] = useState("executor");
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(
    null,
  );
  const [selectedQuestionId, setSelectedQuestionId] = useState<string | null>(
    null,
  );
  const [inspectedTaskId, setInspectedTaskId] = useState<string | null>(null);
  const [draftQuestionPrompt, setDraftQuestionPrompt] = useState("");
  const [draftQuestionReason, setDraftQuestionReason] = useState("");
  const [draftQuestionUrgency, setDraftQuestionUrgency] = useState("medium");
  const [draftReplyBody, setDraftReplyBody] = useState("");
  const [draftCommentBody, setDraftCommentBody] = useState("");
  const [draftCheckSummary, setDraftCheckSummary] = useState("");
  const [draftCheckType, setDraftCheckType] = useState("verification");
  const [draftCheckStatus, setDraftCheckStatus] = useState("passed");
  const [draftArtifactName, setDraftArtifactName] = useState("");
  const [draftArtifactType, setDraftArtifactType] = useState("log");
  const [draftArtifactUri, setDraftArtifactUri] = useState("");
  const [selectedDependencyTaskId, setSelectedDependencyTaskId] = useState("");
  const [draftSubtaskTitle, setDraftSubtaskTitle] = useState("");
  const [activeSection, setActiveSection] = useState<NavSection>("home");
  const deferredSearch = useDeferredValue(search);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
  );

  const dashboardQuery = useDashboardQuery();
  const diagnosticsQuery = useDiagnosticsQuery();
  const eventsQuery = useEventsQuery(selectedProjectId);
  const projectsQuery = useProjectsQuery();
  const searchQuery = useSearchQuery(deferredSearch, selectedProjectId);

  useEffect(() => {
    if (!selectedProjectId && projectsQuery.data?.[0]) {
      setSelectedProjectId(projectsQuery.data[0].id);
    }
  }, [projectsQuery.data, selectedProjectId, setSelectedProjectId]);

  useLiveInvalidationSocket(() => {
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    queryClient.invalidateQueries({ queryKey: ["diagnostics"] });
    queryClient.invalidateQueries({ queryKey: ["projects"] });
    queryClient.invalidateQueries({ queryKey: ["project"] });
    queryClient.invalidateQueries({ queryKey: ["task-detail"] });
    queryClient.invalidateQueries({ queryKey: ["question"] });
    queryClient.invalidateQueries({ queryKey: ["session-tail"] });
    queryClient.invalidateQueries({ queryKey: ["session-timeline"] });
    queryClient.invalidateQueries({ queryKey: ["events"] });
  });

  const projectDetailQuery = useProjectDetailQuery(selectedProjectId);

  useEffect(() => {
    setSelectedRepositoryId(null);
    setSelectedTaskId("");
    setSelectedSessionTaskId("");
    setSelectedSessionWorktreeId("");
    setSelectedSessionId(null);
    setSelectedQuestionId(null);
    setInspectedTaskId(null);
  }, [selectedProjectId]);

  useEffect(() => {
    const repositories = projectDetailQuery.data?.repositories ?? [];
    if (!selectedRepositoryId && repositories[0]) {
      setSelectedRepositoryId(repositories[0].id);
    }
  }, [projectDetailQuery.data?.repositories, selectedRepositoryId]);

  useEffect(() => {
    const questions = projectDetailQuery.data?.waiting_questions ?? [];
    if (!selectedQuestionId && questions[0]) {
      setSelectedQuestionId(questions[0].id);
    }
  }, [projectDetailQuery.data?.waiting_questions, selectedQuestionId]);

  const bootstrapProjectMutation = useBootstrapProjectMutation({
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({
        queryKey: ["project", result.project.id],
      });
      startTransition(() => {
        setSelectedProjectId(result.project.id);
      });
    },
  });

  useEffect(() => {
    const result = bootstrapProjectMutation.data;
    if (!result || result.project.id !== selectedProjectId) {
      return;
    }
    setSelectedRepositoryId(result.repository.id);
    setInspectedTaskId(result.kickoff_task.id);
    setSelectedSessionId(result.kickoff_session.id);
  }, [bootstrapProjectMutation.data, selectedProjectId]);

  const createTaskMutation = useCreateTaskMutation({
    onSuccess: () => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({
          queryKey: ["project", selectedProjectId],
        });
      }
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      setDraftTaskTitle("");
    },
  });

  const createSubtaskMutation = useCreateTaskMutation({
    onSuccess: () => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({
          queryKey: ["project", selectedProjectId],
        });
      }
      if (inspectedTaskId) {
        queryClient.invalidateQueries({
          queryKey: ["task-detail", inspectedTaskId],
        });
      }
      setDraftSubtaskTitle("");
    },
  });

  const patchTaskMutation = usePatchTaskMutation({
    onSuccess: () => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({
          queryKey: ["project", selectedProjectId],
        });
      }
      if (inspectedTaskId) {
        queryClient.invalidateQueries({
          queryKey: ["task-detail", inspectedTaskId],
        });
      }
    },
  });

  const createRepositoryMutation = useCreateRepositoryMutation({
    onSuccess: (repository) => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({
          queryKey: ["project", selectedProjectId],
        });
      }
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      setSelectedRepositoryId(repository.id);
      setDraftRepoPath("");
      setDraftRepoName("");
    },
  });

  const createWorktreeMutation = useCreateWorktreeMutation({
    onSuccess: () => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({
          queryKey: ["project", selectedProjectId],
        });
      }
      setDraftWorktreeLabel("");
      setSelectedTaskId("");
    },
  });

  const patchWorktreeMutation = usePatchWorktreeMutation({
    onSuccess: () => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({
          queryKey: ["project", selectedProjectId],
        });
      }
    },
  });

  const createSessionMutation = useCreateSessionMutation({
    onSuccess: (session) => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({
          queryKey: ["project", selectedProjectId],
        });
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      }
      setSelectedSessionId(session.id);
    },
  });

  const createFollowUpSessionMutation = useCreateFollowUpSessionMutation({
    onSuccess: (session) => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({
          queryKey: ["project", selectedProjectId],
        });
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      }
      queryClient.invalidateQueries({ queryKey: ["session-tail"] });
      queryClient.invalidateQueries({ queryKey: ["session-timeline"] });
      setSelectedSessionId(session.id);
    },
  });

  const createQuestionMutation = useCreateQuestionMutation({
    onSuccess: (question) => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({
          queryKey: ["project", selectedProjectId],
        });
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      }
      setSelectedQuestionId(question.id);
      setDraftQuestionPrompt("");
      setDraftQuestionReason("");
    },
  });

  const answerQuestionMutation = useAnswerQuestionMutation({
    onSuccess: (detail) => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({
          queryKey: ["project", selectedProjectId],
        });
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      }
      queryClient.invalidateQueries({ queryKey: ["question", detail.id] });
      setDraftReplyBody("");
    },
  });

  const addTaskCommentMutation = useAddTaskCommentMutation({
    onSuccess: () => {
      if (inspectedTaskId) {
        queryClient.invalidateQueries({
          queryKey: ["task-detail", inspectedTaskId],
        });
      }
      setDraftCommentBody("");
    },
  });

  const addTaskCheckMutation = useAddTaskCheckMutation({
    onSuccess: () => {
      if (inspectedTaskId) {
        queryClient.invalidateQueries({
          queryKey: ["task-detail", inspectedTaskId],
        });
      }
      setDraftCheckSummary("");
    },
  });

  const addTaskArtifactMutation = useAddTaskArtifactMutation({
    onSuccess: () => {
      if (inspectedTaskId) {
        queryClient.invalidateQueries({
          queryKey: ["task-detail", inspectedTaskId],
        });
      }
      setDraftArtifactName("");
      setDraftArtifactUri("");
    },
  });

  const addTaskDependencyMutation = useAddTaskDependencyMutation({
    onSuccess: () => {
      if (inspectedTaskId) {
        queryClient.invalidateQueries({
          queryKey: ["task-detail", inspectedTaskId],
        });
      }
      setSelectedDependencyTaskId("");
    },
  });

  const cancelSessionMutation = useCancelSessionMutation({
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["project"] });
      queryClient.invalidateQueries({ queryKey: ["session-tail"] });
      queryClient.invalidateQueries({ queryKey: ["session-timeline"] });
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
      if (task.parent_task_id) {
        return;
      }
      const entry = map.get(task.board_column_id);
      if (entry) {
        entry.push(task);
      }
    });
    return map;
  }, [projectDetailQuery.data]);

  const topLevelTasks = useMemo(() => {
    return (projectDetailQuery.data?.board.tasks ?? []).filter(
      (task) => !task.parent_task_id,
    );
  }, [projectDetailQuery.data]);

  const subtasksByParent = useMemo(() => {
    const map = new Map<string, TaskSummary[]>();
    for (const task of projectDetailQuery.data?.board.tasks ?? []) {
      if (!task.parent_task_id) {
        continue;
      }
      const entry = map.get(task.parent_task_id) ?? [];
      entry.push(task);
      map.set(task.parent_task_id, entry);
    }
    return map;
  }, [projectDetailQuery.data]);

  const taskCardMetadata = useMemo(() => {
    const sessionsByTask = new Map<string, number>();
    for (const session of projectDetailQuery.data?.sessions ?? []) {
      sessionsByTask.set(
        session.task_id,
        (sessionsByTask.get(session.task_id) ?? 0) + 1,
      );
    }

    const worktreeByTask = new Set<string>();
    for (const worktree of projectDetailQuery.data?.worktrees ?? []) {
      if (worktree.task_id) {
        worktreeByTask.add(worktree.task_id);
      }
    }

    return { sessionsByTask, worktreeByTask };
  }, [projectDetailQuery.data?.sessions, projectDetailQuery.data?.worktrees]);

  const staleWorktreesById = useMemo(() => {
    const map = new Map<
      string,
      { recommendation: string; reasons: string[] }
    >();
    for (const issue of diagnosticsQuery.data?.stale_worktrees ?? []) {
      map.set(issue.worktree_id, {
        recommendation: issue.recommendation,
        reasons: issue.reasons,
      });
    }
    return map;
  }, [diagnosticsQuery.data]);

  const sessionTailQuery = useSessionTailQuery(selectedSessionId);
  const sessionTimelineQuery = useSessionTimelineQuery(selectedSessionId);

  const questionDetailQuery = useQuestionDetailQuery(selectedQuestionId);

  const taskDetailQuery = useTaskDetailQuery(inspectedTaskId);
  const selectedSession = useMemo(
    () =>
      projectDetailQuery.data?.sessions.find(
        (session) => session.id === selectedSessionId,
      ) ?? null,
    [projectDetailQuery.data?.sessions, selectedSessionId],
  );
  const selectedSessionTaskDetailQuery = useTaskDetailQuery(
    selectedSession?.task_id ?? null,
  );

  const navItems: Array<{ key: NavSection; label: string; icon: typeof Home }> =
    [
      { key: "home", label: "Home", icon: Home },
      { key: "projects", label: "Projects", icon: FolderGit2 },
      { key: "waiting", label: "Waiting Inbox", icon: MessageSquareText },
      { key: "sessions", label: "Sessions", icon: Terminal },
      { key: "worktrees", label: "Worktrees", icon: GitBranch },
      { key: "search", label: "Search", icon: Search },
      { key: "activity", label: "Activity", icon: Activity },
      { key: "diagnostics", label: "Diagnostics/Settings", icon: ShieldCheck },
    ];

  const sectionTitle = {
    home: "Home",
    projects: "Projects",
    waiting: "Waiting Inbox",
    sessions: "Sessions",
    worktrees: "Worktrees",
    search: "Search",
    activity: "Activity",
    diagnostics: "Diagnostics & Settings",
  }[activeSection];

  const breadcrumbs = [
    sectionTitle,
    projectDetailQuery.data?.project.name,
    taskDetailQuery.data?.title,
    sessionTimelineQuery.data?.session.session_name,
  ].filter(Boolean) as string[];

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || !projectDetailQuery.data) {
      return;
    }

    const taskId = String(active.id);
    const boardColumnId = String(over.id);
    const task = projectDetailQuery.data.board.tasks.find(
      (candidate) => candidate.id === taskId,
    );
    const column = projectDetailQuery.data.board.columns.find(
      (candidate) => candidate.id === boardColumnId,
    );
    if (
      !task ||
      !column ||
      task.board_column_id === column.id ||
      task.parent_task_id
    ) {
      return;
    }

    patchTaskMutation.mutate({ taskId, boardColumnId: column.id });
  };

  return (
    <AppShell
      sidebar={
        <>
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-slate-500">
                Agent Control Plane
              </p>
              <h1 className="mt-3 text-2xl font-semibold tracking-tight">
                Local operator workspace
              </h1>
            </div>
            <Pill className="border-emerald-400/20 bg-emerald-400/10 text-emerald-200">
              v0.1
            </Pill>
          </div>

          <div className="mt-8">
            <SectionTitle>Navigation</SectionTitle>
            <div className="mt-3 flex flex-col gap-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.key}
                    onClick={() => setActiveSection(item.key)}
                    className={[
                      "flex items-center gap-3 rounded-2xl border px-4 py-3 text-left text-sm transition",
                      activeSection === item.key
                        ? "border-[color:var(--color-accent-primary)] bg-[color:var(--color-accent-soft)] text-slate-100"
                        : "border-white/7 bg-white/2 text-slate-400 hover:bg-white/5",
                    ].join(" ")}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="mt-8">
            <SectionTitle>Projects</SectionTitle>
            <div className="mt-3 flex flex-col gap-2">
              {filteredProjects.slice(0, 6).map((project) => (
                <button
                  key={project.id}
                  onClick={() => {
                    setSelectedProjectId(project.id);
                    setActiveSection("projects");
                  }}
                  className={[
                    "rounded-2xl border px-3 py-3 text-left text-sm",
                    selectedProjectId === project.id
                      ? "border-[color:var(--color-accent-primary)] bg-[color:var(--color-accent-soft)]"
                      : "border-white/7 bg-white/2",
                  ].join(" ")}
                >
                  <div className="font-semibold text-slate-100">
                    {project.name}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <ProjectBootstrapWizard
            isPending={bootstrapProjectMutation.isPending}
            errorMessage={
              bootstrapProjectMutation.error instanceof Error
                ? bootstrapProjectMutation.error.message
                : undefined
            }
            result={bootstrapProjectMutation.data}
            onSubmit={(payload) => bootstrapProjectMutation.mutate(payload)}
          />
        </>
      }
      header={
        <>
          <section className="surface rounded-[28px] px-5 py-4">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-slate-500">
                  {breadcrumbs.map((crumb, index) => (
                    <span
                      key={crumb}
                      className="inline-flex items-center gap-2"
                    >
                      {index ? <ChevronRight className="h-3 w-3" /> : null}
                      {crumb}
                    </span>
                  ))}
                </div>
                <h2 className="mt-2 text-2xl font-semibold text-slate-100">
                  {sectionTitle}
                </h2>
              </div>
              <div className="flex items-center gap-2">
                <label className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/15 px-3 py-2 text-sm text-slate-400">
                  <Search className="h-4 w-4" />
                  <input
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    className="w-52 border-0 bg-transparent p-0 text-sm outline-none placeholder:text-slate-600"
                    placeholder="Global search"
                  />
                </label>
                <button
                  onClick={() => setActiveSection("projects")}
                  className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900"
                >
                  <Plus className="h-4 w-4" />
                  Quick create
                </button>
                <button className="inline-flex items-center gap-2 rounded-full border border-white/10 px-4 py-2 text-sm text-slate-300">
                  <SlidersHorizontal className="h-4 w-4" />
                  View controls
                </button>
              </div>
            </div>
          </section>
          {activeSection === "home" ? (
            <DashboardScreen>
              <section className="surface rounded-[32px] px-6 py-6">
                <div className="flex flex-wrap items-end justify-between gap-6">
                  <div>
                    <p className="text-xs uppercase tracking-[0.28em] text-slate-500">
                      Operational overview
                    </p>
                    <h2 className="mt-3 text-4xl font-semibold tracking-tight">
                      Observe, steer, resume.
                    </h2>
                    <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
                      The control plane keeps project state, board flow, runtime
                      context, and future agent sessions in one local-first
                      workspace.
                    </p>
                  </div>
                  <div className="flex items-center gap-3 text-sm text-slate-400">
                    <Activity className="h-4 w-4 text-[color:var(--color-accent-primary)]" />
                    {diagnosticsQuery.data?.environment ?? "development"}{" "}
                    environment
                  </div>
                </div>

                <div className="mt-8 grid gap-4 md:grid-cols-4">
                  <StatTile
                    label="Projects"
                    value={dashboardQuery.data?.projects.length ?? 0}
                  />
                  <StatTile
                    label="Waiting"
                    value={dashboardQuery.data?.waiting_count ?? 0}
                  />
                  <StatTile
                    label="Blocked"
                    value={dashboardQuery.data?.blocked_count ?? 0}
                  />
                  <StatTile
                    label="Running Sessions"
                    value={dashboardQuery.data?.running_sessions ?? 0}
                  />
                </div>

                <div className="mt-8 grid gap-4 xl:grid-cols-3">
                  <div className="rounded-[28px] border border-white/8 bg-black/10 p-5">
                    <SectionTitle>Waiting Across Projects</SectionTitle>
                    <div className="mt-4 flex flex-col gap-3">
                      {dashboardQuery.data?.waiting_questions.map(
                        (question) => (
                          <button
                            key={question.id}
                            onClick={() => {
                              setSelectedProjectId(question.project_id);
                              setSelectedQuestionId(question.id);
                            }}
                            className="rounded-2xl border border-white/7 bg-white/3 px-4 py-3 text-left"
                          >
                            <div className="text-sm font-semibold text-slate-100">
                              {question.prompt}
                            </div>
                            <div className="mt-1 text-xs text-slate-500">
                              {question.urgency ?? "open"} ·{" "}
                              {question.project_id.slice(0, 8)}
                            </div>
                          </button>
                        ),
                      )}
                      {!dashboardQuery.data?.waiting_questions.length ? (
                        <div className="text-sm text-slate-500">
                          No open waiting questions across projects.
                        </div>
                      ) : null}
                    </div>
                  </div>

                  <div className="rounded-[28px] border border-white/8 bg-black/10 p-5">
                    <SectionTitle>Blocked Tasks</SectionTitle>
                    <div className="mt-4 flex flex-col gap-3">
                      {dashboardQuery.data?.blocked_tasks.map((task) => (
                        <button
                          key={task.id}
                          onClick={() => {
                            setSelectedProjectId(task.project_id);
                            setInspectedTaskId(task.id);
                          }}
                          className="rounded-2xl border border-white/7 bg-white/3 px-4 py-3 text-left"
                        >
                          <div className="text-sm font-semibold text-slate-100">
                            {task.title}
                          </div>
                          <div className="mt-1 text-xs text-slate-500">
                            {task.blocked_reason ?? "Blocked"}
                          </div>
                        </button>
                      ))}
                      {!dashboardQuery.data?.blocked_tasks.length ? (
                        <div className="text-sm text-slate-500">
                          No blocked tasks right now.
                        </div>
                      ) : null}
                    </div>
                  </div>

                  <div className="rounded-[28px] border border-white/8 bg-black/10 p-5">
                    <SectionTitle>Running Sessions</SectionTitle>
                    <div className="mt-4 flex flex-col gap-3">
                      {dashboardQuery.data?.active_sessions.map((session) => (
                        <button
                          key={session.id}
                          onClick={() => {
                            setSelectedProjectId(session.project_id);
                            setSelectedSessionId(session.id);
                          }}
                          className="rounded-2xl border border-white/7 bg-white/3 px-4 py-3 text-left"
                        >
                          <div className="text-sm font-semibold text-slate-100">
                            {session.profile}
                          </div>
                          <div className="mt-1 text-xs text-slate-500">
                            {session.session_name}
                          </div>
                        </button>
                      ))}
                      {!dashboardQuery.data?.active_sessions.length ? (
                        <div className="text-sm text-slate-500">
                          No running sessions right now.
                        </div>
                      ) : null}
                    </div>
                  </div>
                </div>

                <div className="mt-8 rounded-[28px] border border-white/8 bg-black/10 p-5">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <SectionTitle>Activity Feed</SectionTitle>
                      <div className="mt-2 text-sm text-slate-500">
                        Recent audit events for{" "}
                        {projectDetailQuery.data?.project.name ??
                          "the control plane"}
                        .
                      </div>
                    </div>
                    <Pill className="border-white/8 text-slate-300">
                      {eventsQuery.data?.length ?? 0} visible
                    </Pill>
                  </div>
                  <div className="mt-4 grid gap-3 lg:grid-cols-2">
                    {(eventsQuery.data ?? []).map((event) => (
                      <div
                        key={event.id}
                        className="rounded-2xl border border-white/7 bg-white/3 px-4 py-4"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <div className="text-sm font-semibold text-slate-100">
                            {formatEvent(event.event_type)}
                          </div>
                          <Pill className="border-white/8 text-slate-300">
                            {event.entity_type}
                          </Pill>
                        </div>
                        <div className="mt-2 text-sm text-slate-400">
                          {event.actor_name} updated {event.entity_type}{" "}
                          {event.entity_id.slice(0, 8)}
                        </div>
                        <div className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-600">
                          {new Date(event.created_at).toLocaleString()}
                        </div>
                      </div>
                    ))}
                    {!eventsQuery.data?.length ? (
                      <div className="text-sm text-slate-500">
                        No events recorded yet for this scope.
                      </div>
                    ) : null}
                  </div>
                </div>
              </section>
            </DashboardScreen>
          ) : null}
        </>
      }
      main={
        <>
          {activeSection === "search" ? (
            <SectionFrame className="px-5 py-5">
              <SectionTitle>Search Results</SectionTitle>
              <div className="mt-4 flex flex-col gap-3">
                {deferredSearch.trim().length < 2 ? (
                  <div className="text-sm text-slate-500">
                    Type at least two characters to search tasks, questions,
                    sessions, and events.
                  </div>
                ) : null}
                {searchQuery.data?.hits.map((hit) => (
                  <button
                    key={`${hit.entity_type}-${hit.entity_id}`}
                    onClick={() => {
                      if (hit.entity_type === "task") {
                        setInspectedTaskId(hit.entity_id);
                      } else if (hit.entity_type === "waiting_question") {
                        setSelectedQuestionId(hit.entity_id);
                      } else if (hit.entity_type === "session") {
                        setSelectedSessionId(hit.entity_id);
                      }
                      if (hit.project_id) {
                        setSelectedProjectId(hit.project_id);
                      }
                    }}
                    className="rounded-2xl border border-white/7 bg-white/3 px-4 py-3 text-left"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-semibold text-slate-100">
                        {hit.title}
                      </div>
                      <Pill className="border-white/8 text-slate-300">
                        {hit.entity_type}
                      </Pill>
                    </div>
                    <div className="mt-2 line-clamp-2 text-sm text-slate-500">
                      {hit.snippet}
                    </div>
                  </button>
                ))}
              </div>
            </SectionFrame>
          ) : null}
          {activeSection !== "home" && activeSection !== "search" ? (
            <ProjectOverviewScreen>
              <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
                <ProjectBoardScreen>
                  {activeSection === "projects" ? (
                    <SectionFrame className="px-5 py-5">
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <SectionTitle>Project Board</SectionTitle>
                          <h3 className="mt-2 text-2xl font-semibold">
                            {projectDetailQuery.data?.project.name ??
                              "Select or create a project"}
                          </h3>
                        </div>
                        {selectedProjectId ? (
                          <div className="flex items-center gap-3">
                            <input
                              value={draftTaskTitle}
                              onChange={(event) =>
                                setDraftTaskTitle(event.target.value)
                              }
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
                              disabled={
                                !draftTaskTitle.trim() ||
                                createTaskMutation.isPending
                              }
                              className="rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                              New task
                            </button>
                          </div>
                        ) : null}
                      </div>

                      <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
                        <div className="mt-6 flex gap-6 overflow-x-auto pb-2 scrollbar-thin">
                          {projectDetailQuery.data?.board.columns.map(
                            (column) => (
                              <DroppableBoardColumn
                                key={column.id}
                                columnId={column.id}
                              >
                                <ColumnShell className="flex flex-col gap-4">
                                  <div className="flex items-center justify-between gap-4">
                                    <div>
                                      <div className="text-sm font-semibold">
                                        {column.name}
                                      </div>
                                      <div className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-500">
                                        {column.key}
                                      </div>
                                    </div>
                                    <Pill className="border-white/8 text-slate-300">
                                      {groupedTasks.get(column.id)?.length ?? 0}
                                      {column.wip_limit
                                        ? ` / ${column.wip_limit}`
                                        : ""}
                                    </Pill>
                                  </div>

                                  <div className="space-y-3">
                                    {(groupedTasks.get(column.id) ?? []).map(
                                      (task) => (
                                        <DraggableTaskCard
                                          key={task.id}
                                          task={task}
                                          subtasks={
                                            subtasksByParent.get(task.id) ?? []
                                          }
                                          selected={inspectedTaskId === task.id}
                                          metadata={{
                                            sessions:
                                              taskCardMetadata.sessionsByTask.get(
                                                task.id,
                                              ) ?? 0,
                                            worktree:
                                              taskCardMetadata.worktreeByTask.has(
                                                task.id,
                                              ),
                                            checks:
                                              inspectedTaskId === task.id
                                                ? (taskDetailQuery.data?.checks
                                                    .length ?? 0)
                                                : 0,
                                            artifacts:
                                              inspectedTaskId === task.id
                                                ? (taskDetailQuery.data
                                                    ?.artifacts.length ?? 0)
                                                : 0,
                                          }}
                                          onInspect={() =>
                                            setInspectedTaskId(task.id)
                                          }
                                        />
                                      ),
                                    )}
                                    {!groupedTasks.get(column.id)?.length ? (
                                      <div className="rounded-2xl border border-dashed border-white/8 px-4 py-6 text-sm text-slate-500">
                                        No tasks in this column yet.
                                      </div>
                                    ) : null}
                                  </div>
                                </ColumnShell>
                              </DroppableBoardColumn>
                            ),
                          )}
                        </div>
                      </DndContext>
                    </SectionFrame>
                  ) : null}
                </ProjectBoardScreen>

                <div className="flex flex-col gap-6">
                  {activeSection === "projects" ? (
                    taskDetailQuery.data ? (
                      <TaskDetailScreen
                        quickInspect
                        title={taskDetailQuery.data.title}
                        state={taskDetailQuery.data.workflow_state}
                        priority={taskDetailQuery.data.priority}
                        description={
                          taskDetailQuery.data.description ??
                          "No task description yet."
                        }
                        contextPanel={
                          <div className="grid gap-3 sm:grid-cols-2 text-sm">
                            <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-2">
                              <div className="text-xs text-slate-500">
                                Owner
                              </div>
                              <div className="mt-1 text-slate-200">
                                Operator-managed
                              </div>
                            </div>
                            <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-2">
                              <div className="text-xs text-slate-500">
                                Session
                              </div>
                              <div className="mt-1 text-slate-200">
                                {projectDetailQuery.data?.sessions.find(
                                  (session) =>
                                    session.task_id === taskDetailQuery.data.id,
                                )?.session_name ?? "Unlinked"}
                              </div>
                            </div>
                            <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-2">
                              <div className="text-xs text-slate-500">
                                Worktree
                              </div>
                              <div className="mt-1 text-slate-200">
                                {projectDetailQuery.data?.worktrees.find(
                                  (worktree) =>
                                    worktree.task_id ===
                                    taskDetailQuery.data.id,
                                )?.branch_name ?? "Unlinked"}
                              </div>
                            </div>
                            <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-2">
                              <div className="text-xs text-slate-500">
                                Dependencies
                              </div>
                              <div className="mt-1 text-slate-200">
                                {taskDetailQuery.data.dependencies.length}
                              </div>
                            </div>
                          </div>
                        }
                        sections={[
                          {
                            id: "subtasks",
                            label: "Subtasks",
                            content: (
                              <>
                                <div className="flex flex-col gap-2">
                                  {(
                                    subtasksByParent.get(
                                      taskDetailQuery.data.id,
                                    ) ?? []
                                  ).map((subtask) => (
                                    <button
                                      key={subtask.id}
                                      onClick={() =>
                                        setInspectedTaskId(subtask.id)
                                      }
                                      className="rounded-2xl border border-white/8 bg-white/4 px-3 py-3 text-left"
                                    >
                                      <div className="flex items-center justify-between gap-3">
                                        <div className="text-sm font-medium text-slate-100">
                                          {subtask.title}
                                        </div>
                                        <Pill className="border-white/8 text-slate-300">
                                          {subtask.workflow_state}
                                        </Pill>
                                      </div>
                                    </button>
                                  ))}
                                  {!(
                                    subtasksByParent.get(
                                      taskDetailQuery.data.id,
                                    ) ?? []
                                  ).length ? (
                                    <div className="text-sm text-slate-500">
                                      No subtasks yet.
                                    </div>
                                  ) : null}
                                </div>
                                <input
                                  value={draftSubtaskTitle}
                                  onChange={(event) =>
                                    setDraftSubtaskTitle(event.target.value)
                                  }
                                  placeholder="Add a subtask under this task"
                                  className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                                />
                                <button
                                  onClick={() =>
                                    createSubtaskMutation.mutate({
                                      project_id:
                                        taskDetailQuery.data.project_id,
                                      title: draftSubtaskTitle,
                                      parent_task_id: taskDetailQuery.data.id,
                                      board_column_key: "backlog",
                                    })
                                  }
                                  disabled={
                                    !draftSubtaskTitle.trim() ||
                                    createSubtaskMutation.isPending
                                  }
                                  className="mt-3 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                  Add subtask
                                </button>
                              </>
                            ),
                          },
                          {
                            id: "dependencies",
                            label: "Dependencies",
                            content: (
                              <>
                                <div className="flex flex-col gap-2">
                                  {taskDetailQuery.data.dependencies.map(
                                    (dependency) => {
                                      const dependencyTask =
                                        projectDetailQuery.data?.board.tasks.find(
                                          (candidate) =>
                                            candidate.id ===
                                            dependency.depends_on_task_id,
                                        );
                                      return (
                                        <div
                                          key={dependency.id}
                                          className="rounded-2xl border border-white/8 bg-white/4 px-3 py-3"
                                        >
                                          <div className="flex items-center justify-between gap-3">
                                            <div className="text-sm font-medium text-slate-100">
                                              {dependencyTask?.title ??
                                                dependency.depends_on_task_id}
                                            </div>
                                            <Pill className="border-white/8 text-slate-300">
                                              {dependency.relationship_type}
                                            </Pill>
                                          </div>
                                        </div>
                                      );
                                    },
                                  )}
                                  {!taskDetailQuery.data.dependencies.length ? (
                                    <div className="text-sm text-slate-500">
                                      No explicit dependencies yet.
                                    </div>
                                  ) : null}
                                </div>
                                <select
                                  value={selectedDependencyTaskId}
                                  onChange={(event) =>
                                    setSelectedDependencyTaskId(
                                      event.target.value,
                                    )
                                  }
                                  className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                                >
                                  <option value="">Select blocker task</option>
                                  {(projectDetailQuery.data?.board.tasks ?? [])
                                    .filter(
                                      (candidate) =>
                                        candidate.id !==
                                        taskDetailQuery.data.id,
                                    )
                                    .map((candidate) => (
                                      <option
                                        key={candidate.id}
                                        value={candidate.id}
                                      >
                                        {candidate.title}
                                      </option>
                                    ))}
                                </select>
                                <button
                                  onClick={() =>
                                    addTaskDependencyMutation.mutate({
                                      taskId: taskDetailQuery.data!.id,
                                      dependsOnTaskId: selectedDependencyTaskId,
                                    })
                                  }
                                  disabled={
                                    !selectedDependencyTaskId ||
                                    addTaskDependencyMutation.isPending
                                  }
                                  className="mt-3 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                  Add dependency
                                </button>
                              </>
                            ),
                          },
                          {
                            id: "comments",
                            label: "Comments",
                            content: (
                              <>
                                <div className="flex flex-col gap-2">
                                  {taskDetailQuery.data.comments.map(
                                    (comment) => (
                                      <div
                                        key={comment.id}
                                        className="rounded-2xl border border-white/8 bg-white/4 px-3 py-3"
                                      >
                                        <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
                                          {comment.author_name}
                                        </div>
                                        <div className="mt-2 text-sm text-slate-200">
                                          {comment.body}
                                        </div>
                                      </div>
                                    ),
                                  )}
                                  {!taskDetailQuery.data.comments.length ? (
                                    <div className="text-sm text-slate-500">
                                      No comments yet.
                                    </div>
                                  ) : null}
                                </div>
                                <textarea
                                  value={draftCommentBody}
                                  onChange={(event) =>
                                    setDraftCommentBody(event.target.value)
                                  }
                                  placeholder="Add operator note"
                                  className="mt-3 min-h-24 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                                />
                                <button
                                  onClick={() =>
                                    addTaskCommentMutation.mutate({
                                      taskId: taskDetailQuery.data!.id,
                                      body: draftCommentBody,
                                    })
                                  }
                                  disabled={
                                    !draftCommentBody.trim() ||
                                    addTaskCommentMutation.isPending
                                  }
                                  className="mt-3 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                  Add comment
                                </button>
                              </>
                            ),
                          },
                          {
                            id: "checks",
                            label: "Checks",
                            content: (
                              <>
                                <div className="flex flex-col gap-2">
                                  {taskDetailQuery.data.checks.map((check) => (
                                    <div
                                      key={check.id}
                                      className="rounded-2xl border border-white/8 bg-white/4 px-3 py-3"
                                    >
                                      <div className="flex items-center justify-between gap-3">
                                        <div className="text-sm font-medium text-slate-100">
                                          {check.check_type}
                                        </div>
                                        <Pill className="border-white/8 text-slate-300">
                                          {check.status}
                                        </Pill>
                                      </div>
                                      <div className="mt-2 text-sm text-slate-200">
                                        {check.summary}
                                      </div>
                                    </div>
                                  ))}
                                  {!taskDetailQuery.data.checks.length ? (
                                    <div className="text-sm text-slate-500">
                                      No checks yet.
                                    </div>
                                  ) : null}
                                </div>
                                <div className="mt-3 grid gap-3 md:grid-cols-2">
                                  <input
                                    value={draftCheckType}
                                    onChange={(event) =>
                                      setDraftCheckType(event.target.value)
                                    }
                                    placeholder="Check type"
                                    className="rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                                  />
                                  <select
                                    value={draftCheckStatus}
                                    onChange={(event) =>
                                      setDraftCheckStatus(event.target.value)
                                    }
                                    className="rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                                  >
                                    {[
                                      "pending",
                                      "passed",
                                      "failed",
                                      "warning",
                                    ].map((status) => (
                                      <option key={status} value={status}>
                                        {status}
                                      </option>
                                    ))}
                                  </select>
                                </div>
                                <textarea
                                  value={draftCheckSummary}
                                  onChange={(event) =>
                                    setDraftCheckSummary(event.target.value)
                                  }
                                  placeholder="What was checked?"
                                  className="mt-3 min-h-24 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                                />
                                <button
                                  onClick={() =>
                                    addTaskCheckMutation.mutate({
                                      taskId: taskDetailQuery.data!.id,
                                      checkType: draftCheckType,
                                      status: draftCheckStatus,
                                      summary: draftCheckSummary,
                                    })
                                  }
                                  disabled={
                                    !draftCheckSummary.trim() ||
                                    addTaskCheckMutation.isPending
                                  }
                                  className="mt-3 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                  Add check
                                </button>
                              </>
                            ),
                          },
                          {
                            id: "artifacts",
                            label: "Artifacts",
                            content: (
                              <>
                                <div className="flex flex-col gap-2">
                                  {taskDetailQuery.data.artifacts.map(
                                    (artifact) => (
                                      <div
                                        key={artifact.id}
                                        className="rounded-2xl border border-white/8 bg-white/4 px-3 py-3"
                                      >
                                        <div className="flex items-center justify-between gap-3">
                                          <div className="text-sm font-medium text-slate-100">
                                            {artifact.name}
                                          </div>
                                          <Pill className="border-white/8 text-slate-300">
                                            {artifact.artifact_type}
                                          </Pill>
                                        </div>
                                        <div className="mt-2 break-all text-sm text-slate-400">
                                          {artifact.uri}
                                        </div>
                                      </div>
                                    ),
                                  )}
                                  {!taskDetailQuery.data.artifacts.length ? (
                                    <div className="text-sm text-slate-500">
                                      No artifacts yet.
                                    </div>
                                  ) : null}
                                </div>
                                <div className="mt-3 grid gap-3 md:grid-cols-2">
                                  <input
                                    value={draftArtifactType}
                                    onChange={(event) =>
                                      setDraftArtifactType(event.target.value)
                                    }
                                    placeholder="Artifact type"
                                    className="rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                                  />
                                  <input
                                    value={draftArtifactName}
                                    onChange={(event) =>
                                      setDraftArtifactName(event.target.value)
                                    }
                                    placeholder="Artifact name"
                                    className="rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                                  />
                                </div>
                                <input
                                  value={draftArtifactUri}
                                  onChange={(event) =>
                                    setDraftArtifactUri(event.target.value)
                                  }
                                  placeholder="file path, branch, diff, or URL"
                                  className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                                />
                                <button
                                  onClick={() =>
                                    addTaskArtifactMutation.mutate({
                                      taskId: taskDetailQuery.data!.id,
                                      artifactType: draftArtifactType,
                                      name: draftArtifactName,
                                      uri: draftArtifactUri,
                                    })
                                  }
                                  disabled={
                                    !draftArtifactName.trim() ||
                                    !draftArtifactUri.trim() ||
                                    addTaskArtifactMutation.isPending
                                  }
                                  className="mt-3 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                  Add artifact
                                </button>
                              </>
                            ),
                          },
                          {
                            id: "waiting",
                            label: "Waiting",
                            content: (
                              <div className="flex flex-col gap-2">
                                {taskDetailQuery.data.waiting_questions.map(
                                  (question) => (
                                    <div
                                      key={question.id}
                                      className="rounded-2xl border border-white/8 bg-black/15 px-3 py-3"
                                    >
                                      <div className="text-sm font-medium text-slate-100">
                                        {question.prompt}
                                      </div>
                                      <div className="mt-2 text-sm text-slate-400">
                                        {question.blocked_reason ??
                                          "Awaiting operator input."}
                                      </div>
                                    </div>
                                  ),
                                )}
                                {!taskDetailQuery.data.waiting_questions
                                  .length ? (
                                  <div className="text-sm text-slate-500">
                                    No waiting items for this task.
                                  </div>
                                ) : null}
                              </div>
                            ),
                          },
                          {
                            id: "timeline",
                            label: "Timeline",
                            content: (
                              <div className="flex flex-col gap-2">
                                {[
                                  ...taskDetailQuery.data.comments.map(
                                    (comment) => ({
                                      id: comment.id,
                                      kind: "comment",
                                      ts: comment.created_at,
                                      text: comment.body,
                                    }),
                                  ),
                                  ...taskDetailQuery.data.checks.map(
                                    (check) => ({
                                      id: check.id,
                                      kind: "check",
                                      ts: check.created_at,
                                      text: check.summary,
                                    }),
                                  ),
                                  ...taskDetailQuery.data.artifacts.map(
                                    (artifact) => ({
                                      id: artifact.id,
                                      kind: "artifact",
                                      ts: artifact.created_at,
                                      text: artifact.name,
                                    }),
                                  ),
                                ]
                                  .sort(
                                    (a, b) =>
                                      new Date(b.ts).getTime() -
                                      new Date(a.ts).getTime(),
                                  )
                                  .slice(0, 8)
                                  .map((item) => (
                                    <div
                                      key={item.id}
                                      className="rounded-2xl border border-white/8 bg-black/15 px-3 py-3"
                                    >
                                      <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
                                        {item.kind}
                                      </div>
                                      <div className="mt-2 text-sm text-slate-200">
                                        {item.text}
                                      </div>
                                      <div className="mt-2 text-xs text-slate-500">
                                        {new Date(item.ts).toLocaleString()}
                                      </div>
                                    </div>
                                  ))}
                                {!(
                                  taskDetailQuery.data.comments.length +
                                  taskDetailQuery.data.checks.length +
                                  taskDetailQuery.data.artifacts.length
                                ) ? (
                                  <div className="text-sm text-slate-500">
                                    No timeline activity yet.
                                  </div>
                                ) : null}
                              </div>
                            ),
                          },
                        ]}
                      />
                    ) : (
                      <SectionFrame className="px-5 py-5">
                        <div className="text-sm text-slate-500">
                          Select a task card to inspect comments, checks, and
                          artifacts.
                        </div>
                      </SectionFrame>
                    )
                  ) : null}

                  <WorktreeInventoryScreen>
                    {activeSection === "worktrees" ? (
                      <SectionFrame className="px-5 py-5">
                        <SectionTitle>Repository Inventory</SectionTitle>
                        <div className="mt-4 flex flex-col gap-3">
                          {projectDetailQuery.data?.repositories.map(
                            (repository) => (
                              <div
                                key={repository.id}
                                className="rounded-2xl border border-white/7 bg-white/3 px-4 py-4"
                              >
                                <div className="flex items-start justify-between gap-3">
                                  <div>
                                    <div className="text-sm font-semibold text-slate-100">
                                      {repository.name}
                                    </div>
                                    <div className="mt-1 break-all text-xs text-slate-500">
                                      {repository.local_path}
                                    </div>
                                  </div>
                                  <Pill className="border-white/8 text-slate-300">
                                    {repository.default_branch ?? "detached"}
                                  </Pill>
                                </div>
                                <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
                                  <span>
                                    dirty:{" "}
                                    {String(
                                      repository.metadata_json.is_dirty ??
                                        false,
                                    )}
                                  </span>
                                  <span>
                                    remotes:{" "}
                                    {Array.isArray(
                                      repository.metadata_json.remotes,
                                    )
                                      ? repository.metadata_json.remotes.length
                                      : 0}
                                  </span>
                                </div>
                              </div>
                            ),
                          )}
                          {!projectDetailQuery.data?.repositories.length ? (
                            <div className="text-sm text-slate-500">
                              Attach a local git repo to unlock worktrees.
                            </div>
                          ) : null}
                        </div>

                        {selectedProjectId ? (
                          <div className="mt-5 rounded-2xl border border-white/7 bg-black/10 p-4">
                            <div className="text-sm font-medium text-slate-200">
                              Attach repository
                            </div>
                            <input
                              value={draftRepoPath}
                              onChange={(event) =>
                                setDraftRepoPath(event.target.value)
                              }
                              placeholder="/absolute/path/to/repo"
                              className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                            />
                            <input
                              value={draftRepoName}
                              onChange={(event) =>
                                setDraftRepoName(event.target.value)
                              }
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
                              disabled={
                                !draftRepoPath.trim() ||
                                createRepositoryMutation.isPending
                              }
                              className="mt-3 rounded-full bg-[color:var(--color-accent-primary)] px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                              Attach repo
                            </button>
                          </div>
                        ) : null}
                      </SectionFrame>
                    ) : null}
                  </WorktreeInventoryScreen>

                  <WorktreeInventoryScreen>
                    {activeSection === "worktrees" ? (
                      <SectionFrame className="px-5 py-5">
                        <SectionTitle>Worktree Fleet</SectionTitle>
                        <div className="mt-4 flex flex-col gap-3">
                          {projectDetailQuery.data?.worktrees.map(
                            (worktree) => (
                              <div
                                key={worktree.id}
                                className="rounded-2xl border border-white/7 bg-white/3 px-4 py-4"
                              >
                                {staleWorktreesById.get(worktree.id) ? (
                                  <div className="mb-3 rounded-2xl border border-amber-300/20 bg-amber-300/10 px-3 py-2 text-xs text-amber-100">
                                    Recommended:{" "}
                                    {
                                      staleWorktreesById.get(worktree.id)
                                        ?.recommendation
                                    }
                                    {" · "}
                                    {(
                                      staleWorktreesById.get(worktree.id)
                                        ?.reasons ?? []
                                    ).join(", ")}
                                  </div>
                                ) : null}
                                <div className="flex items-start justify-between gap-3">
                                  <div className="min-w-0">
                                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-100">
                                      <GitBranch className="h-4 w-4 text-slate-400" />
                                      <span className="truncate">
                                        {worktree.branch_name}
                                      </span>
                                    </div>
                                    <div className="mt-1 break-all text-xs text-slate-500">
                                      {worktree.path}
                                    </div>
                                  </div>
                                  <Pill className="border-white/8 text-slate-300">
                                    {worktree.status}
                                  </Pill>
                                </div>
                                <div className="mt-3 flex gap-2">
                                  {worktree.status === "active" ? (
                                    <>
                                      <button
                                        onClick={() =>
                                          patchWorktreeMutation.mutate({
                                            worktreeId: worktree.id,
                                            status: "locked",
                                          })
                                        }
                                        className="inline-flex items-center gap-2 rounded-full border border-white/8 px-3 py-1.5 text-xs text-slate-200"
                                      >
                                        <Lock className="h-3.5 w-3.5" />
                                        Lock
                                      </button>
                                      <button
                                        onClick={() =>
                                          patchWorktreeMutation.mutate({
                                            worktreeId: worktree.id,
                                            status: "archived",
                                          })
                                        }
                                        className="inline-flex items-center gap-2 rounded-full border border-white/8 px-3 py-1.5 text-xs text-slate-200"
                                      >
                                        <GitFork className="h-3.5 w-3.5" />
                                        Archive
                                      </button>
                                    </>
                                  ) : null}
                                  {worktree.status === "locked" ||
                                  worktree.status === "archived" ? (
                                    <button
                                      onClick={() =>
                                        patchWorktreeMutation.mutate({
                                          worktreeId: worktree.id,
                                          status: "pruned",
                                        })
                                      }
                                      className="inline-flex items-center gap-2 rounded-full border border-rose-300/20 px-3 py-1.5 text-xs text-rose-100"
                                    >
                                      <Trash2 className="h-3.5 w-3.5" />
                                      Prune
                                    </button>
                                  ) : null}
                                </div>
                              </div>
                            ),
                          )}
                          {!projectDetailQuery.data?.worktrees.length ? (
                            <div className="text-sm text-slate-500">
                              No worktrees allocated yet.
                            </div>
                          ) : null}
                        </div>

                        {selectedProjectId ? (
                          <div className="mt-5 rounded-2xl border border-white/7 bg-black/10 p-4">
                            <div className="text-sm font-medium text-slate-200">
                              Allocate worktree
                            </div>
                            <select
                              value={selectedRepositoryId ?? ""}
                              onChange={(event) =>
                                setSelectedRepositoryId(
                                  event.target.value || null,
                                )
                              }
                              className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                            >
                              <option value="">Choose repository</option>
                              {(
                                projectDetailQuery.data?.repositories ?? []
                              ).map((repository) => (
                                <option
                                  key={repository.id}
                                  value={repository.id}
                                >
                                  {repository.name}
                                </option>
                              ))}
                            </select>
                            <select
                              value={selectedTaskId}
                              onChange={(event) =>
                                setSelectedTaskId(event.target.value)
                              }
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
                              onChange={(event) =>
                                setDraftWorktreeLabel(event.target.value)
                              }
                              placeholder="Optional label for an unlinked worktree"
                              className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                            />
                            <button
                              onClick={() =>
                                createWorktreeMutation.mutate({
                                  repository_id: selectedRepositoryId!,
                                  task_id: selectedTaskId || undefined,
                                  label: selectedTaskId
                                    ? undefined
                                    : draftWorktreeLabel || undefined,
                                })
                              }
                              disabled={
                                !selectedRepositoryId ||
                                createWorktreeMutation.isPending
                              }
                              className="mt-3 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                              Allocate
                            </button>
                          </div>
                        ) : null}
                      </SectionFrame>
                    ) : null}
                  </WorktreeInventoryScreen>

                  {activeSection === "sessions" ? (
                    <SectionFrame className="px-5 py-5">
                      <SectionTitle>Session Runtime</SectionTitle>
                      <div className="mt-4 flex flex-col gap-3">
                        {projectDetailQuery.data?.sessions.map((session) => (
                          <button
                            key={session.id}
                            onClick={() => setSelectedSessionId(session.id)}
                            className={[
                              "rounded-2xl border px-4 py-4 text-left",
                              selectedSessionId === session.id
                                ? "border-[color:var(--color-accent-primary)] bg-[color:var(--color-accent-soft)]"
                                : "border-white/7 bg-white/3",
                            ].join(" ")}
                          >
                            <div className="flex items-center justify-between gap-3">
                              <div className="flex items-center gap-2 text-sm font-semibold text-slate-100">
                                <Terminal className="h-4 w-4 text-slate-400" />
                                {session.profile}
                              </div>
                              <Pill className="border-white/8 text-slate-300">
                                {session.status}
                              </Pill>
                            </div>
                            <div className="mt-2 text-xs text-slate-500">
                              {session.session_name}
                            </div>
                          </button>
                        ))}
                        {!projectDetailQuery.data?.sessions.length ? (
                          <div className="text-sm text-slate-500">
                            No agent sessions yet.
                          </div>
                        ) : null}
                      </div>

                      {selectedProjectId ? (
                        <div className="mt-5 rounded-2xl border border-white/7 bg-black/10 p-4">
                          <div className="text-sm font-medium text-slate-200">
                            Spawn session
                          </div>
                          <select
                            value={selectedSessionTaskId}
                            onChange={(event) =>
                              setSelectedSessionTaskId(event.target.value)
                            }
                            className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                          >
                            <option value="">Choose task</option>
                            {topLevelTasks.map((task) => (
                              <option key={task.id} value={task.id}>
                                {task.title}
                              </option>
                            ))}
                          </select>
                          <select
                            value={selectedSessionWorktreeId}
                            onChange={(event) =>
                              setSelectedSessionWorktreeId(event.target.value)
                            }
                            className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                          >
                            <option value="">No worktree</option>
                            {(projectDetailQuery.data?.worktrees ?? [])
                              .filter(
                                (worktree) => worktree.status !== "pruned",
                              )
                              .map((worktree) => (
                                <option key={worktree.id} value={worktree.id}>
                                  {worktree.branch_name}
                                </option>
                              ))}
                          </select>
                          <select
                            value={sessionProfile}
                            onChange={(event) =>
                              setSessionProfile(event.target.value)
                            }
                            className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                          >
                            {[
                              "executor",
                              "reviewer",
                              "verifier",
                              "research",
                              "docs",
                            ].map((profile) => (
                              <option key={profile} value={profile}>
                                {profile}
                              </option>
                            ))}
                          </select>
                          <button
                            onClick={() =>
                              createSessionMutation.mutate({
                                task_id: selectedSessionTaskId,
                                profile: sessionProfile,
                                worktree_id:
                                  selectedSessionWorktreeId || undefined,
                              })
                            }
                            disabled={
                              !selectedSessionTaskId ||
                              createSessionMutation.isPending
                            }
                            className="mt-3 inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                          >
                            <Play className="h-4 w-4" />
                            Spawn
                          </button>
                        </div>
                      ) : null}

                      {selectedSession ? (
                        <div className="mt-5">
                          <SessionDetailScreen
                            profile={selectedSession.profile}
                            status={selectedSession.status}
                            summary={
                              <div className="grid gap-1 text-xs sm:grid-cols-2">
                                <span>Task: {selectedSession.task_id}</span>
                                <span>
                                  Project: {selectedSession.project_id}
                                </span>
                                <span>
                                  Worktree:{" "}
                                  {selectedSession.worktree_id ?? "none"}
                                </span>
                                <span>
                                  Branch:{" "}
                                  {projectDetailQuery.data?.worktrees.find(
                                    (worktree) =>
                                      worktree.id ===
                                      selectedSession.worktree_id,
                                  )?.branch_name ?? "detached"}
                                </span>
                              </div>
                            }
                            actions={
                              <>
                                {selectedSessionId &&
                                sessionTailQuery.data?.session.status ===
                                  "running" ? (
                                  <button
                                    onClick={() =>
                                      cancelSessionMutation.mutate(
                                        selectedSessionId,
                                      )
                                    }
                                    disabled={cancelSessionMutation.isPending}
                                    className="rounded-full border border-rose-300/25 px-4 py-2 text-sm font-semibold text-rose-100 disabled:cursor-not-allowed disabled:opacity-50"
                                  >
                                    Cancel session
                                  </button>
                                ) : null}
                                {sessionTimelineQuery.data ? (
                                  <button
                                    onClick={() =>
                                      createFollowUpSessionMutation.mutate({
                                        sessionId:
                                          sessionTimelineQuery.data.session.id,
                                        profile:
                                          sessionTimelineQuery.data.session
                                            .profile,
                                        followUpType: "retry",
                                      })
                                    }
                                    disabled={
                                      createFollowUpSessionMutation.isPending
                                    }
                                    className="inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-2 text-xs font-semibold text-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
                                  >
                                    <GitFork className="h-3.5 w-3.5" />
                                    Retry
                                  </button>
                                ) : null}
                              </>
                            }
                            outputPanel={
                              sessionTailQuery.data ? (
                                <pre className="max-h-72 overflow-auto rounded-2xl bg-black/25 p-3 text-xs leading-5 text-slate-300">
                                  {sessionTailQuery.data.lines.join("\n")}
                                </pre>
                              ) : (
                                <div className="text-sm text-slate-500">
                                  Select a session to inspect recent runtime
                                  output.
                                </div>
                              )
                            }
                            structuredPanels={[
                              {
                                id: "messages",
                                label: "Emitted comments",
                                content: sessionTimelineQuery.data ? (
                                  <div className="flex flex-col gap-2">
                                    {sessionTimelineQuery.data.messages
                                      .slice(0, 4)
                                      .map((message) => (
                                        <div
                                          key={message.id}
                                          className="rounded-2xl border border-white/8 bg-black/15 px-3 py-3"
                                        >
                                          <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
                                            {message.source}
                                          </div>
                                          <div className="mt-2 text-sm text-slate-200">
                                            {message.body}
                                          </div>
                                        </div>
                                      ))}
                                    {!sessionTimelineQuery.data.messages
                                      .length ? (
                                      <div className="text-sm text-slate-500">
                                        No structured session messages yet.
                                      </div>
                                    ) : null}
                                  </div>
                                ) : (
                                  <div className="text-sm text-slate-500">
                                    No selected session.
                                  </div>
                                ),
                              },
                              {
                                id: "checks",
                                label: "Emitted checks",
                                content: selectedSessionTaskDetailQuery.data ? (
                                  <div className="flex flex-col gap-2">
                                    {selectedSessionTaskDetailQuery.data.checks
                                      .slice(0, 4)
                                      .map((check) => (
                                        <div
                                          key={check.id}
                                          className="rounded-2xl border border-white/8 bg-black/15 px-3 py-3"
                                        >
                                          <div className="flex items-center justify-between gap-2">
                                            <div className="text-sm text-slate-100">
                                              {check.check_type}
                                            </div>
                                            <Pill className="border-white/8 text-slate-300">
                                              {check.status}
                                            </Pill>
                                          </div>
                                          <div className="mt-2 text-sm text-slate-400">
                                            {check.summary}
                                          </div>
                                        </div>
                                      ))}
                                    {!selectedSessionTaskDetailQuery.data.checks
                                      .length ? (
                                      <div className="text-sm text-slate-500">
                                        No task checks emitted yet.
                                      </div>
                                    ) : null}
                                  </div>
                                ) : (
                                  <div className="text-sm text-slate-500">
                                    No linked task selected.
                                  </div>
                                ),
                              },
                              {
                                id: "waiting",
                                label: "Waiting items",
                                content: sessionTimelineQuery.data ? (
                                  <div className="flex flex-col gap-2">
                                    {sessionTimelineQuery.data.waiting_questions
                                      .slice(0, 4)
                                      .map((question) => (
                                        <div
                                          key={question.id}
                                          className="rounded-2xl border border-white/8 bg-black/15 px-3 py-3"
                                        >
                                          <div className="text-sm font-medium text-slate-100">
                                            {question.prompt}
                                          </div>
                                          <div className="mt-2 text-sm text-slate-400">
                                            {question.blocked_reason ??
                                              "Waiting on operator input."}
                                          </div>
                                        </div>
                                      ))}
                                    {!sessionTimelineQuery.data
                                      .waiting_questions.length ? (
                                      <div className="text-sm text-slate-500">
                                        No waiting items linked to this session.
                                      </div>
                                    ) : null}
                                  </div>
                                ) : (
                                  <div className="text-sm text-slate-500">
                                    No selected session.
                                  </div>
                                ),
                              },
                              {
                                id: "events",
                                label: "Timeline/events",
                                content: sessionTimelineQuery.data ? (
                                  <div className="flex flex-col gap-2">
                                    {sessionTimelineQuery.data.events
                                      .slice(0, 4)
                                      .map((event) => (
                                        <div
                                          key={event.id}
                                          className="rounded-2xl border border-white/8 bg-black/15 px-3 py-3"
                                        >
                                          <div className="text-sm font-medium text-slate-100">
                                            {formatEvent(event.event_type)}
                                          </div>
                                          <div className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">
                                            {new Date(
                                              event.created_at,
                                            ).toLocaleString()}
                                          </div>
                                        </div>
                                      ))}
                                    {!sessionTimelineQuery.data.events
                                      .length ? (
                                      <div className="text-sm text-slate-500">
                                        No session events recorded yet.
                                      </div>
                                    ) : null}
                                  </div>
                                ) : (
                                  <div className="text-sm text-slate-500">
                                    No selected session.
                                  </div>
                                ),
                              },
                            ]}
                          />
                        </div>
                      ) : null}

                      <div className="mt-5 rounded-2xl border border-white/7 bg-black/10 p-4">
                        <div className="text-sm font-medium text-slate-200">
                          Open waiting question
                        </div>
                        <select
                          value={selectedSessionTaskId}
                          onChange={(event) =>
                            setSelectedSessionTaskId(event.target.value)
                          }
                          className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                        >
                          <option value="">Choose task</option>
                          {topLevelTasks.map((task) => (
                            <option key={task.id} value={task.id}>
                              {task.title}
                            </option>
                          ))}
                        </select>
                        <select
                          value={selectedSessionId ?? ""}
                          onChange={(event) =>
                            setSelectedSessionId(event.target.value || null)
                          }
                          className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                        >
                          <option value="">Optional linked session</option>
                          {(projectDetailQuery.data?.sessions ?? []).map(
                            (session) => (
                              <option key={session.id} value={session.id}>
                                {session.profile} · {session.session_name}
                              </option>
                            ),
                          )}
                        </select>
                        <textarea
                          value={draftQuestionPrompt}
                          onChange={(event) =>
                            setDraftQuestionPrompt(event.target.value)
                          }
                          placeholder="What decision or clarification does the agent need?"
                          className="mt-3 min-h-24 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                        />
                        <input
                          value={draftQuestionReason}
                          onChange={(event) =>
                            setDraftQuestionReason(event.target.value)
                          }
                          placeholder="Why is work blocked?"
                          className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                        />
                        <select
                          value={draftQuestionUrgency}
                          onChange={(event) =>
                            setDraftQuestionUrgency(event.target.value)
                          }
                          className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                        >
                          {["low", "medium", "high", "urgent"].map(
                            (urgency) => (
                              <option key={urgency} value={urgency}>
                                {urgency}
                              </option>
                            ),
                          )}
                        </select>
                        <button
                          onClick={() =>
                            createQuestionMutation.mutate({
                              task_id: selectedSessionTaskId,
                              session_id: selectedSessionId || undefined,
                              prompt: draftQuestionPrompt,
                              blocked_reason: draftQuestionReason || undefined,
                              urgency: draftQuestionUrgency,
                            })
                          }
                          disabled={
                            !selectedSessionTaskId ||
                            !draftQuestionPrompt.trim() ||
                            createQuestionMutation.isPending
                          }
                          className="mt-3 rounded-full bg-[color:var(--color-accent-primary)] px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          Open question
                        </button>
                      </div>
                    </SectionFrame>
                  ) : null}

                  <WaitingInboxScreen>
                    {activeSection === "waiting" ? (
                      <SectionFrame className="px-5 py-5">
                        <SectionTitle>Waiting Inbox</SectionTitle>
                        <div className="mt-4 flex flex-col gap-3">
                          {(
                            projectDetailQuery.data?.waiting_questions ?? []
                          ).map((question) => (
                            <button
                              key={question.id}
                              onClick={() => setSelectedQuestionId(question.id)}
                              className={[
                                "rounded-2xl border px-4 py-4 text-left",
                                selectedQuestionId === question.id
                                  ? "border-[color:var(--color-accent-primary)] bg-[color:var(--color-accent-soft)]"
                                  : "border-white/7 bg-white/3",
                              ].join(" ")}
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div className="text-sm font-semibold text-slate-100">
                                  {question.prompt}
                                </div>
                                <Pill className="border-white/8 text-slate-300">
                                  {question.urgency ?? "open"}
                                </Pill>
                              </div>
                              <div className="mt-2 text-xs text-slate-500">
                                {question.blocked_reason ??
                                  "Awaiting operator input"}
                              </div>
                            </button>
                          ))}
                          {!projectDetailQuery.data?.waiting_questions
                            .length ? (
                            <div className="text-sm text-slate-500">
                              No waiting questions right now.
                            </div>
                          ) : null}
                        </div>

                        <div className="mt-5 rounded-2xl border border-white/7 bg-black/15 p-4">
                          <div className="flex items-center gap-2 text-sm font-medium text-slate-200">
                            <MessageSquareText className="h-4 w-4 text-slate-400" />
                            Selected question
                          </div>
                          {questionDetailQuery.data ? (
                            <>
                              <div className="mt-3 text-sm font-semibold text-slate-100">
                                {questionDetailQuery.data.prompt}
                              </div>
                              <div className="mt-2 text-sm text-slate-400">
                                {questionDetailQuery.data.blocked_reason ??
                                  "No explicit blocked reason provided."}
                              </div>
                              <div className="mt-3 flex flex-wrap gap-2">
                                <Pill className="border-white/8 text-slate-300">
                                  {questionDetailQuery.data.status}
                                </Pill>
                                <Pill className="border-white/8 text-slate-300">
                                  {questionDetailQuery.data.urgency ?? "normal"}
                                </Pill>
                              </div>
                              <div className="mt-4 flex flex-col gap-2">
                                {questionDetailQuery.data.replies.map(
                                  (reply) => (
                                    <div
                                      key={reply.id}
                                      className="rounded-2xl border border-white/8 bg-white/4 px-3 py-3"
                                    >
                                      <div className="text-xs uppercase tracking-[0.18em] text-slate-500">
                                        {reply.responder_name}
                                      </div>
                                      <div className="mt-2 text-sm text-slate-200">
                                        {reply.body}
                                      </div>
                                    </div>
                                  ),
                                )}
                                {!questionDetailQuery.data.replies.length ? (
                                  <div className="text-sm text-slate-500">
                                    No replies yet.
                                  </div>
                                ) : null}
                              </div>
                              {questionDetailQuery.data.status === "open" ? (
                                <>
                                  <textarea
                                    value={draftReplyBody}
                                    onChange={(event) =>
                                      setDraftReplyBody(event.target.value)
                                    }
                                    placeholder="Reply to unblock the agent"
                                    className="mt-4 min-h-24 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                                  />
                                  <button
                                    onClick={() =>
                                      answerQuestionMutation.mutate({
                                        questionId:
                                          questionDetailQuery.data!.id,
                                        body: draftReplyBody,
                                      })
                                    }
                                    disabled={
                                      !draftReplyBody.trim() ||
                                      answerQuestionMutation.isPending
                                    }
                                    className="mt-3 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                                  >
                                    Send reply
                                  </button>
                                </>
                              ) : null}
                            </>
                          ) : (
                            <div className="mt-3 text-sm text-slate-500">
                              Select a waiting question to inspect and answer
                              it.
                            </div>
                          )}
                        </div>
                      </SectionFrame>
                    ) : null}
                  </WaitingInboxScreen>

                  <DiagnosticsScreen>
                    {activeSection === "diagnostics" ? (
                      <SectionFrame className="px-5 py-5">
                        <SectionTitle>Runtime readiness</SectionTitle>
                        <div className="mt-5 grid gap-3">
                          <Signal
                            label="tmux"
                            ready={Boolean(
                              diagnosticsQuery.data?.tmux_available,
                            )}
                            icon={Bot}
                          />
                          <Signal
                            label="tmux server"
                            ready={Boolean(
                              diagnosticsQuery.data?.tmux_server_running,
                            )}
                            icon={Terminal}
                          />
                          <Signal
                            label="git"
                            ready={Boolean(
                              diagnosticsQuery.data?.git_available,
                            )}
                            icon={FolderGit2}
                          />
                          <Signal
                            label="runtime orphans"
                            ready={
                              !Boolean(
                                diagnosticsQuery.data
                                  ?.orphan_runtime_session_count,
                              )
                            }
                            icon={Activity}
                          />
                          <Signal label="audit log" ready icon={ShieldCheck} />
                          <Signal
                            label="waiting inbox"
                            ready
                            icon={MessageSquareText}
                          />
                        </div>
                      </SectionFrame>
                    ) : null}
                  </DiagnosticsScreen>

                  <DiagnosticsScreen>
                    {activeSection === "diagnostics" ? (
                      <SectionFrame className="px-5 py-5">
                        <SectionTitle>Diagnostics</SectionTitle>
                        <div className="mt-4 grid gap-3">
                          <DiagRow
                            label="DB path"
                            value={
                              diagnosticsQuery.data?.database_path ?? "unknown"
                            }
                          />
                          <DiagRow
                            label="Runtime home"
                            value={
                              diagnosticsQuery.data?.runtime_home ?? "unknown"
                            }
                          />
                          <DiagRow
                            label="Repositories"
                            value={String(
                              diagnosticsQuery.data?.current_repository_count ??
                                0,
                            )}
                          />
                          <DiagRow
                            label="Worktrees"
                            value={String(
                              diagnosticsQuery.data?.current_worktree_count ??
                                0,
                            )}
                          />
                          <DiagRow
                            label="Sessions"
                            value={String(
                              diagnosticsQuery.data?.current_session_count ?? 0,
                            )}
                          />
                          <DiagRow
                            label="Runtime sessions"
                            value={String(
                              diagnosticsQuery.data
                                ?.runtime_managed_session_count ?? 0,
                            )}
                          />
                          <DiagRow
                            label="Reconciled on check"
                            value={String(
                              diagnosticsQuery.data?.reconciled_session_count ??
                                0,
                            )}
                          />
                          <DiagRow
                            label="Orphan tmux sessions"
                            value={String(
                              diagnosticsQuery.data
                                ?.orphan_runtime_session_count ?? 0,
                            )}
                          />
                          <DiagRow
                            label="Stale worktrees"
                            value={String(
                              diagnosticsQuery.data?.stale_worktree_count ?? 0,
                            )}
                          />
                          <DiagRow
                            label="Open questions"
                            value={String(
                              diagnosticsQuery.data
                                ?.current_open_question_count ?? 0,
                            )}
                          />
                          <DiagRow
                            label="Events"
                            value={String(
                              diagnosticsQuery.data?.current_event_count ?? 0,
                            )}
                          />
                        </div>
                        {diagnosticsQuery.data?.orphan_runtime_sessions
                          .length ? (
                          <div className="mt-4 rounded-2xl border border-amber-300/20 bg-amber-300/10 px-4 py-4">
                            <div className="text-sm font-medium text-amber-100">
                              Orphan runtime sessions
                            </div>
                            <div className="mt-2 flex flex-col gap-2">
                              {diagnosticsQuery.data.orphan_runtime_sessions.map(
                                (sessionName) => (
                                  <div
                                    key={sessionName}
                                    className="text-sm text-amber-50"
                                  >
                                    {sessionName}
                                  </div>
                                ),
                              )}
                            </div>
                          </div>
                        ) : null}
                        {diagnosticsQuery.data?.stale_worktrees.length ? (
                          <div className="mt-4 rounded-2xl border border-amber-300/20 bg-amber-300/10 px-4 py-4">
                            <div className="text-sm font-medium text-amber-100">
                              Worktree recommendations
                            </div>
                            <div className="mt-2 flex flex-col gap-3">
                              {diagnosticsQuery.data.stale_worktrees.map(
                                (issue) => (
                                  <div
                                    key={issue.worktree_id}
                                    className="rounded-2xl border border-amber-300/15 bg-black/10 px-3 py-3"
                                  >
                                    <div className="text-sm font-medium text-amber-50">
                                      {issue.branch_name}
                                    </div>
                                    <div className="mt-1 text-xs text-amber-100">
                                      {issue.recommendation} ·{" "}
                                      {issue.reasons.join(", ")}
                                    </div>
                                  </div>
                                ),
                              )}
                            </div>
                          </div>
                        ) : null}
                      </SectionFrame>
                    ) : null}
                  </DiagnosticsScreen>

                  <ActivityScreen>
                    {activeSection === "activity" ? (
                      <SectionFrame className="px-5 py-5">
                        <SectionTitle>Recent events</SectionTitle>
                        <div className="mt-4 flex flex-col gap-3">
                          {dashboardQuery.data?.recent_events.map((event) => (
                            <div
                              key={event.id}
                              className="rounded-2xl border border-white/7 bg-white/3 px-4 py-3"
                            >
                              <div className="text-sm font-medium text-slate-100">
                                {formatEvent(event.event_type)}
                              </div>
                              <div className="mt-1 text-sm text-slate-500">
                                {event.actor_name} on {event.entity_type}
                              </div>
                            </div>
                          ))}
                          {!dashboardQuery.data?.recent_events.length ? (
                            <div className="text-sm text-slate-500">
                              Events will appear here as work is created and
                              updated.
                            </div>
                          ) : null}
                        </div>
                      </SectionFrame>
                    ) : null}
                  </ActivityScreen>
                </div>
              </div>
            </ProjectOverviewScreen>
          ) : null}
        </>
      }
      drawer={<></>}
    />
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

function DiagRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-2xl border border-white/7 bg-white/3 px-4 py-3">
      <div className="text-sm text-slate-400">{label}</div>
      <div className="max-w-[60%] break-all text-right text-sm text-slate-200">
        {value}
      </div>
    </div>
  );
}
