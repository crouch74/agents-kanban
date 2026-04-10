import { useDeferredValue, useEffect, useMemo, useState, startTransition } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  ArrowRight,
  Bot,
  CircleDashed,
  FolderGit2,
  GitBranch,
  GitFork,
  Lock,
  MessageSquareText,
  Play,
  Search,
  ShieldCheck,
  Terminal,
  Trash2,
} from "lucide-react";
import type { TaskSummary } from "@acp/sdk";
import {
  addTaskArtifact,
  addTaskCheck,
  addTaskComment,
  answerQuestion,
  createQuestion,
  createSession,
  createProject,
  createRepository,
  createTask,
  createWorktree,
  getDashboard,
  getDiagnostics,
  getProject,
  getProjects,
  getQuestion,
  getTaskDetail,
  getSessionTail,
  patchWorktree,
  searchContext,
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
  const [selectedSessionTaskId, setSelectedSessionTaskId] = useState<string>("");
  const [selectedSessionWorktreeId, setSelectedSessionWorktreeId] = useState<string>("");
  const [sessionProfile, setSessionProfile] = useState("executor");
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [selectedQuestionId, setSelectedQuestionId] = useState<string | null>(null);
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
  const searchQuery = useQuery({
    queryKey: ["search", deferredSearch, selectedProjectId],
    queryFn: () => searchContext(deferredSearch, selectedProjectId ?? undefined),
    enabled: deferredSearch.trim().length >= 2,
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

  const createSessionMutation = useMutation({
    mutationFn: createSession,
    onSuccess: (session) => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({ queryKey: ["project", selectedProjectId] });
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      }
      setSelectedSessionId(session.id);
    },
  });

  const createQuestionMutation = useMutation({
    mutationFn: createQuestion,
    onSuccess: (question) => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({ queryKey: ["project", selectedProjectId] });
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      }
      setSelectedQuestionId(question.id);
      setDraftQuestionPrompt("");
      setDraftQuestionReason("");
    },
  });

  const answerQuestionMutation = useMutation({
    mutationFn: ({ questionId, body }: { questionId: string; body: string }) =>
      answerQuestion(questionId, { responder_name: "operator", body }),
    onSuccess: (detail) => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({ queryKey: ["project", selectedProjectId] });
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      }
      queryClient.invalidateQueries({ queryKey: ["question", detail.id] });
      setDraftReplyBody("");
    },
  });

  const addTaskCommentMutation = useMutation({
    mutationFn: ({ taskId, body }: { taskId: string; body: string }) =>
      addTaskComment(taskId, { author_name: "operator", body }),
    onSuccess: () => {
      if (inspectedTaskId) {
        queryClient.invalidateQueries({ queryKey: ["task-detail", inspectedTaskId] });
      }
      setDraftCommentBody("");
    },
  });

  const addTaskCheckMutation = useMutation({
    mutationFn: ({ taskId, checkType, status, summary }: { taskId: string; checkType: string; status: string; summary: string }) =>
      addTaskCheck(taskId, { check_type: checkType, status, summary }),
    onSuccess: () => {
      if (inspectedTaskId) {
        queryClient.invalidateQueries({ queryKey: ["task-detail", inspectedTaskId] });
      }
      setDraftCheckSummary("");
    },
  });

  const addTaskArtifactMutation = useMutation({
    mutationFn: ({ taskId, artifactType, name, uri }: { taskId: string; artifactType: string; name: string; uri: string }) =>
      addTaskArtifact(taskId, { artifact_type: artifactType, name, uri }),
    onSuccess: () => {
      if (inspectedTaskId) {
        queryClient.invalidateQueries({ queryKey: ["task-detail", inspectedTaskId] });
      }
      setDraftArtifactName("");
      setDraftArtifactUri("");
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

  const sessionTailQuery = useQuery({
    queryKey: ["session-tail", selectedSessionId],
    queryFn: () => getSessionTail(selectedSessionId!),
    enabled: Boolean(selectedSessionId),
    refetchInterval: selectedSessionId ? 2500 : false,
  });

  const questionDetailQuery = useQuery({
    queryKey: ["question", selectedQuestionId],
    queryFn: () => getQuestion(selectedQuestionId!),
    enabled: Boolean(selectedQuestionId),
  });

  const taskDetailQuery = useQuery({
    queryKey: ["task-detail", inspectedTaskId],
    queryFn: () => getTaskDetail(inspectedTaskId!),
    enabled: Boolean(inspectedTaskId),
  });

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
          <SectionTitle>Search Results</SectionTitle>
          <div className="mt-4 flex flex-col gap-3">
            {deferredSearch.trim().length < 2 ? (
              <div className="text-sm text-slate-500">Type at least two characters to search tasks, questions, sessions, and events.</div>
            ) : null}
            {searchQuery.data?.hits.map((hit) => (
              <button
                key={`${hit.entity_type}-${hit.entity_id}`}
                onClick={() => {
                  if (hit.entity_type === "task") {
                    setInspectedTaskId(hit.entity_id);
                    if (hit.project_id) {
                      setSelectedProjectId(hit.project_id);
                    }
                  } else if (hit.entity_type === "waiting_question") {
                    setSelectedQuestionId(hit.entity_id);
                    if (hit.project_id) {
                      setSelectedProjectId(hit.project_id);
                    }
                  } else if (hit.entity_type === "session") {
                    setSelectedSessionId(hit.entity_id);
                    if (hit.project_id) {
                      setSelectedProjectId(hit.project_id);
                    }
                  } else if (hit.project_id) {
                    setSelectedProjectId(hit.project_id);
                  }
                }}
                className="rounded-2xl border border-white/7 bg-white/3 px-4 py-3 text-left"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-semibold text-slate-100">{hit.title}</div>
                  <Pill className="border-white/8 text-slate-300">{hit.entity_type}</Pill>
                </div>
                <div className="mt-2 line-clamp-2 text-sm text-slate-500">{hit.snippet}</div>
                {hit.secondary ? <div className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-600">{hit.secondary}</div> : null}
              </button>
            ))}
            {deferredSearch.trim().length >= 2 && !searchQuery.data?.hits.length ? (
              <div className="text-sm text-slate-500">No matching records found.</div>
            ) : null}
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
                      <button
                        key={task.id}
                        onClick={() => setInspectedTaskId(task.id)}
                        className={[
                          "w-full rounded-2xl border bg-white/4 p-4 text-left",
                          inspectedTaskId === task.id
                            ? "border-[color:var(--accent)]"
                            : "border-white/8",
                        ].join(" ")}
                      >
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
                      </button>
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
              <SectionTitle>Task Inspector</SectionTitle>
              {taskDetailQuery.data ? (
                <div className="mt-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="text-xl font-semibold text-slate-100">{taskDetailQuery.data.title}</div>
                      <div className="mt-2 text-sm text-slate-400">
                        {taskDetailQuery.data.description ?? "No task description yet."}
                      </div>
                    </div>
                    <Pill className="border-white/8 text-slate-300">{taskDetailQuery.data.workflow_state}</Pill>
                  </div>

                  <div className="mt-5 rounded-2xl border border-white/7 bg-black/10 p-4">
                    <div className="text-sm font-medium text-slate-200">Comments</div>
                    <div className="mt-3 flex flex-col gap-2">
                      {taskDetailQuery.data.comments.map((comment) => (
                        <div key={comment.id} className="rounded-2xl border border-white/8 bg-white/4 px-3 py-3">
                          <div className="text-xs uppercase tracking-[0.18em] text-slate-500">{comment.author_name}</div>
                          <div className="mt-2 text-sm text-slate-200">{comment.body}</div>
                        </div>
                      ))}
                      {!taskDetailQuery.data.comments.length ? (
                        <div className="text-sm text-slate-500">No comments yet.</div>
                      ) : null}
                    </div>
                    <textarea
                      value={draftCommentBody}
                      onChange={(event) => setDraftCommentBody(event.target.value)}
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
                      disabled={!draftCommentBody.trim() || addTaskCommentMutation.isPending}
                      className="mt-3 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Add comment
                    </button>
                  </div>

                  <div className="mt-5 rounded-2xl border border-white/7 bg-black/10 p-4">
                    <div className="text-sm font-medium text-slate-200">Checks</div>
                    <div className="mt-3 flex flex-col gap-2">
                      {taskDetailQuery.data.checks.map((check) => (
                        <div key={check.id} className="rounded-2xl border border-white/8 bg-white/4 px-3 py-3">
                          <div className="flex items-center justify-between gap-3">
                            <div className="text-sm font-medium text-slate-100">{check.check_type}</div>
                            <Pill className="border-white/8 text-slate-300">{check.status}</Pill>
                          </div>
                          <div className="mt-2 text-sm text-slate-200">{check.summary}</div>
                        </div>
                      ))}
                      {!taskDetailQuery.data.checks.length ? (
                        <div className="text-sm text-slate-500">No checks yet.</div>
                      ) : null}
                    </div>
                    <div className="mt-3 grid gap-3 md:grid-cols-2">
                      <input
                        value={draftCheckType}
                        onChange={(event) => setDraftCheckType(event.target.value)}
                        placeholder="Check type"
                        className="rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                      />
                      <select
                        value={draftCheckStatus}
                        onChange={(event) => setDraftCheckStatus(event.target.value)}
                        className="rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                      >
                        {["pending", "passed", "failed", "warning"].map((status) => (
                          <option key={status} value={status}>
                            {status}
                          </option>
                        ))}
                      </select>
                    </div>
                    <textarea
                      value={draftCheckSummary}
                      onChange={(event) => setDraftCheckSummary(event.target.value)}
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
                      disabled={!draftCheckSummary.trim() || addTaskCheckMutation.isPending}
                      className="mt-3 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Add check
                    </button>
                  </div>

                  <div className="mt-5 rounded-2xl border border-white/7 bg-black/10 p-4">
                    <div className="text-sm font-medium text-slate-200">Artifacts</div>
                    <div className="mt-3 flex flex-col gap-2">
                      {taskDetailQuery.data.artifacts.map((artifact) => (
                        <div key={artifact.id} className="rounded-2xl border border-white/8 bg-white/4 px-3 py-3">
                          <div className="flex items-center justify-between gap-3">
                            <div className="text-sm font-medium text-slate-100">{artifact.name}</div>
                            <Pill className="border-white/8 text-slate-300">{artifact.artifact_type}</Pill>
                          </div>
                          <div className="mt-2 break-all text-sm text-slate-400">{artifact.uri}</div>
                        </div>
                      ))}
                      {!taskDetailQuery.data.artifacts.length ? (
                        <div className="text-sm text-slate-500">No artifacts yet.</div>
                      ) : null}
                    </div>
                    <div className="mt-3 grid gap-3 md:grid-cols-2">
                      <input
                        value={draftArtifactType}
                        onChange={(event) => setDraftArtifactType(event.target.value)}
                        placeholder="Artifact type"
                        className="rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                      />
                      <input
                        value={draftArtifactName}
                        onChange={(event) => setDraftArtifactName(event.target.value)}
                        placeholder="Artifact name"
                        className="rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                      />
                    </div>
                    <input
                      value={draftArtifactUri}
                      onChange={(event) => setDraftArtifactUri(event.target.value)}
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
                      disabled={!draftArtifactName.trim() || !draftArtifactUri.trim() || addTaskArtifactMutation.isPending}
                      className="mt-3 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Add artifact
                    </button>
                  </div>
                </div>
              ) : (
                <div className="mt-4 text-sm text-slate-500">Select a task card to inspect comments, checks, and artifacts.</div>
              )}
            </SectionFrame>

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
              <SectionTitle>Session Runtime</SectionTitle>
              <div className="mt-4 flex flex-col gap-3">
                {projectDetailQuery.data?.sessions.map((session) => (
                  <button
                    key={session.id}
                    onClick={() => setSelectedSessionId(session.id)}
                    className={[
                      "rounded-2xl border px-4 py-4 text-left",
                      selectedSessionId === session.id
                        ? "border-[color:var(--accent)] bg-[color:var(--accent-soft)]"
                        : "border-white/7 bg-white/3",
                    ].join(" ")}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2 text-sm font-semibold text-slate-100">
                        <Terminal className="h-4 w-4 text-slate-400" />
                        {session.profile}
                      </div>
                      <Pill className="border-white/8 text-slate-300">{session.status}</Pill>
                    </div>
                    <div className="mt-2 text-xs text-slate-500">{session.session_name}</div>
                  </button>
                ))}
                {!projectDetailQuery.data?.sessions.length ? (
                  <div className="text-sm text-slate-500">No agent sessions yet.</div>
                ) : null}
              </div>

              {selectedProjectId ? (
                <div className="mt-5 rounded-2xl border border-white/7 bg-black/10 p-4">
                  <div className="text-sm font-medium text-slate-200">Spawn session</div>
                  <select
                    value={selectedSessionTaskId}
                    onChange={(event) => setSelectedSessionTaskId(event.target.value)}
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
                    onChange={(event) => setSelectedSessionWorktreeId(event.target.value)}
                    className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
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
                    onChange={(event) => setSessionProfile(event.target.value)}
                    className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                  >
                    {["executor", "reviewer", "verifier", "research", "docs"].map((profile) => (
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
                        worktree_id: selectedSessionWorktreeId || undefined,
                      })
                    }
                    disabled={!selectedSessionTaskId || createSessionMutation.isPending}
                    className="mt-3 inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <Play className="h-4 w-4" />
                    Spawn
                  </button>
                </div>
              ) : null}

              <div className="mt-5 rounded-2xl border border-white/7 bg-black/15 p-4">
                <div className="flex items-center gap-2 text-sm font-medium text-slate-200">
                  <CircleDashed className="h-4 w-4 text-slate-400" />
                  Recent tail
                </div>
                {sessionTailQuery.data ? (
                  <pre className="mt-3 max-h-56 overflow-auto rounded-2xl bg-black/25 p-3 text-xs leading-5 text-slate-300">
                    {sessionTailQuery.data.lines.join("\n")}
                  </pre>
                ) : (
                  <div className="mt-3 text-sm text-slate-500">Select a session to inspect recent runtime output.</div>
                )}
              </div>

              <div className="mt-5 rounded-2xl border border-white/7 bg-black/10 p-4">
                <div className="text-sm font-medium text-slate-200">Open waiting question</div>
                <select
                  value={selectedSessionTaskId}
                  onChange={(event) => setSelectedSessionTaskId(event.target.value)}
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
                  onChange={(event) => setSelectedSessionId(event.target.value || null)}
                  className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                >
                  <option value="">Optional linked session</option>
                  {(projectDetailQuery.data?.sessions ?? []).map((session) => (
                    <option key={session.id} value={session.id}>
                      {session.profile} · {session.session_name}
                    </option>
                  ))}
                </select>
                <textarea
                  value={draftQuestionPrompt}
                  onChange={(event) => setDraftQuestionPrompt(event.target.value)}
                  placeholder="What decision or clarification does the agent need?"
                  className="mt-3 min-h-24 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                />
                <input
                  value={draftQuestionReason}
                  onChange={(event) => setDraftQuestionReason(event.target.value)}
                  placeholder="Why is work blocked?"
                  className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                />
                <select
                  value={draftQuestionUrgency}
                  onChange={(event) => setDraftQuestionUrgency(event.target.value)}
                  className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                >
                  {["low", "medium", "high", "urgent"].map((urgency) => (
                    <option key={urgency} value={urgency}>
                      {urgency}
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
                  disabled={!selectedSessionTaskId || !draftQuestionPrompt.trim() || createQuestionMutation.isPending}
                  className="mt-3 rounded-full bg-[color:var(--accent)] px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Open question
                </button>
              </div>
            </SectionFrame>

            <SectionFrame className="px-5 py-5">
              <SectionTitle>Waiting Inbox</SectionTitle>
              <div className="mt-4 flex flex-col gap-3">
                {(projectDetailQuery.data?.waiting_questions ?? []).map((question) => (
                  <button
                    key={question.id}
                    onClick={() => setSelectedQuestionId(question.id)}
                    className={[
                      "rounded-2xl border px-4 py-4 text-left",
                      selectedQuestionId === question.id
                        ? "border-[color:var(--accent)] bg-[color:var(--accent-soft)]"
                        : "border-white/7 bg-white/3",
                    ].join(" ")}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="text-sm font-semibold text-slate-100">{question.prompt}</div>
                      <Pill className="border-white/8 text-slate-300">{question.urgency ?? "open"}</Pill>
                    </div>
                    <div className="mt-2 text-xs text-slate-500">{question.blocked_reason ?? "Awaiting operator input"}</div>
                  </button>
                ))}
                {!projectDetailQuery.data?.waiting_questions.length ? (
                  <div className="text-sm text-slate-500">No waiting questions right now.</div>
                ) : null}
              </div>

              <div className="mt-5 rounded-2xl border border-white/7 bg-black/15 p-4">
                <div className="flex items-center gap-2 text-sm font-medium text-slate-200">
                  <MessageSquareText className="h-4 w-4 text-slate-400" />
                  Selected question
                </div>
                {questionDetailQuery.data ? (
                  <>
                    <div className="mt-3 text-sm font-semibold text-slate-100">{questionDetailQuery.data.prompt}</div>
                    <div className="mt-2 text-sm text-slate-400">
                      {questionDetailQuery.data.blocked_reason ?? "No explicit blocked reason provided."}
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Pill className="border-white/8 text-slate-300">{questionDetailQuery.data.status}</Pill>
                      <Pill className="border-white/8 text-slate-300">{questionDetailQuery.data.urgency ?? "normal"}</Pill>
                    </div>
                    <div className="mt-4 flex flex-col gap-2">
                      {questionDetailQuery.data.replies.map((reply) => (
                        <div key={reply.id} className="rounded-2xl border border-white/8 bg-white/4 px-3 py-3">
                          <div className="text-xs uppercase tracking-[0.18em] text-slate-500">{reply.responder_name}</div>
                          <div className="mt-2 text-sm text-slate-200">{reply.body}</div>
                        </div>
                      ))}
                      {!questionDetailQuery.data.replies.length ? (
                        <div className="text-sm text-slate-500">No replies yet.</div>
                      ) : null}
                    </div>
                    {questionDetailQuery.data.status === "open" ? (
                      <>
                        <textarea
                          value={draftReplyBody}
                          onChange={(event) => setDraftReplyBody(event.target.value)}
                          placeholder="Reply to unblock the agent"
                          className="mt-4 min-h-24 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
                        />
                        <button
                          onClick={() =>
                            answerQuestionMutation.mutate({
                              questionId: questionDetailQuery.data!.id,
                              body: draftReplyBody,
                            })
                          }
                          disabled={!draftReplyBody.trim() || answerQuestionMutation.isPending}
                          className="mt-3 rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          Send reply
                        </button>
                      </>
                    ) : null}
                  </>
                ) : (
                  <div className="mt-3 text-sm text-slate-500">Select a waiting question to inspect and answer it.</div>
                )}
              </div>
            </SectionFrame>

            <SectionFrame className="px-5 py-5">
              <SectionTitle>Runtime readiness</SectionTitle>
              <div className="mt-5 grid gap-3">
                <Signal label="tmux" ready={Boolean(diagnosticsQuery.data?.tmux_available)} icon={Bot} />
                <Signal label="tmux server" ready={Boolean(diagnosticsQuery.data?.tmux_server_running)} icon={Terminal} />
                <Signal label="git" ready={Boolean(diagnosticsQuery.data?.git_available)} icon={FolderGit2} />
                <Signal label="audit log" ready icon={ShieldCheck} />
                <Signal label="waiting inbox" ready icon={MessageSquareText} />
              </div>
            </SectionFrame>

            <SectionFrame className="px-5 py-5">
              <SectionTitle>Diagnostics</SectionTitle>
              <div className="mt-4 grid gap-3">
                <DiagRow label="DB path" value={diagnosticsQuery.data?.database_path ?? "unknown"} />
                <DiagRow label="Runtime home" value={diagnosticsQuery.data?.runtime_home ?? "unknown"} />
                <DiagRow label="Repositories" value={String(diagnosticsQuery.data?.current_repository_count ?? 0)} />
                <DiagRow label="Worktrees" value={String(diagnosticsQuery.data?.current_worktree_count ?? 0)} />
                <DiagRow label="Sessions" value={String(diagnosticsQuery.data?.current_session_count ?? 0)} />
                <DiagRow label="Open questions" value={String(diagnosticsQuery.data?.current_open_question_count ?? 0)} />
                <DiagRow label="Events" value={String(diagnosticsQuery.data?.current_event_count ?? 0)} />
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

function DiagRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-2xl border border-white/7 bg-white/3 px-4 py-3">
      <div className="text-sm text-slate-400">{label}</div>
      <div className="max-w-[60%] break-all text-right text-sm text-slate-200">{value}</div>
    </div>
  );
}
