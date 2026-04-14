import { type QueryClient } from "@tanstack/react-query";

// Legacy adapter kept for compile-time compatibility.
export function useControlPlaneMutations({ queryClient }: { queryClient: QueryClient }) {
  const unsupported = {
    isPending: false,
    mutate: () => {},
    mutateAsync: async () => {
      throw new Error("Removed in task-board mode");
    },
  };

  queryClient.getQueryCache();

  return {
    bootstrapPreviewMutation: unsupported,
    bootstrapProjectMutation: unsupported,
    createTaskMutation: unsupported,
    createSubtaskMutation: unsupported,
    patchTaskMutation: unsupported,
    createRepositoryMutation: unsupported,
    createWorktreeMutation: unsupported,
    patchWorktreeMutation: unsupported,
    createSessionMutation: unsupported,
    createFollowUpSessionMutation: unsupported,
    createQuestionMutation: unsupported,
    answerQuestionMutation: unsupported,
    addTaskCommentMutation: unsupported,
    addTaskCheckMutation: unsupported,
    addTaskArtifactMutation: unsupported,
    addTaskDependencyMutation: unsupported,
    archiveProjectMutation: unsupported,
    cancelSessionMutation: unsupported,
  };
}
