import {
  useDeferredValue,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  DndContext,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import * as Drawer from "vaul";
import { GitFork, MoreHorizontal, Play, Terminal, X } from "lucide-react";
import type { TaskSummary } from "@acp/sdk";
import { Button } from "@/components/primitives";
import {
  CollapsibleSection,
  ColumnShell,
  DialogFrame,
  Pill,
  SectionFrame,
  SectionTitle,
  StatusDot,
} from "@/components/ui";
import { useUIStore } from "@/store/ui";
import { AppShell } from "@/layout/AppShell";
import { SidebarNavigation } from "@/layout/SidebarNavigation";
import { AppHeader } from "@/layout/AppHeader";
import {
  BoardColumnHeader,
  DraggableTaskCard,
  DroppableBoardColumn,
} from "@/screens/ProjectBoardScreen";
import { TaskDetailScreen } from "@/screens/TaskDetailScreen";
import { SessionDetailScreen } from "@/screens/SessionDetailScreen";
import { ProjectOverviewScreen } from "@/screens/ProjectOverviewScreen";
import {
  useDashboardQuery,
  useDiagnosticsQuery,
  useEventsQuery,
  useLiveInvalidationSocket,
  useProjectDetailQuery,
  useProjectsQuery,
  useQuestionDetailQuery,
  useQuestionsQuery,
  useSearchQuery,
  useSessionTailQuery,
  useSessionTimelineQuery,
  useTaskDetailQuery,
} from "@/features/control-plane/hooks";
import type { EventRecord, SearchHit } from "@/lib/api";
import { useAppUrlState } from "@/app-shell/useAppUrlState";
import { useControlPlaneMutations } from "@/app-shell/useControlPlaneMutations";
import { sectionTitleByKey, type DetailSelection, type NavSection } from "@/app-shell/types";
import { HomeSectionContainer } from "@/features/navigation/containers/HomeSectionContainer";
import { SearchSectionContainer } from "@/features/navigation/containers/SearchSectionContainer";
import { ActivitySectionContainer } from "@/features/activity/containers/ActivitySectionContainer";
import { DiagnosticsSectionContainer } from "@/features/navigation/containers/DiagnosticsSectionContainer";
import { ProjectsSectionContainer } from "@/features/project/containers/ProjectsSectionContainer";
import { WaitingSectionContainer } from "@/features/project/containers/WaitingSectionContainer";
import { WorktreesSectionContainer } from "@/features/project/containers/WorktreesSectionContainer";
import { createControlPlaneInvalidation } from "@/features/control-plane/invalidation";
import { ProjectBootstrapWizard } from "@/components/project-bootstrap-wizard";
import { toDisplay } from "@/utils/display";

function formatEvent(eventType: string) {
  return toDisplay(eventType.replaceAll(".", "_"));
}

function summarizeEvent(event: EventRecord) {
  const payload = event.payload_json;
  const summaryFields = [
    payload.title,
    payload.name,
    payload.prompt,
    payload.summary,
    payload.local_path,
    payload.branch_name,
    payload.status,
  ];
  const summary = summaryFields.find(
    (value): value is string => typeof value === "string" && value.trim().length > 0,
  );
  if (summary) {
    return summary;
  }

  const addedColumnKeys = payload.added_column_keys;
  if (Array.isArray(addedColumnKeys) && addedColumnKeys.length > 0) {
    return `Added columns: ${addedColumnKeys.join(", ")}`;
  }

  return `${event.actor_name || "system"} updated ${event.entity_type}.`;
}

function formatSearchSnippet(hit: SearchHit) {
  if (hit.entity_type === "event") {
    return `Audit event matched the query. ${formatEvent(hit.title)} · ${hit.secondary ?? "system"}`;
  }
  return hit.snippet;
}


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
  const [draftCheckType] = useState("verification");
  const [draftCheckStatus, setDraftCheckStatus] = useState("pending");
  const [draftArtifactName, setDraftArtifactName] = useState("");
  const [draftArtifactType] = useState("log");
  const [draftArtifactUri, setDraftArtifactUri] = useState("");
  const [selectedDependencyTaskId, setSelectedDependencyTaskId] = useState("");
  const [draftSubtaskTitle, setDraftSubtaskTitle] = useState("");
  const [activeSection, setActiveSection] = useState<NavSection>("home");
  const [drawerSelection, setDrawerSelection] = useState<DetailSelection | null>(null);
  const [projectDialogOpen, setProjectDialogOpen] = useState(false);
  const [mobileTaskPanelOpen, setMobileTaskPanelOpen] = useState(false);
  const [openTaskSections, setOpenTaskSections] = useState<Record<string, boolean>>({});
  const [commentFocused, setCommentFocused] = useState(false);
  const deferredSearch = useDeferredValue(search);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
  );

  useAppUrlState({
    activeSection,
    selectedProjectId,
    inspectedTaskId,
    selectedSessionId,
    selectedQuestionId,
    drawerSelection,
    setActiveSection,
    setSelectedProjectId,
    setInspectedTaskId,
    setSelectedSessionId,
    setSelectedQuestionId,
    setDrawerSelection,
  });

  const dashboardQuery = useDashboardQuery();
  const diagnosticsQuery = useDiagnosticsQuery();
  const eventsQuery = useEventsQuery(selectedProjectId);
  const activityEventsQuery = useEventsQuery(null);
  const projectsQuery = useProjectsQuery();
  const searchQuery = useSearchQuery(deferredSearch);
  const invalidation = createControlPlaneInvalidation({ queryClient });

  useEffect(() => {
    if (!selectedProjectId && projectsQuery.data?.[0]) {
      setSelectedProjectId(projectsQuery.data[0].id);
    }
  }, [projectsQuery.data, selectedProjectId, setSelectedProjectId]);

  useLiveInvalidationSocket(invalidation.invalidateLiveUpdate);

  const projectDetailQuery = useProjectDetailQuery(selectedProjectId);
  const questionsQuery = useQuestionsQuery(selectedProjectId);

  useEffect(() => {
    setSelectedRepositoryId(null);
    setSelectedTaskId("");
    setSelectedSessionTaskId("");
    setSelectedSessionWorktreeId("");
    setSelectedSessionId(null);
    setSelectedQuestionId(null);
    setInspectedTaskId(null);
    setDrawerSelection(null);
  }, [selectedProjectId]);

  useEffect(() => {
    const repositories = projectDetailQuery.data?.repositories ?? [];
    if (!selectedRepositoryId && repositories[0]) {
      setSelectedRepositoryId(repositories[0].id);
    }
  }, [projectDetailQuery.data?.repositories, selectedRepositoryId]);

  useEffect(() => {
    const questions = questionsQuery.data ?? [];
    const isCurrentStillAvailable = questions.some(q => q.id === selectedQuestionId);
    if (!isCurrentStillAvailable && questions[0]) {
      setSelectedQuestionId(questions[0].id);
    }
  }, [questionsQuery.data, selectedQuestionId]);

  const {
    bootstrapPreviewMutation,
    bootstrapProjectMutation,
    createTaskMutation,
    createSubtaskMutation,
    patchTaskMutation,
    createRepositoryMutation,
    createWorktreeMutation,
    patchWorktreeMutation,
    createSessionMutation,
    createFollowUpSessionMutation,
    createQuestionMutation,
    answerQuestionMutation,
    addTaskCommentMutation,
    addTaskCheckMutation,
    addTaskArtifactMutation,
    addTaskDependencyMutation,
    cancelSessionMutation,
  } = useControlPlaneMutations({
    queryClient,
    selectedProjectId,
    inspectedTaskId,
    setSelectedProjectId,
    setActiveSection,
    setProjectDialogOpen,
    selectSession: (sessionId) => {
      setSelectedSessionId(sessionId);
      setDrawerSelection({ type: "session", id: sessionId });
    },
    selectQuestion: (questionId) => {
      setSelectedQuestionId(questionId);
      setDrawerSelection({ type: "question", id: questionId });
    },
    setSelectedRepositoryId,
    setInspectedTaskId,
    setSelectedSessionId,
    setDraftTaskTitle,
    setDraftSubtaskTitle,
    setDraftRepoPath,
    setDraftRepoName,
    setDraftWorktreeLabel,
    setSelectedTaskId,
    setDraftQuestionPrompt,
    setDraftQuestionReason,
    setDraftReplyBody,
    setDraftCommentBody,
    setDraftCheckSummary,
    setDraftArtifactName,
    setDraftArtifactUri,
    setSelectedDependencyTaskId,
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

  const projectNameById = useMemo(
    () => new Map((projectsQuery.data ?? []).map((project) => [project.id, project.name])),
    [projectsQuery.data],
  );

  const activityProjectOptions = useMemo(
    () =>
      (projectsQuery.data ?? []).map((project) => ({
        value: project.id,
        label: project.name,
      })),
    [projectsQuery.data],
  );

  const activityTaskOptions = useMemo(() => {
    const options = new Map<string, string>();
    for (const task of projectDetailQuery.data?.board.tasks ?? []) {
      options.set(task.id, task.title);
    }
    for (const event of activityEventsQuery.data ?? []) {
      const taskId =
        typeof event.payload_json.task_id === "string"
          ? event.payload_json.task_id
          : event.entity_type === "task"
            ? event.entity_id
            : null;
      if (taskId && !options.has(taskId)) {
        const payloadTitle = event.payload_json.title;
        options.set(
          taskId,
          typeof payloadTitle === "string" && payloadTitle.trim().length > 0
            ? payloadTitle
            : `Task ${taskId.slice(0, 8)}`,
        );
      }
    }
    return Array.from(options.entries()).map(([value, label]) => ({ value, label }));
  }, [activityEventsQuery.data, projectDetailQuery.data?.board.tasks]);

  const activitySessionOptions = useMemo(() => {
    const options = new Map<string, string>();
    for (const session of projectDetailQuery.data?.sessions ?? []) {
      options.set(session.id, session.session_name);
    }
    for (const event of activityEventsQuery.data ?? []) {
      const sessionId =
        typeof event.payload_json.session_id === "string"
          ? event.payload_json.session_id
          : event.entity_type === "session"
            ? event.entity_id
            : null;
      if (sessionId && !options.has(sessionId)) {
        const payloadSessionName = event.payload_json.session_name;
        options.set(
          sessionId,
          typeof payloadSessionName === "string" && payloadSessionName.trim().length > 0
            ? payloadSessionName
            : `Session ${sessionId.slice(0, 8)}`,
        );
      }
    }
    return Array.from(options.entries()).map(([value, label]) => ({ value, label }));
  }, [activityEventsQuery.data, projectDetailQuery.data?.sessions]);

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

  const sectionTitle = sectionTitleByKey[activeSection];

  const breadcrumbs = useMemo(() => {
    const crumbs = [sectionTitle];
    if (!["home", "search", "activity"].includes(activeSection) && projectDetailQuery.data?.project.name) {
      crumbs.push(projectDetailQuery.data.project.name);
    }
    if (activeSection === "projects" && taskDetailQuery.data?.title) {
      crumbs.push(taskDetailQuery.data.title);
    }
    if (activeSection === "sessions" && sessionTimelineQuery.data?.session.session_name) {
      crumbs.push(sessionTimelineQuery.data.session.session_name);
    }
    return crumbs;
  }, [
    activeSection,
    projectDetailQuery.data?.project.name,
    sectionTitle,
    sessionTimelineQuery.data?.session.session_name,
    taskDetailQuery.data?.title,
  ]);

  const selectTask = (taskId: string) => {
    setInspectedTaskId(taskId);
    setDrawerSelection({ type: "task", id: taskId });
    setMobileTaskPanelOpen(true);
  };

  const selectSession = (sessionId: string) => {
    setSelectedSessionId(sessionId);
    setDrawerSelection({ type: "session", id: sessionId });
  };

  const selectQuestion = (questionId: string) => {
    setSelectedQuestionId(questionId);
    setDrawerSelection({ type: "question", id: questionId });
  };

  const selectWorktree = (worktreeId: string) => {
    setDrawerSelection({ type: "worktree", id: worktreeId });
  };

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

  const taskSessionCount = taskDetailQuery.data
    ? projectDetailQuery.data?.sessions.filter((session) => session.task_id === taskDetailQuery.data?.id).length ?? 0
    : 0;

  const taskPanelSections = {
    subtasks: subtasksByParent.get(taskDetailQuery.data?.id ?? "") ?? [],
    dependencies: taskDetailQuery.data?.dependencies ?? [],
    checks: taskDetailQuery.data?.checks ?? [],
    artifacts: taskDetailQuery.data?.artifacts ?? [],
  };

  const linkedTaskSessions = useMemo(
    () =>
      taskDetailQuery.data
        ? (projectDetailQuery.data?.sessions ?? []).filter(
            (session) => session.task_id === taskDetailQuery.data?.id,
          )
        : [],
    [projectDetailQuery.data?.sessions, taskDetailQuery.data],
  );

  const toggleTaskSection = (key: string) => {
    setOpenTaskSections((current) => ({ ...current, [key]: !current[key] }));
  };

  const closeTaskDetail = () => {
    setDrawerSelection(null);
    setInspectedTaskId(null);
    setMobileTaskPanelOpen(false);
  };

  const isProjectScopedSection =
    activeSection === "projects" ||
    activeSection === "sessions" ||
    activeSection === "worktrees";

  const projectWorkspaceTitle =
    projectDetailQuery.data?.project.name ?? "Projects";

  const projectWorkspaceTabs: Array<{
    key: Extract<NavSection, "projects" | "sessions" | "worktrees">;
    label: string;
  }> = [
    { key: "projects", label: "Board" },
    { key: "sessions", label: "Sessions" },
    { key: "worktrees", label: "Worktrees" },
  ];

  return (
    <AppShell
      sidebar={
        <SidebarNavigation
          activeSection={activeSection}
          setActiveSection={setActiveSection}
        />
      }
      header={
        <AppHeader
          breadcrumbs={breadcrumbs}
          search={search}
          setSearch={setSearch}
          onSearchActivate={() => setActiveSection("search")}
        />
      }
      main={
        <>
          {activeSection === "home" ? (
            <div className="page-frame p-4">
              <HomeSectionContainer
                environment={diagnosticsQuery.data?.environment ?? "development"}
                dashboard={dashboardQuery.data}
                events={eventsQuery.data ?? []}
                projectName={projectDetailQuery.data?.project.name ?? "the control plane"}
                onOpenQuestion={(questionId, projectId) => {
                  setSelectedProjectId(projectId);
                  selectQuestion(questionId);
                  setActiveSection("waiting");
                }}
                onOpenTask={(taskId, projectId) => {
                  setSelectedProjectId(projectId);
                  selectTask(taskId);
                  setActiveSection("projects");
                }}
                onOpenSession={(sessionId, projectId) => {
                  setSelectedProjectId(projectId);
                  selectSession(sessionId);
                  setActiveSection("sessions");
                }}
                formatEvent={formatEvent}
                summarizeEvent={summarizeEvent}
              />
            </div>
          ) : null}
          {activeSection === "search" ? (
            <div className="page-frame p-4">
              <SearchSectionContainer
                deferredSearch={deferredSearch}
                hits={searchQuery.data?.hits ?? []}
                formatSearchSnippet={formatSearchSnippet}
                projectNameById={projectNameById}
                onSelectHit={(hit) => {
                  if (hit.entity_type === "project") {
                    setSelectedProjectId(hit.entity_id);
                    setActiveSection("projects");
                  } else if (hit.entity_type === "task") {
                    selectTask(hit.entity_id);
                    setActiveSection("projects");
                  } else if (hit.entity_type === "waiting_question") {
                    selectQuestion(hit.entity_id);
                    setActiveSection("waiting");
                  } else if (hit.entity_type === "session") {
                    selectSession(hit.entity_id);
                    setActiveSection("sessions");
                  } else if (hit.entity_type === "event") {
                    setActiveSection("activity");
                  }
                  if (hit.project_id && hit.entity_type !== "project") {
                    setSelectedProjectId(hit.project_id);
                  }
                }}
              />
            </div>
          ) : null}
          {activeSection === "activity" ? (
            <div className="page-frame p-4">
              <ActivitySectionContainer
                events={activityEventsQuery.data ?? []}
                loading={activityEventsQuery.isLoading}
                error={activityEventsQuery.error instanceof Error ? activityEventsQuery.error.message : null}
                projectOptions={activityProjectOptions}
                taskOptions={activityTaskOptions}
                sessionOptions={activitySessionOptions}
              />
            </div>
          ) : null}
          {isProjectScopedSection ? (
            <ProjectOverviewScreen>
              <div className="min-w-0">
                <ProjectsSectionContainer active={isProjectScopedSection}>
                  <div className="project-workspace">
                    <aside className="project-switcher">
                      <div className="flex items-center justify-between gap-2">
                        <div className="text-sm font-medium text-[color:var(--text)]">
                          Projects
                        </div>
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
                            onClick={() => {
                              setSelectedProjectId(project.id);
                              setActiveSection("projects");
                            }}
                            className={[
                              "flex h-9 w-full items-center gap-2 rounded px-3 text-left text-sm",
                              selectedProjectId === project.id
                                ? "bg-[rgba(37,99,235,0.08)] text-[color:var(--accent)]"
                                : "text-[color:var(--text)] hover:bg-black/4",
                            ].join(" ")}
                          >
                            <StatusDot status={selectedProjectId === project.id ? "ready" : "backlog"} />
                            <span className="truncate">{project.name}</span>
                          </button>
                        ))}
                      </div>
                    </aside>
                    <div className="board-region">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <SectionTitle>{projectWorkspaceTitle}</SectionTitle>
                        <div className="inline-flex flex-wrap items-center gap-1 rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)] p-1">
                          {projectWorkspaceTabs.map((tab) => (
                            <button
                              key={tab.key}
                              type="button"
                              className={[
                                "rounded-[4px] px-3 py-1.5 text-sm",
                                activeSection === tab.key
                                  ? "bg-[rgba(37,99,235,0.08)] text-[color:var(--accent)]"
                                  : "text-[color:var(--text-muted)] hover:bg-black/4 hover:text-[color:var(--text)]",
                              ].join(" ")}
                              onClick={() => setActiveSection(tab.key)}
                            >
                              {tab.label}
                            </button>
                          ))}
                        </div>
                      </div>

                      {activeSection === "projects" ? (
                        <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
                          <div className="board-scroll mt-4 scrollbar-thin">
                            {projectDetailQuery.data?.board.columns.map((column) => (
                              <DroppableBoardColumn key={column.id} columnId={column.id}>
                                <ColumnShell className="flex flex-col gap-3">
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
                                        task={task}
                                        subtasks={subtasksByParent.get(task.id) ?? []}
                                        selected={inspectedTaskId === task.id}
                                        metadata={{
                                          sessions: taskCardMetadata.sessionsByTask.get(task.id) ?? 0,
                                          worktree: taskCardMetadata.worktreeByTask.has(task.id),
                                          checks: 0,
                                          artifacts: 0,
                                          assignees: (projectDetailQuery.data?.sessions ?? [])
                                            .filter((session) => session.task_id === task.id)
                                            .map((session) => session.profile),
                                        }}
                                        onInspect={() => selectTask(task.id)}
                                      />
                                    ))}
                                  </div>
                                  <div className="space-y-2">
                                    <input
                                      value={draftTaskTitle}
                                      onChange={(event) => setDraftTaskTitle(event.target.value)}
                                      placeholder={column.key === "backlog" ? "Add task" : "Add task title"}
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
                                            })
                                          : null
                                      }
                                      disabled={!draftTaskTitle.trim() || createTaskMutation.isPending}
                                    >
                                      + Add task
                                    </button>
                                  </div>
                                </ColumnShell>
                              </DroppableBoardColumn>
                            ))}
                          </div>
                        </DndContext>
                      ) : null}

                      {activeSection === "worktrees" ? (
                        <div className="mt-4">
                          <WorktreesSectionContainer
                            active={activeSection === "worktrees"}
                            repositories={projectDetailQuery.data?.repositories ?? []}
                            worktrees={projectDetailQuery.data?.worktrees ?? []}
                            tasks={topLevelTasks}
                            sessions={projectDetailQuery.data?.sessions ?? []}
                            events={eventsQuery.data ?? []}
                            selectedWorktreeId={drawerSelection?.type === "worktree" ? drawerSelection.id : null}
                            onSelectWorktree={selectWorktree}
                            loading={projectDetailQuery.isLoading || eventsQuery.isLoading}
                            error={
                              projectDetailQuery.error instanceof Error
                                ? projectDetailQuery.error.message
                                : eventsQuery.error instanceof Error
                                  ? eventsQuery.error.message
                                  : null
                            }
                            onLock={(worktreeId) =>
                              patchWorktreeMutation.mutate({
                                worktreeId,
                                status: "locked",
                              })
                            }
                            onArchive={(worktreeId) =>
                              patchWorktreeMutation.mutate({
                                worktreeId,
                                status: "archived",
                              })
                            }
                            onPrune={(worktreeId) =>
                              patchWorktreeMutation.mutate({
                                worktreeId,
                                status: "pruned",
                              })
                            }
                            controls={
                              selectedProjectId ? (
                                <div className="grid gap-4 lg:grid-cols-2">
                                  <div className="rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
                                    <div className="text-sm font-medium text-[color:var(--text)]">Attach repository</div>
                                    <input
                                      value={draftRepoPath}
                                      onChange={(event) => setDraftRepoPath(event.target.value)}
                                      placeholder="/absolute/path/to/repo"
                                      className="mt-3 w-full rounded-[4px] border border-[color:var(--border)] px-3 py-3 text-sm outline-none"
                                    />
                                    <input
                                      value={draftRepoName}
                                      onChange={(event) => setDraftRepoName(event.target.value)}
                                      placeholder="Optional display name"
                                      className="mt-3 w-full rounded-[4px] border border-[color:var(--border)] px-3 py-3 text-sm outline-none"
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
                                      className="btn-primary mt-3"
                                    >
                                      Attach repo
                                    </button>
                                  </div>

                                  <div className="rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
                                    <div className="text-sm font-medium text-[color:var(--text)]">Allocate worktree</div>
                                    <select
                                      value={selectedRepositoryId ?? ""}
                                      onChange={(event) => setSelectedRepositoryId(event.target.value || null)}
                                      className="mt-3 w-full rounded-[4px] border border-[color:var(--border)] px-3 py-3 text-sm outline-none"
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
                                      className="mt-3 w-full rounded-[4px] border border-[color:var(--border)] px-3 py-3 text-sm outline-none"
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
                                      className="mt-3 w-full rounded-[4px] border border-[color:var(--border)] px-3 py-3 text-sm outline-none"
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
                                      className="btn-secondary mt-3"
                                    >
                                      Allocate
                                    </button>
                                  </div>
                                </div>
                              ) : null
                            }
                          />
                        </div>
                      ) : null}

                      {activeSection === "sessions" ? (
                        <div className="mt-4">
                          <SectionFrame className="px-5 py-5">
                            <SectionTitle>Session Runtime</SectionTitle>
                            <div className="mt-4 flex flex-col gap-3">
                              {projectDetailQuery.data?.sessions.map((session) => (
                                <button
                                  key={session.id}
                                  onClick={() => selectSession(session.id)}
                                  className={[
                                    "rounded-[6px] border px-4 py-4 text-left",
                                    selectedSessionId === session.id
                                      ? "border-[color:var(--accent)] bg-[rgba(37,99,235,0.08)]"
                                      : "border-[color:var(--border)] bg-[color:var(--surface)]",
                                  ].join(" ")}
                                >
                                  <div className="flex items-center justify-between gap-3">
                                    <div className="flex items-center gap-2 text-sm font-semibold text-[color:var(--text)]">
                                      <Terminal className="h-4 w-4 text-[color:var(--text-muted)]" />
                                      {toDisplay(session.profile)}
                                    </div>
                                    <Pill>{toDisplay(session.status)}</Pill>
                                  </div>
                                  <div className="mt-2 text-xs text-[color:var(--text-muted)]">
                                    {session.session_name}
                                  </div>
                                </button>
                              ))}
                              {!projectDetailQuery.data?.sessions.length ? (
                                <div className="text-sm text-[color:var(--text-muted)]">
                                  No agent sessions yet.
                                </div>
                              ) : null}
                            </div>

                            {selectedProjectId ? (
                              <div className="mt-5 rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
                                <div className="text-sm font-medium text-[color:var(--text)]">
                                  Spawn session
                                </div>
                                <select
                                  value={selectedSessionTaskId}
                                  onChange={(event) =>
                                    setSelectedSessionTaskId(event.target.value)
                                  }
                                  className="mt-3 w-full rounded-[4px] border border-[color:var(--border)] px-3 py-3 text-sm outline-none"
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
                                  className="mt-3 w-full rounded-[4px] border border-[color:var(--border)] px-3 py-3 text-sm outline-none"
                                >
                                  <option value="">No worktree</option>
                                  {(projectDetailQuery.data?.worktrees ?? [])
                                    .filter((worktree) => worktree.status !== "pruned")
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
                                  className="mt-3 w-full rounded-[4px] border border-[color:var(--border)] px-3 py-3 text-sm outline-none"
                                >
                                  {["executor", "reviewer", "verifier", "research", "docs"].map((profile) => (
                                    <option key={profile} value={profile}>
                                      {toDisplay(profile)}
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
                                  className="btn-primary mt-3 inline-flex items-center gap-2"
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
                                          className="btn-secondary border-rose-200 text-rose-600"
                                        >
                                          Cancel session
                                        </button>
                                      ) : null}
                                      {sessionTimelineQuery.data ? (
                                        <div className="flex flex-wrap gap-2">
                                          {[
                                            {
                                              label: "Retry",
                                              profile: sessionTimelineQuery.data.session.profile,
                                              followUpType: "retry" as const,
                                            },
                                            {
                                              label: "Review",
                                              profile: "reviewer",
                                              followUpType: "review" as const,
                                            },
                                            {
                                              label: "Verify",
                                              profile: "verifier",
                                              followUpType: "verify" as const,
                                            },
                                            {
                                              label: "Handoff",
                                              profile: "executor",
                                              followUpType: "handoff" as const,
                                            },
                                          ].map((followUp) => (
                                            <button
                                              key={followUp.label}
                                              onClick={() =>
                                                createFollowUpSessionMutation.mutate({
                                                  sessionId: sessionTimelineQuery.data.session.id,
                                                  profile: followUp.profile,
                                                  followUpType: followUp.followUpType,
                                                })
                                              }
                                              disabled={createFollowUpSessionMutation.isPending}
                                              className="btn-secondary inline-flex items-center gap-2 !h-8 text-xs"
                                            >
                                              <GitFork className="h-3.5 w-3.5" />
                                              {followUp.label}
                                            </button>
                                          ))}
                                        </div>
                                      ) : null}
                                    </>
                                  }
                                  outputPanel={
                                    sessionTailQuery.data ? (
                                      <pre className="max-h-72 overflow-auto rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface-2)] p-3 text-xs leading-5 text-[color:var(--text)]">
                                        {sessionTailQuery.data.lines.join("\n")}
                                      </pre>
                                    ) : (
                                      <div className="text-sm text-[color:var(--text-muted)]">
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
                                                className="rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface-2)] px-3 py-3"
                                              >
                                                <div className="text-xs text-[color:var(--text-muted)]">
                                                  {toDisplay(message.source)}
                                                </div>
                                                <div className="mt-2 text-sm text-[color:var(--text)]">
                                                  {message.body}
                                                </div>
                                              </div>
                                            ))}
                                          {!sessionTimelineQuery.data.messages.length ? (
                                            <div className="text-sm text-[color:var(--text-muted)]">
                                              No structured session messages yet.
                                            </div>
                                          ) : null}
                                        </div>
                                      ) : (
                                        <div className="text-sm text-[color:var(--text-muted)]">
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
                                                className="rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface-2)] px-3 py-3"
                                              >
                                                <div className="flex items-center justify-between gap-2">
                                                  <div className="text-sm text-[color:var(--text)]">
                                                    {toDisplay(check.check_type)}
                                                  </div>
                                                  <Pill>{toDisplay(check.status)}</Pill>
                                                </div>
                                                <div className="mt-2 text-sm text-[color:var(--text-muted)]">
                                                  {check.summary}
                                                </div>
                                              </div>
                                            ))}
                                          {!selectedSessionTaskDetailQuery.data.checks.length ? (
                                            <div className="text-sm text-[color:var(--text-muted)]">
                                              No task checks emitted yet.
                                            </div>
                                          ) : null}
                                        </div>
                                      ) : (
                                        <div className="text-sm text-[color:var(--text-muted)]">
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
                                                className="rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface-2)] px-3 py-3"
                                              >
                                                <div className="text-sm font-medium text-[color:var(--text)]">
                                                  {question.prompt}
                                                </div>
                                                <div className="mt-2 text-sm text-[color:var(--text-muted)]">
                                                  {question.blocked_reason ??
                                                    "Waiting on operator input."}
                                                </div>
                                              </div>
                                            ))}
                                          {!sessionTimelineQuery.data.waiting_questions.length ? (
                                            <div className="text-sm text-[color:var(--text-muted)]">
                                              No waiting items linked to this session.
                                            </div>
                                          ) : null}
                                        </div>
                                      ) : (
                                        <div className="text-sm text-[color:var(--text-muted)]">
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
                                                className="rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface-2)] px-3 py-3"
                                              >
                                                <div className="text-sm font-medium text-[color:var(--text)]">
                                                  {formatEvent(event.event_type)}
                                                </div>
                                                <div className="mt-2 text-xs text-[color:var(--text-muted)]">
                                                  {new Date(
                                                    event.created_at,
                                                  ).toLocaleString()}
                                                </div>
                                              </div>
                                            ))}
                                          {!sessionTimelineQuery.data.events.length ? (
                                            <div className="text-sm text-[color:var(--text-muted)]">
                                              No session events recorded yet.
                                            </div>
                                          ) : null}
                                        </div>
                                      ) : (
                                        <div className="text-sm text-[color:var(--text-muted)]">
                                          No selected session.
                                        </div>
                                      ),
                                    },
                                  ]}
                                />
                              </div>
                            ) : null}

                            <div className="mt-5 rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)] p-4">
                              <div className="text-sm font-medium text-[color:var(--text)]">
                                Open waiting question
                              </div>
                              <select
                                value={selectedSessionTaskId}
                                onChange={(event) =>
                                  setSelectedSessionTaskId(event.target.value)
                                }
                                className="mt-3 w-full rounded-[4px] border border-[color:var(--border)] px-3 py-3 text-sm outline-none"
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
                                className="mt-3 w-full rounded-[4px] border border-[color:var(--border)] px-3 py-3 text-sm outline-none"
                              >
                                <option value="">Optional linked session</option>
                                {(projectDetailQuery.data?.sessions ?? []).map(
                                  (session) => (
                                    <option key={session.id} value={session.id}>
                                      {toDisplay(session.profile)} · {session.session_name}
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
                                className="mt-3 min-h-24 w-full rounded-[4px] border border-[color:var(--border)] px-3 py-3 text-sm outline-none"
                              />
                              <input
                                value={draftQuestionReason}
                                onChange={(event) =>
                                  setDraftQuestionReason(event.target.value)
                                }
                                placeholder="Why is work blocked?"
                                className="mt-3 w-full rounded-[4px] border border-[color:var(--border)] px-3 py-3 text-sm outline-none"
                              />
                              <select
                                value={draftQuestionUrgency}
                                onChange={(event) =>
                                  setDraftQuestionUrgency(event.target.value)
                                }
                                className="mt-3 w-full rounded-[4px] border border-[color:var(--border)] px-3 py-3 text-sm outline-none"
                              >
                                {["low", "medium", "high", "urgent"].map((urgency) => (
                                  <option key={urgency} value={urgency}>
                                    {toDisplay(urgency)}
                                  </option>
                                ))}
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
                                className="btn-primary mt-3"
                              >
                                Open question
                              </button>
                            </div>
                          </SectionFrame>
                        </div>
                      ) : null}
                    </div>
                  </div>
                </ProjectsSectionContainer>
              </div>
            </ProjectOverviewScreen>
          ) : null}
          {activeSection !== "home" &&
          activeSection !== "search" &&
          activeSection !== "activity" &&
          !isProjectScopedSection ? (
            <ProjectOverviewScreen>
              <div className="min-w-0 flex flex-col gap-6">
                <WaitingSectionContainer
                  active={activeSection === "waiting"}
                  questions={questionsQuery.data ?? []}
                  selectedQuestionId={selectedQuestionId}
                  questionDetail={questionDetailQuery.data}
                  sessions={projectDetailQuery.data?.sessions ?? []}
                  tasks={projectDetailQuery.data?.board.tasks ?? []}
                  projectLabel={
                    projectDetailQuery.data?.project.name ??
                    selectedProjectId?.slice(0, 8) ??
                    "Project"
                  }
                  draftReplyBody={draftReplyBody}
                  onDraftReplyBodyChange={setDraftReplyBody}
                  onSelectQuestion={selectQuestion}
                  onSendReply={(questionId, body) =>
                    answerQuestionMutation.mutate({ questionId, body })
                  }
                  isSendingReply={answerQuestionMutation.isPending}
                  onOpenProject={() => setActiveSection("projects")}
                  onOpenSession={(sessionId) => {
                    selectSession(sessionId);
                    setActiveSection("sessions");
                  }}
                  onOpenTask={(taskId) => {
                    selectTask(taskId);
                    setActiveSection("projects");
                  }}
                />

                {activeSection === "diagnostics" ? (
                  <DiagnosticsSectionContainer diagnostics={diagnosticsQuery.data} />
                ) : null}
              </div>
            </ProjectOverviewScreen>
          ) : null}
          <DialogFrame
            open={projectDialogOpen}
            onOpenChange={setProjectDialogOpen}
            title="New Project"
          >
            <ProjectBootstrapWizard
              isPreviewPending={bootstrapPreviewMutation.isPending}
              isConfirmPending={bootstrapProjectMutation.isPending}
              errorMessage={
                bootstrapProjectMutation.error instanceof Error
                  ? bootstrapProjectMutation.error.message
                  : bootstrapPreviewMutation.error instanceof Error
                    ? bootstrapPreviewMutation.error.message
                    : undefined
              }
              result={bootstrapProjectMutation.data as never}
              onPreview={bootstrapPreviewMutation.mutateAsync}
              onConfirm={bootstrapProjectMutation.mutateAsync}
            />
          </DialogFrame>
        </>
      }
      drawer={
        activeSection === "projects" && taskDetailQuery.data ? (
          <>
            <div className="detail-panel max-lg:hidden">
              <TaskDetailScreen
                title={
                  <div className="flex items-center justify-between gap-3">
                    <button
                      type="button"
                      className="btn-ghost !px-0"
                      onClick={closeTaskDetail}
                    >
                      <X className="h-4 w-4" />
                      Back to board
                    </button>
                    <DropdownMenu.Root>
                      <DropdownMenu.Trigger asChild>
                        <button
                          type="button"
                          className="btn-ghost"
                          aria-label="Task actions"
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </button>
                      </DropdownMenu.Trigger>
                      <DropdownMenu.Content className="rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)] p-1 shadow-[var(--shadow-panel)]">
                        {taskDetailQuery.data.workflow_state !== "cancelled" ? (
                          <DropdownMenu.Item
                            className="rounded px-2 py-1.5 text-sm outline-none"
                            onSelect={() =>
                              patchTaskMutation.mutate({
                                taskId: taskDetailQuery.data.id,
                                workflowState: "cancelled",
                              })
                            }
                          >
                            Cancel task
                          </DropdownMenu.Item>
                        ) : (
                          <DropdownMenu.Item
                            className="rounded px-2 py-1.5 text-sm outline-none"
                            onSelect={() =>
                              patchTaskMutation.mutate({
                                taskId: taskDetailQuery.data.id,
                                workflowState: "backlog",
                              })
                            }
                          >
                            Reopen to backlog
                          </DropdownMenu.Item>
                        )}
                      </DropdownMenu.Content>
                    </DropdownMenu.Root>
                  </div>
                }
                actions={
                  <div className="space-y-3">
                    <input
                      value={taskDetailQuery.data.title}
                      readOnly
                      className="w-full border-0 bg-transparent p-0 text-xl font-semibold outline-none"
                    />
                    <div className="flex flex-wrap gap-2">
                      <DropdownMenu.Root>
                        <DropdownMenu.Trigger asChild>
                          <button type="button" className="btn-secondary">
                            <StatusDot status={taskDetailQuery.data.workflow_state} />
                            {toDisplay(taskDetailQuery.data.workflow_state)}
                          </button>
                        </DropdownMenu.Trigger>
                        <DropdownMenu.Content className="rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)] p-1 shadow-[var(--shadow-panel)]">
                          {(projectDetailQuery.data?.board.columns ?? []).map((column) => (
                            <DropdownMenu.Item
                              key={column.id}
                              className="flex items-center gap-2 rounded px-2 py-1.5 text-sm outline-none"
                              onSelect={() =>
                                patchTaskMutation.mutate({
                                  taskId: taskDetailQuery.data.id,
                                  boardColumnId: column.id,
                                })
                              }
                            >
                              <StatusDot status={column.key} />
                              {toDisplay(column.name)}
                            </DropdownMenu.Item>
                          ))}
                        </DropdownMenu.Content>
                      </DropdownMenu.Root>
                      <div className="inline-flex h-8 items-center rounded-[4px] border border-[color:var(--border)] bg-[color:var(--surface)] px-3 text-[13px] font-medium text-[color:var(--text)]">
                        {taskDetailQuery.data.priority
                          ? toDisplay(taskDetailQuery.data.priority)
                          : "Priority"}
                      </div>
                      <button
                        type="button"
                        onClick={() =>
                          createSessionMutation.mutate({
                            task_id: taskDetailQuery.data.id,
                            profile: "executor",
                          })
                        }
                        disabled={createSessionMutation.isPending}
                        className="btn-primary inline-flex h-8 items-center gap-1.5 rounded-[4px] px-3 text-[13px] font-medium"
                      >
                        <Play className="h-3.5 w-3.5 fill-current" />
                        Spawn Agent
                      </button>
                      <DropdownMenu.Root>
                        <DropdownMenu.Trigger asChild>
                          <button type="button" className="btn-secondary">
                            Session {taskSessionCount > 0 ? `(${taskSessionCount})` : ""}
                          </button>
                        </DropdownMenu.Trigger>
                        <DropdownMenu.Content className="rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)] p-1 shadow-[var(--shadow-panel)]">
                          {linkedTaskSessions.length ? (
                            linkedTaskSessions.map((session) => (
                              <DropdownMenu.Item
                                key={session.id}
                                className="flex items-center gap-2 rounded px-2 py-1.5 text-sm outline-none"
                                onSelect={() => {
                                  selectSession(session.id);
                                  setActiveSection("sessions");
                                  closeTaskDetail();
                                }}
                              >
                                <StatusDot status={session.status} />
                                {toDisplay(session.profile)} · {session.session_name}
                              </DropdownMenu.Item>
                            ))
                          ) : (
                            <DropdownMenu.Item
                              disabled
                              className="rounded px-2 py-1.5 text-sm text-[color:var(--text-muted)] outline-none"
                            >
                              No linked sessions
                            </DropdownMenu.Item>
                          )}
                        </DropdownMenu.Content>
                      </DropdownMenu.Root>
                    </div>
                  </div>
                }
                contextPanel={
                  <div className="space-y-4">
                    <div>
                      <div className="section-label">Description</div>
                      <textarea
                        value={taskDetailQuery.data.description ?? ""}
                        onChange={(event) =>
                          patchTaskMutation.mutate({
                            taskId: taskDetailQuery.data.id,
                            description: event.target.value,
                          })
                        }
                        className="mt-2 min-h-28 w-full rounded-[4px] border border-[color:var(--border)] px-3 py-2"
                      />
                    </div>
                    <CollapsibleSection
                      title="Subtasks"
                      count={taskPanelSections.subtasks.length}
                      open={Boolean(openTaskSections.subtasks)}
                      onToggle={() => toggleTaskSection("subtasks")}
                    >
                      {taskPanelSections.subtasks.map((subtask) => (
                        <button key={subtask.id} type="button" className="card-surface w-full p-2 text-left" onClick={() => selectTask(subtask.id)}>
                          <div className="flex items-center justify-between gap-2">
                            <span>{subtask.title}</span>
                            <Pill>{toDisplay(subtask.workflow_state)}</Pill>
                          </div>
                        </button>
                      ))}
                      <input
                        value={draftSubtaskTitle}
                        onChange={(event) => setDraftSubtaskTitle(event.target.value)}
                        placeholder="+ Add item"
                        className="w-full rounded-[4px] border border-[color:var(--border)] px-3 py-2"
                      />
                      <Button
                        variant="ghost"
                        onClick={() =>
                          createSubtaskMutation.mutate({
                            project_id: taskDetailQuery.data.project_id,
                            title: draftSubtaskTitle,
                            parent_task_id: taskDetailQuery.data.id,
                            board_column_key: "backlog",
                          })
                        }
                        disabled={!draftSubtaskTitle.trim()}
                      >
                        + Add item
                      </Button>
                    </CollapsibleSection>
                    <CollapsibleSection
                      title="Dependencies"
                      count={taskPanelSections.dependencies.length}
                      open={Boolean(openTaskSections.dependencies)}
                      onToggle={() => toggleTaskSection("dependencies")}
                    >
                      {taskPanelSections.dependencies.map((dependency) => (
                        <div key={dependency.id} className="card-surface p-2 text-sm">
                          {projectDetailQuery.data?.board.tasks.find((candidate) => candidate.id === dependency.depends_on_task_id)?.title ??
                            dependency.depends_on_task_id}
                        </div>
                      ))}
                      <select
                        value={selectedDependencyTaskId}
                        onChange={(event) => setSelectedDependencyTaskId(event.target.value)}
                        className="w-full rounded-[4px] border border-[color:var(--border)] px-3 py-2"
                      >
                        <option value="">Select blocker task</option>
                        {(projectDetailQuery.data?.board.tasks ?? [])
                          .filter((candidate) => candidate.id !== taskDetailQuery.data.id)
                          .map((candidate) => (
                            <option key={candidate.id} value={candidate.id}>
                              {candidate.title}
                            </option>
                          ))}
                      </select>
                      <Button
                        variant="ghost"
                        onClick={() =>
                          addTaskDependencyMutation.mutate({
                            taskId: taskDetailQuery.data.id,
                            dependsOnTaskId: selectedDependencyTaskId,
                          })
                        }
                        disabled={!selectedDependencyTaskId}
                      >
                        + Add item
                      </Button>
                    </CollapsibleSection>
                    <CollapsibleSection
                      title="Checks"
                      count={taskPanelSections.checks.length}
                      open={Boolean(openTaskSections.checks)}
                      onToggle={() => toggleTaskSection("checks")}
                    >
                      {taskPanelSections.checks.map((check) => (
                        <div key={check.id} className="card-surface p-2 text-sm">
                          <div className="font-medium">{toDisplay(check.check_type)}</div>
                          <div className="text-[color:var(--text-muted)]">{check.summary}</div>
                        </div>
                      ))}
                      <select
                        value={draftCheckStatus}
                        onChange={(event) => setDraftCheckStatus(event.target.value)}
                        className="w-full rounded-[4px] border border-[color:var(--border)] px-3 py-2 text-sm"
                      >
                        {["pending", "passed", "failed", "warning"].map((status) => (
                          <option key={status} value={status}>
                            {toDisplay(status)}
                          </option>
                        ))}
                      </select>
                      <input
                        value={draftCheckSummary}
                        onChange={(event) => setDraftCheckSummary(event.target.value)}
                        placeholder="+ Add item"
                        className="w-full rounded-[4px] border border-[color:var(--border)] px-3 py-2"
                      />
                      <Button
                        variant="ghost"
                        onClick={() =>
                          addTaskCheckMutation.mutate({
                            taskId: taskDetailQuery.data.id,
                            checkType: draftCheckType,
                            status: draftCheckStatus,
                            summary: draftCheckSummary,
                          })
                        }
                        disabled={!draftCheckSummary.trim()}
                      >
                        + Add item
                      </Button>
                    </CollapsibleSection>
                    <CollapsibleSection
                      title="Artifacts"
                      count={taskPanelSections.artifacts.length}
                      open={Boolean(openTaskSections.artifacts)}
                      onToggle={() => toggleTaskSection("artifacts")}
                    >
                      {taskPanelSections.artifacts.map((artifact) => (
                        <div key={artifact.id} className="card-surface p-2 text-sm">
                          <div className="font-medium">{artifact.name}</div>
                          <div className="break-all text-[color:var(--text-muted)]">{artifact.uri}</div>
                        </div>
                      ))}
                      <input
                        value={draftArtifactName}
                        onChange={(event) => setDraftArtifactName(event.target.value)}
                        placeholder="Artifact name"
                        className="w-full rounded-[4px] border border-[color:var(--border)] px-3 py-2"
                      />
                      <input
                        value={draftArtifactUri}
                        onChange={(event) => setDraftArtifactUri(event.target.value)}
                        placeholder="+ Add item"
                        className="w-full rounded-[4px] border border-[color:var(--border)] px-3 py-2"
                      />
                      <Button
                        variant="ghost"
                        onClick={() =>
                          addTaskArtifactMutation.mutate({
                            taskId: taskDetailQuery.data.id,
                            artifactType: draftArtifactType,
                            name: draftArtifactName,
                            uri: draftArtifactUri,
                          })
                        }
                        disabled={!draftArtifactName.trim() || !draftArtifactUri.trim()}
                      >
                        + Add item
                      </Button>
                    </CollapsibleSection>
                    <div className="pt-2">
                      <div className="section-label">Comments</div>
                      <textarea
                        value={draftCommentBody}
                        onFocus={() => setCommentFocused(true)}
                        onBlur={() => {
                          if (!draftCommentBody.trim()) {
                            setCommentFocused(false);
                          }
                        }}
                        onChange={(event) => setDraftCommentBody(event.target.value)}
                        placeholder="Leave a comment…"
                        className="mt-2 min-h-9 w-full rounded-[4px] border border-[color:var(--border)] px-3 py-2"
                      />
                      {commentFocused ? (
                        <div className="mt-2 flex justify-end">
                          <Button
                            variant="primary"
                            onClick={() =>
                              addTaskCommentMutation.mutate({
                                taskId: taskDetailQuery.data.id,
                                body: draftCommentBody,
                              })
                            }
                            disabled={!draftCommentBody.trim()}
                          >
                            Post
                          </Button>
                        </div>
                      ) : null}
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
