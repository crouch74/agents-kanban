import { useEffect } from "react";
import { useMutation, useQuery, type UseMutationOptions } from "@tanstack/react-query";
import {
  bootstrapProject,
  getProject,
  getProjects,
} from "@/lib/api/projects";
import { answerQuestion, createQuestion, getQuestion } from "@/lib/api/questions";
import { createRepository } from "@/lib/api/repositories";
import {
  cancelSession,
  createFollowUpSession,
  createSession,
  getSessionTail,
  getSessionTimeline,
} from "@/lib/api/sessions";
import { getDashboard, getDiagnostics, getEvents, searchContext } from "@/lib/api/system";
import {
  addTaskArtifact,
  addTaskCheck,
  addTaskComment,
  addTaskDependency,
  createTask,
  getTaskDetail,
  patchTask,
} from "@/lib/api/tasks";
import { WS_BASE } from "@/lib/api/httpClient";
import { createWorktree, patchWorktree } from "@/lib/api/worktrees";

export function useLiveInvalidationSocket(invalidateAll: () => void) {
  useEffect(() => {
    if (typeof window === "undefined" || typeof window.WebSocket === "undefined") {
      return;
    }

    let disposed = false;
    let socket: WebSocket | null = null;
    let reconnectHandle: number | undefined;

    const connect = () => {
      if (disposed) {
        return;
      }
      socket = new window.WebSocket(WS_BASE);
      socket.onmessage = (event) => {
        const payload = JSON.parse(event.data) as { type?: string };
        if (payload.type === "system.connected" || payload.type === "system.ping") {
          return;
        }
        invalidateAll();
      };
      socket.onclose = () => {
        if (disposed) {
          return;
        }
        reconnectHandle = window.setTimeout(connect, 1500);
      };
    };

    connect();

    return () => {
      disposed = true;
      if (reconnectHandle) {
        window.clearTimeout(reconnectHandle);
      }
      socket?.close();
    };
  }, [invalidateAll]);
}

export const useDashboardQuery = () => useQuery({ queryKey: ["dashboard"], queryFn: getDashboard });
export const useDiagnosticsQuery = () => useQuery({ queryKey: ["diagnostics"], queryFn: getDiagnostics });
export const useProjectsQuery = () => useQuery({ queryKey: ["projects"], queryFn: getProjects });
export const useProjectDetailQuery = (projectId: string | null) =>
  useQuery({ queryKey: ["project", projectId], queryFn: () => getProject(projectId!), enabled: Boolean(projectId) });
export const useEventsQuery = (projectId: string | null) =>
  useQuery({ queryKey: ["events", projectId], queryFn: () => getEvents({ projectId: projectId ?? undefined, limit: 18 }) });
export const useSearchQuery = (deferredSearch: string, projectId?: string | null) =>
  useQuery({
    queryKey: ["search", deferredSearch, projectId],
    queryFn: () => searchContext(deferredSearch, projectId ?? undefined),
    enabled: deferredSearch.trim().length >= 2,
  });
export const useSessionTailQuery = (sessionId: string | null) =>
  useQuery({
    queryKey: ["session-tail", sessionId],
    queryFn: () => getSessionTail(sessionId!),
    enabled: Boolean(sessionId),
    refetchInterval: sessionId ? 2500 : false,
  });
export const useSessionTimelineQuery = (sessionId: string | null) =>
  useQuery({
    queryKey: ["session-timeline", sessionId],
    queryFn: () => getSessionTimeline(sessionId!),
    enabled: Boolean(sessionId),
    refetchInterval: sessionId ? 3000 : false,
  });
export const useQuestionDetailQuery = (questionId: string | null) =>
  useQuery({ queryKey: ["question", questionId], queryFn: () => getQuestion(questionId!), enabled: Boolean(questionId) });
export const useTaskDetailQuery = (taskId: string | null) =>
  useQuery({ queryKey: ["task-detail", taskId], queryFn: () => getTaskDetail(taskId!), enabled: Boolean(taskId) });

type MutationHookOptions<TData, TVars> = Omit<UseMutationOptions<TData, Error, TVars>, "mutationFn">;

export const useBootstrapProjectMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof bootstrapProject>>, Parameters<typeof bootstrapProject>[0]>) =>
  useMutation({ mutationFn: bootstrapProject, ...options });
export const useCreateTaskMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof createTask>>, Parameters<typeof createTask>[0]>) =>
  useMutation({ mutationFn: createTask, ...options });
export const usePatchTaskMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof patchTask>>, { taskId: string; boardColumnId: string }>) =>
  useMutation({ mutationFn: ({ taskId, boardColumnId }) => patchTask(taskId, { board_column_id: boardColumnId }), ...options });
export const useCreateRepositoryMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof createRepository>>, Parameters<typeof createRepository>[0]>) =>
  useMutation({ mutationFn: createRepository, ...options });
export const useCreateWorktreeMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof createWorktree>>, Parameters<typeof createWorktree>[0]>) =>
  useMutation({ mutationFn: createWorktree, ...options });
export const usePatchWorktreeMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof patchWorktree>>, { worktreeId: string; status: string }>) =>
  useMutation({ mutationFn: ({ worktreeId, status }) => patchWorktree(worktreeId, { status }), ...options });
export const useCreateSessionMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof createSession>>, Parameters<typeof createSession>[0]>) =>
  useMutation({ mutationFn: createSession, ...options });
export const useCreateFollowUpSessionMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof createFollowUpSession>>, { sessionId: string; profile: string; followUpType?: "retry" | "review" | "verify" | "handoff" }>) =>
  useMutation({
    mutationFn: ({ sessionId, profile, followUpType }) =>
      createFollowUpSession(sessionId, {
        profile,
        follow_up_type: followUpType,
        reuse_repository: true,
        reuse_worktree: true,
      }),
    ...options,
  });
export const useCreateQuestionMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof createQuestion>>, Parameters<typeof createQuestion>[0]>) =>
  useMutation({ mutationFn: createQuestion, ...options });
export const useAnswerQuestionMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof answerQuestion>>, { questionId: string; body: string }>) =>
  useMutation({ mutationFn: ({ questionId, body }) => answerQuestion(questionId, { responder_name: "operator", body }), ...options });
export const useAddTaskCommentMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof addTaskComment>>, { taskId: string; body: string }>) =>
  useMutation({ mutationFn: ({ taskId, body }) => addTaskComment(taskId, { author_name: "operator", body }), ...options });
export const useAddTaskCheckMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof addTaskCheck>>, { taskId: string; checkType: string; status: string; summary: string }>) =>
  useMutation({ mutationFn: ({ taskId, checkType, status, summary }) => addTaskCheck(taskId, { check_type: checkType, status, summary }), ...options });
export const useAddTaskArtifactMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof addTaskArtifact>>, { taskId: string; artifactType: string; name: string; uri: string }>) =>
  useMutation({ mutationFn: ({ taskId, artifactType, name, uri }) => addTaskArtifact(taskId, { artifact_type: artifactType, name, uri }), ...options });
export const useAddTaskDependencyMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof addTaskDependency>>, { taskId: string; dependsOnTaskId: string }>) =>
  useMutation({ mutationFn: ({ taskId, dependsOnTaskId }) => addTaskDependency(taskId, { depends_on_task_id: dependsOnTaskId }), ...options });
export const useCancelSessionMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof cancelSession>>, Parameters<typeof cancelSession>[0]>) =>
  useMutation({ mutationFn: cancelSession, ...options });
