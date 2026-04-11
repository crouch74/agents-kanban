import {
  useDeferredValue,
  useEffect,
  useMemo,
  useRef,
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
import { GitFork, Play, Terminal } from "lucide-react";
import type { TaskSummary } from "@acp/sdk";
import { DetailDrawer, type DetailDrawerSection } from "@/components/DetailDrawer";
import { ColumnShell, Pill, SectionFrame, SectionTitle } from "@/components/ui";
import { useUIStore } from "@/store/ui";
import { AppShell } from "@/layout/AppShell";
import { SidebarNavigation } from "@/layout/SidebarNavigation";
import { AppHeader } from "@/layout/AppHeader";
import {
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

function formatEvent(eventType: string) {
  return eventType.replaceAll(".", " ").replaceAll("_", " ");
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
  const taskTitleInputRef = useRef<HTMLInputElement | null>(null);
  const bootstrapWizardRef = useRef<HTMLDivElement | null>(null);
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
  const [drawerSelection, setDrawerSelection] = useState<DetailSelection | null>(null);
  const [quickCreateOpen, setQuickCreateOpen] = useState(false);
  const [pendingQuickCreateAction, setPendingQuickCreateAction] = useState<"task" | "bootstrap" | null>(null);
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
    setDrawerSelection(null);
  }, [selectedProjectId]);

  useEffect(() => {
    const repositories = projectDetailQuery.data?.repositories ?? [];
    if (!selectedRepositoryId && repositories[0]) {
      setSelectedRepositoryId(repositories[0].id);
    }
  }, [projectDetailQuery.data?.repositories, selectedRepositoryId]);

  useEffect(() => {
    if (!pendingQuickCreateAction || activeSection !== "projects") {
      return;
    }

    const frame = window.requestAnimationFrame(() => {
      if (pendingQuickCreateAction === "task") {
        taskTitleInputRef.current?.focus();
      } else {
        bootstrapWizardRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
      setPendingQuickCreateAction(null);
    });

    return () => window.cancelAnimationFrame(frame);
  }, [activeSection, pendingQuickCreateAction]);

  useEffect(() => {
    const questions = projectDetailQuery.data?.waiting_questions ?? [];
    if (!selectedQuestionId && questions[0]) {
      setSelectedQuestionId(questions[0].id);
    }
  }, [projectDetailQuery.data?.waiting_questions, selectedQuestionId]);

  const {
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

  const selectedWorktree = useMemo(
    () =>
      projectDetailQuery.data?.worktrees.find(
        (worktree) => worktree.id === drawerSelection?.id,
      ) ?? null,
    [projectDetailQuery.data?.worktrees, drawerSelection?.id],
  );

  const openFullDetail = () => {
    if (!drawerSelection) {
      return;
    }
    if (drawerSelection.type === "task") {
      setActiveSection("projects");
      setInspectedTaskId(drawerSelection.id);
      return;
    }
    if (drawerSelection.type === "session") {
      setActiveSection("sessions");
      setSelectedSessionId(drawerSelection.id);
      return;
    }
    if (drawerSelection.type === "worktree") {
      setActiveSection("worktrees");
      return;
    }
    setActiveSection("waiting");
    setSelectedQuestionId(drawerSelection.id);
  };

  const drawerContent = useMemo(() => {
    if (!drawerSelection) {
      return (
        <SectionFrame className="px-4 py-4">
          <SectionTitle>Detail Drawer</SectionTitle>
          <p className="mt-2 text-sm text-slate-500">
            Single-click a task, session, worktree, or waiting question to
            inspect it here.
          </p>
        </SectionFrame>
      );
    }

    if (drawerSelection.type === "task" && taskDetailQuery.data) {
      const sections: DetailDrawerSection[] = [
        {
          id: "context",
          label: "Context",
          content: (
            <div className="space-y-1">
              <div>State: {taskDetailQuery.data.workflow_state}</div>
              <div>Priority: {taskDetailQuery.data.priority ?? "unset"}</div>
              <div>Dependencies: {taskDetailQuery.data.dependencies.length}</div>
            </div>
          ),
        },
        {
          id: "activity",
          label: "Recent activity",
          content: (
            <div className="space-y-1">
              <div>Comments: {taskDetailQuery.data.comments.length}</div>
              <div>Checks: {taskDetailQuery.data.checks.length}</div>
              <div>Artifacts: {taskDetailQuery.data.artifacts.length}</div>
            </div>
          ),
        },
      ];
      return (
        <DetailDrawer
          title={taskDetailQuery.data.title}
          subtitle={taskDetailQuery.data.description ?? "No description yet."}
          sections={sections}
          onOpenFullDetail={openFullDetail}
          onClose={() => setDrawerSelection(null)}
        />
      );
    }

    if (drawerSelection.type === "session" && selectedSession) {
      const sections: DetailDrawerSection[] = [
        {
          id: "runtime",
          label: "Runtime",
          content: (
            <div className="space-y-1">
              <div>Status: {selectedSession.status}</div>
              <div>Profile: {selectedSession.profile}</div>
              <div>Task: {selectedSession.task_id.slice(0, 8)}</div>
            </div>
          ),
        },
        {
          id: "output",
          label: "Recent output",
          content: sessionTailQuery.data?.lines.length ? (
            <pre className="max-h-40 overflow-auto rounded-xl bg-black/25 p-2 text-xs text-slate-300">
              {sessionTailQuery.data.lines.slice(-8).join("\n")}
            </pre>
          ) : (
            "No tail output available."
          ),
        },
      ];
      return (
        <DetailDrawer
          title={selectedSession.session_name}
          subtitle={`${selectedSession.profile} · ${selectedSession.status}`}
          sections={sections}
          onOpenFullDetail={openFullDetail}
          onClose={() => setDrawerSelection(null)}
        />
      );
    }

    if (drawerSelection.type === "worktree" && selectedWorktree) {
      const sections: DetailDrawerSection[] = [
        {
          id: "ownership",
          label: "Ownership",
          content: (
            <div className="space-y-1">
              <div>Branch: {selectedWorktree.branch_name}</div>
              <div>Status: {selectedWorktree.status}</div>
              <div>Task: {selectedWorktree.task_id ?? "unlinked"}</div>
            </div>
          ),
        },
        {
          id: "location",
          label: "Filesystem",
          content: <div className="break-all">{selectedWorktree.path}</div>,
        },
      ];
      return (
        <DetailDrawer
          title={selectedWorktree.branch_name}
          subtitle={selectedWorktree.status}
          sections={sections}
          onOpenFullDetail={openFullDetail}
          onClose={() => setDrawerSelection(null)}
        />
      );
    }

    if (drawerSelection.type === "question" && questionDetailQuery.data) {
      const sections: DetailDrawerSection[] = [
        {
          id: "prompt",
          label: "Prompt",
          content: questionDetailQuery.data.prompt,
        },
        {
          id: "status",
          label: "Status",
          content: (
            <div className="space-y-1">
              <div>Status: {questionDetailQuery.data.status}</div>
              <div>Urgency: {questionDetailQuery.data.urgency ?? "low"}</div>
              <div>Replies: {questionDetailQuery.data.replies.length}</div>
            </div>
          ),
        },
      ];
      return (
        <DetailDrawer
          title="Waiting question"
          subtitle={questionDetailQuery.data.blocked_reason ?? "No blocked reason"}
          sections={sections}
          onOpenFullDetail={openFullDetail}
          onClose={() => setDrawerSelection(null)}
        />
      );
    }

    return (
      <SectionFrame className="px-4 py-4">
        <SectionTitle>Detail Drawer</SectionTitle>
        <p className="mt-2 text-sm text-slate-500">
          The selected entity is unavailable in this project context.
        </p>
      </SectionFrame>
    );
  }, [
    drawerSelection,
    openFullDetail,
    questionDetailQuery.data,
    selectedSession,
    selectedWorktree,
    sessionTailQuery.data?.lines,
    taskDetailQuery.data,
  ]);

  return (
    <AppShell
      sidebar={
        <SidebarNavigation
          activeSection={activeSection}
          setActiveSection={setActiveSection}
          filteredProjects={filteredProjects}
          selectedProjectId={selectedProjectId}
          setSelectedProjectId={(projectId) => setSelectedProjectId(projectId)}
          setProjectsSection={() => setActiveSection("projects")}
          bootstrapWizardRef={bootstrapWizardRef}
          bootstrapProjectMutation={bootstrapProjectMutation}
        />
      }
      header={
        <>
          <AppHeader
            breadcrumbs={breadcrumbs}
            sectionTitle={sectionTitle}
            search={search}
            setSearch={setSearch}
            onSearchActivate={() => setActiveSection("search")}
            quickCreateOpen={quickCreateOpen}
            selectedProjectId={selectedProjectId}
            onToggleQuickCreate={() => setQuickCreateOpen((open) => !open)}
            onQuickCreateTask={() => {
              setQuickCreateOpen(false);
              setActiveSection("projects");
              setPendingQuickCreateAction("task");
            }}
            onQuickCreateBootstrap={() => {
              setQuickCreateOpen(false);
              setActiveSection("projects");
              setPendingQuickCreateAction("bootstrap");
            }}
          />
          {activeSection === "home" ? (
            <HomeSectionContainer
              environment={diagnosticsQuery.data?.environment ?? "development"}
              dashboard={dashboardQuery.data}
              events={eventsQuery.data ?? []}
              projectName={projectDetailQuery.data?.project.name ?? "the control plane"}
              onOpenQuestion={(questionId, projectId) => {
                setSelectedProjectId(projectId);
                selectQuestion(questionId);
              }}
              onOpenTask={(taskId, projectId) => {
                setSelectedProjectId(projectId);
                selectTask(taskId);
              }}
              onOpenSession={(sessionId, projectId) => {
                setSelectedProjectId(projectId);
                selectSession(sessionId);
              }}
              formatEvent={formatEvent}
              summarizeEvent={summarizeEvent}
            />
          ) : null}
        </>
      }
      main={
        <>
          {activeSection === "search" ? (
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
          ) : null}
          {activeSection === "activity" ? (
            <ActivitySectionContainer
              events={activityEventsQuery.data ?? []}
              loading={activityEventsQuery.isLoading}
              error={activityEventsQuery.error instanceof Error ? activityEventsQuery.error.message : null}
              projectOptions={activityProjectOptions}
              taskOptions={activityTaskOptions}
              sessionOptions={activitySessionOptions}
            />
          ) : null}
          {activeSection !== "home" && activeSection !== "search" && activeSection !== "activity" ? (
            <ProjectOverviewScreen>
              <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
                <ProjectsSectionContainer active={activeSection === "projects"}>
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
                              ref={taskTitleInputRef}
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
                                            selectTask(task.id)
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
                </ProjectsSectionContainer>

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
                                        selectTask(subtask.id)
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
                          <div className="rounded-2xl border border-white/7 bg-black/10 p-4">
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
                              className="mt-3 rounded-full bg-[color:var(--color-accent-primary)] px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                              Attach repo
                            </button>
                          </div>

                          <div className="rounded-2xl border border-white/7 bg-black/10 p-4">
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
                        </div>
                      ) : null
                    }
                  />

                  {activeSection === "sessions" ? (
                    <SectionFrame className="px-5 py-5">
                      <SectionTitle>Session Runtime</SectionTitle>
                      <div className="mt-4 flex flex-col gap-3">
                        {projectDetailQuery.data?.sessions.map((session) => (
                          <button
                            key={session.id}
                            onClick={() => selectSession(session.id)}
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

                  <WaitingSectionContainer
                    active={activeSection === "waiting"}
                    questions={projectDetailQuery.data?.waiting_questions ?? []}
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
              </div>
            </ProjectOverviewScreen>
          ) : null}
        </>
      }
      drawer={drawerContent}
    />
  );
}
