import { useEffect } from "react";
import { useMutation, useQuery, type UseMutationOptions } from "@tanstack/react-query";
import { archiveProject, createProject, getProject, getProjects } from "@/lib/api/projects";
import { addTaskComment, createTask, getTaskDetail, patchTask } from "@/lib/api/tasks";
import { getDashboard, getEvents, searchContext } from "@/lib/api/system";
import { WS_BASE } from "@/lib/api/httpClient";
import { controlPlaneQueryKeys } from "@/features/control-plane/queryKeys";

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

export const useDashboardQuery = () => useQuery({ queryKey: controlPlaneQueryKeys.dashboard, queryFn: getDashboard });
export const useDiagnosticsQuery = () => useQuery({ queryKey: controlPlaneQueryKeys.diagnostics, queryFn: getDashboard });
export const useProjectsQuery = () => useQuery({ queryKey: controlPlaneQueryKeys.projects, queryFn: getProjects });
export const useProjectDetailQuery = (projectId: string | null) =>
  useQuery({ queryKey: controlPlaneQueryKeys.project(projectId), queryFn: () => getProject(projectId!), enabled: Boolean(projectId) });
export const useQuestionsQuery = () => useQuery({ queryKey: controlPlaneQueryKeys.questionsRoot, queryFn: async () => [] as never[] });
export const useEventsQuery = (projectId: string | null) =>
  useQuery({ queryKey: controlPlaneQueryKeys.events(projectId), queryFn: () => getEvents({ projectId: projectId ?? undefined, limit: 18 }) });
export const useSearchQuery = (deferredSearch: string, projectId?: string | null) =>
  useQuery({
    queryKey: controlPlaneQueryKeys.search(deferredSearch, projectId),
    queryFn: () => searchContext(deferredSearch, projectId ?? undefined),
    enabled: deferredSearch.trim().length >= 2,
  });
export const useSessionTailQuery = () => useQuery({ queryKey: controlPlaneQueryKeys.sessionTail(null), queryFn: async () => null, enabled: false });
export const useSessionTimelineQuery = () => useQuery({ queryKey: controlPlaneQueryKeys.sessionTimeline(null), queryFn: async () => null, enabled: false });
export const useQuestionDetailQuery = () => useQuery({ queryKey: controlPlaneQueryKeys.question(null), queryFn: async () => null, enabled: false });
export const useTaskDetailQuery = (taskId: string | null) =>
  useQuery({ queryKey: controlPlaneQueryKeys.taskDetail(taskId), queryFn: () => getTaskDetail(taskId!), enabled: Boolean(taskId) });

type MutationHookOptions<TData, TVars> = Omit<UseMutationOptions<TData, Error, TVars>, "mutationFn">;

const unsupported = <T, V>() => useMutation<T, Error, V>({ mutationFn: async () => { throw new Error("Removed in task-board mode"); } });

export const useBootstrapProjectMutation = <TData, TVars>() => unsupported<TData, TVars>();
export const useBootstrapProjectPreviewMutation = <TData, TVars>() => unsupported<TData, TVars>();
export const useCreateRepositoryMutation = <TData, TVars>() => unsupported<TData, TVars>();
export const useCreateWorktreeMutation = <TData, TVars>() => unsupported<TData, TVars>();
export const usePatchWorktreeMutation = <TData, TVars>() => unsupported<TData, TVars>();
export const useCreateSessionMutation = <TData, TVars>() => unsupported<TData, TVars>();
export const useCreateFollowUpSessionMutation = <TData, TVars>() => unsupported<TData, TVars>();
export const useCreateQuestionMutation = <TData, TVars>() => unsupported<TData, TVars>();
export const useAnswerQuestionMutation = <TData, TVars>() => unsupported<TData, TVars>();
export const useAddTaskCheckMutation = <TData, TVars>() => unsupported<TData, TVars>();
export const useAddTaskArtifactMutation = <TData, TVars>() => unsupported<TData, TVars>();
export const useAddTaskDependencyMutation = <TData, TVars>() => unsupported<TData, TVars>();
export const useCancelSessionMutation = <TData, TVars>() => unsupported<TData, TVars>();
export const useCleanRuntimeOrphansMutation = <TData, TVars>() => unsupported<TData, TVars>();

export const useArchiveProjectMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof archiveProject>>, string>) =>
  useMutation({ mutationFn: archiveProject, ...options });

export const useCreateTaskMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof createTask>>, Parameters<typeof createTask>[0]>) =>
  useMutation({ mutationFn: createTask, ...options });

export const usePatchTaskMutation = (
  options?: MutationHookOptions<
    Awaited<ReturnType<typeof patchTask>>,
    {
      taskId: string;
      boardColumnId?: string;
      title?: string;
      description?: string;
      workflowState?: string;
    }
  >,
) =>
  useMutation({
    mutationFn: ({ taskId, boardColumnId, title, description, workflowState }) =>
      patchTask(taskId, {
        board_column_id: boardColumnId,
        title,
        description,
        workflow_state: workflowState as never,
      }),
    ...options,
  });

export const useAddTaskCommentMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof addTaskComment>>, { taskId: string; body: string }>) =>
  useMutation({ mutationFn: ({ taskId, body }) => addTaskComment(taskId, { author_name: "operator", source: "web", body }), ...options });

export const useCreateProjectMutation = (options?: MutationHookOptions<Awaited<ReturnType<typeof createProject>>, Parameters<typeof createProject>[0]>) =>
  useMutation({ mutationFn: createProject, ...options });
