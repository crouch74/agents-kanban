import { useMutation, useQuery } from "@tanstack/react-query";
import {
  addTaskArtifact,
  addTaskCheck,
  addTaskComment,
  addTaskDependency,
  createTask,
  getTaskDetail,
  patchTask,
} from "@/lib/api/tasks";
import { controlPlaneQueryKeys } from "@/features/control-plane/queryKeys";
import { type MutationHookOptions } from "@/features/control-plane/hooks/mutationTypes";

export const useTaskDetailQuery = (taskId: string | null) =>
  useQuery({
    queryKey: controlPlaneQueryKeys.taskDetail(taskId),
    queryFn: () => getTaskDetail(taskId!),
    enabled: Boolean(taskId),
  });

export const useCreateTaskMutation = (
  options?: MutationHookOptions<
    Awaited<ReturnType<typeof createTask>>,
    Parameters<typeof createTask>[0]
  >,
) => useMutation({ mutationFn: createTask, ...options });

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
        workflow_state: workflowState,
      }),
    ...options,
  });

export const useAddTaskCommentMutation = (
  options?: MutationHookOptions<
    Awaited<ReturnType<typeof addTaskComment>>,
    { taskId: string; body: string }
  >,
) =>
  useMutation({
    mutationFn: ({ taskId, body }) => addTaskComment(taskId, { author_name: "operator", body }),
    ...options,
  });

export const useAddTaskCheckMutation = (
  options?: MutationHookOptions<
    Awaited<ReturnType<typeof addTaskCheck>>,
    { taskId: string; checkType: string; status: string; summary: string }
  >,
) =>
  useMutation({
    mutationFn: ({ taskId, checkType, status, summary }) =>
      addTaskCheck(taskId, { check_type: checkType, status, summary }),
    ...options,
  });

export const useAddTaskArtifactMutation = (
  options?: MutationHookOptions<
    Awaited<ReturnType<typeof addTaskArtifact>>,
    { taskId: string; artifactType: string; name: string; uri: string }
  >,
) =>
  useMutation({
    mutationFn: ({ taskId, artifactType, name, uri }) =>
      addTaskArtifact(taskId, { artifact_type: artifactType, name, uri }),
    ...options,
  });

export const useAddTaskDependencyMutation = (
  options?: MutationHookOptions<
    Awaited<ReturnType<typeof addTaskDependency>>,
    { taskId: string; dependsOnTaskId: string }
  >,
) =>
  useMutation({
    mutationFn: ({ taskId, dependsOnTaskId }) =>
      addTaskDependency(taskId, { depends_on_task_id: dependsOnTaskId }),
    ...options,
  });
