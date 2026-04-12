import type { QueryClient, QueryKey } from "@tanstack/react-query";
import { controlPlaneQueryKeys } from "@/features/control-plane/queryKeys";

type InvalidationContext = {
  queryClient: QueryClient;
  projectId?: string | null;
  taskId?: string | null;
};

type ProjectMutationOptions = {
  projectId?: string | null;
  taskId?: string | null;
  questionId?: string | null;
  includeDashboard?: boolean;
  includeProjects?: boolean;
};

type SessionMutationOptions = {
  projectId?: string | null;
  includeDashboard?: boolean;
  includeProjectRoot?: boolean;
  includeSessionStreams?: boolean;
};

const invalidateMany = (queryClient: QueryClient, queryKeys: readonly QueryKey[]) => {
  queryKeys.forEach((queryKey) => {
    queryClient.invalidateQueries({ queryKey });
  });
};

export function createControlPlaneInvalidation({ queryClient, projectId, taskId }: InvalidationContext) {
  const invalidateProjectMutation = ({
    projectId: overrideProjectId = projectId ?? null,
    taskId: overrideTaskId,
    questionId,
    includeDashboard = false,
    includeProjects = false,
  }: ProjectMutationOptions = {}) => {
    const queryKeys: QueryKey[] = [];

    if (overrideProjectId) {
      queryKeys.push(controlPlaneQueryKeys.project(overrideProjectId));
    }

    if (includeDashboard) {
      queryKeys.push(controlPlaneQueryKeys.dashboard);
    }

    if (includeProjects) {
      queryKeys.push(controlPlaneQueryKeys.projects);
    }

    const taskDetailId = overrideTaskId ?? taskId ?? null;
    if (taskDetailId) {
      queryKeys.push(controlPlaneQueryKeys.taskDetail(taskDetailId));
    }

    if (questionId) {
      queryKeys.push(controlPlaneQueryKeys.question(questionId));
    }
    queryKeys.push(controlPlaneQueryKeys.questionsRoot);

    invalidateMany(queryClient, queryKeys);
  };

  const invalidateTaskDetailMutation = (overrideTaskId?: string | null) => {
    const taskDetailId = overrideTaskId ?? taskId ?? null;
    if (!taskDetailId) {
      return;
    }
    queryClient.invalidateQueries({ queryKey: controlPlaneQueryKeys.taskDetail(taskDetailId) });
  };

  const invalidateSessionMutation = ({
    projectId: overrideProjectId = projectId ?? null,
    includeDashboard = true,
    includeProjectRoot = false,
    includeSessionStreams = true,
  }: SessionMutationOptions = {}) => {
    const queryKeys: QueryKey[] = [];

    if (includeDashboard) {
      queryKeys.push(controlPlaneQueryKeys.dashboard);
    }

    if (overrideProjectId) {
      queryKeys.push(controlPlaneQueryKeys.project(overrideProjectId));
    }

    if (includeProjectRoot) {
      queryKeys.push(controlPlaneQueryKeys.projectRoot);
    }

    if (includeSessionStreams) {
      queryKeys.push(controlPlaneQueryKeys.sessionTailRoot);
      queryKeys.push(controlPlaneQueryKeys.sessionTimelineRoot);
    }

    invalidateMany(queryClient, queryKeys);
  };

  const invalidateLiveUpdate = () => {
    invalidateMany(queryClient, [
      controlPlaneQueryKeys.dashboard,
      controlPlaneQueryKeys.diagnostics,
      controlPlaneQueryKeys.projects,
      controlPlaneQueryKeys.projectRoot,
      controlPlaneQueryKeys.taskDetailRoot,
      controlPlaneQueryKeys.questionsRoot,
      controlPlaneQueryKeys.questionRoot,
      controlPlaneQueryKeys.sessionTailRoot,
      controlPlaneQueryKeys.sessionTimelineRoot,
      controlPlaneQueryKeys.eventsRoot,
    ]);
  };

  return {
    invalidateLiveUpdate,
    invalidateProjectMutation,
    invalidateTaskDetailMutation,
    invalidateSessionMutation,
  };
}
