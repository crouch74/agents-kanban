import { startTransition } from "react";
import { type QueryClient } from "@tanstack/react-query";
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
  usePatchTaskMutation,
  usePatchWorktreeMutation,
} from "@/features/control-plane/hooks";

type Params = {
  queryClient: QueryClient;
  selectedProjectId: string | null;
  inspectedTaskId: string | null;
  setSelectedProjectId: (projectId: string | null) => void;
  selectSession: (sessionId: string) => void;
  selectQuestion: (questionId: string) => void;
  setSelectedRepositoryId: (repositoryId: string | null) => void;
  setInspectedTaskId: (taskId: string | null) => void;
  setSelectedSessionId: (sessionId: string | null) => void;
  setDraftTaskTitle: (value: string) => void;
  setDraftSubtaskTitle: (value: string) => void;
  setDraftRepoPath: (value: string) => void;
  setDraftRepoName: (value: string) => void;
  setDraftWorktreeLabel: (value: string) => void;
  setSelectedTaskId: (value: string) => void;
  setDraftQuestionPrompt: (value: string) => void;
  setDraftQuestionReason: (value: string) => void;
  setDraftReplyBody: (value: string) => void;
  setDraftCommentBody: (value: string) => void;
  setDraftCheckSummary: (value: string) => void;
  setDraftArtifactName: (value: string) => void;
  setDraftArtifactUri: (value: string) => void;
  setSelectedDependencyTaskId: (value: string) => void;
};

export function useControlPlaneMutations({
  queryClient,
  selectedProjectId,
  inspectedTaskId,
  setSelectedProjectId,
  selectSession,
  selectQuestion,
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
}: Params) {
  const bootstrapProjectMutation = useBootstrapProjectMutation({
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: ["project", result.project.id] });
      startTransition(() => {
        setSelectedProjectId(result.project.id);
      });
    },
  });

  const createTaskMutation = useCreateTaskMutation({
    onSuccess: () => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({ queryKey: ["project", selectedProjectId] });
      }
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      setDraftTaskTitle("");
    },
  });

  const createSubtaskMutation = useCreateTaskMutation({
    onSuccess: () => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({ queryKey: ["project", selectedProjectId] });
      }
      if (inspectedTaskId) {
        queryClient.invalidateQueries({ queryKey: ["task-detail", inspectedTaskId] });
      }
      setDraftSubtaskTitle("");
    },
  });

  const patchTaskMutation = usePatchTaskMutation({
    onSuccess: () => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({ queryKey: ["project", selectedProjectId] });
      }
      if (inspectedTaskId) {
        queryClient.invalidateQueries({ queryKey: ["task-detail", inspectedTaskId] });
      }
    },
  });

  const createRepositoryMutation = useCreateRepositoryMutation({
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

  const createWorktreeMutation = useCreateWorktreeMutation({
    onSuccess: () => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({ queryKey: ["project", selectedProjectId] });
      }
      setDraftWorktreeLabel("");
      setSelectedTaskId("");
    },
  });

  const patchWorktreeMutation = usePatchWorktreeMutation({
    onSuccess: () => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({ queryKey: ["project", selectedProjectId] });
      }
    },
  });

  const createSessionMutation = useCreateSessionMutation({
    onSuccess: (session) => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({ queryKey: ["project", selectedProjectId] });
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      }
      selectSession(session.id);
    },
  });

  const createFollowUpSessionMutation = useCreateFollowUpSessionMutation({
    onSuccess: (session) => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({ queryKey: ["project", selectedProjectId] });
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      }
      queryClient.invalidateQueries({ queryKey: ["session-tail"] });
      queryClient.invalidateQueries({ queryKey: ["session-timeline"] });
      selectSession(session.id);
    },
  });

  const createQuestionMutation = useCreateQuestionMutation({
    onSuccess: (question) => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({ queryKey: ["project", selectedProjectId] });
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      }
      selectQuestion(question.id);
      setDraftQuestionPrompt("");
      setDraftQuestionReason("");
    },
  });

  const answerQuestionMutation = useAnswerQuestionMutation({
    onSuccess: (detail) => {
      if (selectedProjectId) {
        queryClient.invalidateQueries({ queryKey: ["project", selectedProjectId] });
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      }
      queryClient.invalidateQueries({ queryKey: ["question", detail.id] });
      setDraftReplyBody("");
    },
  });

  const addTaskCommentMutation = useAddTaskCommentMutation({
    onSuccess: () => {
      if (inspectedTaskId) {
        queryClient.invalidateQueries({ queryKey: ["task-detail", inspectedTaskId] });
      }
      setDraftCommentBody("");
    },
  });

  const addTaskCheckMutation = useAddTaskCheckMutation({
    onSuccess: () => {
      if (inspectedTaskId) {
        queryClient.invalidateQueries({ queryKey: ["task-detail", inspectedTaskId] });
      }
      setDraftCheckSummary("");
    },
  });

  const addTaskArtifactMutation = useAddTaskArtifactMutation({
    onSuccess: () => {
      if (inspectedTaskId) {
        queryClient.invalidateQueries({ queryKey: ["task-detail", inspectedTaskId] });
      }
      setDraftArtifactName("");
      setDraftArtifactUri("");
    },
  });

  const addTaskDependencyMutation = useAddTaskDependencyMutation({
    onSuccess: () => {
      if (inspectedTaskId) {
        queryClient.invalidateQueries({ queryKey: ["task-detail", inspectedTaskId] });
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
      setInspectedTaskId(null);
      setSelectedSessionId(null);
    },
  });

  return {
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
  };
}
