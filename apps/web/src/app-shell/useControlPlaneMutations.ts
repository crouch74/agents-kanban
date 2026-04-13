import { startTransition } from "react";
import { type QueryClient } from "@tanstack/react-query";
import { type NavSection } from "@/app-shell/types";
import {
  useAddTaskArtifactMutation,
  useAddTaskCheckMutation,
  useAddTaskCommentMutation,
  useAddTaskDependencyMutation,
  useAnswerQuestionMutation,
  useBootstrapProjectMutation,
  useBootstrapProjectPreviewMutation,
  useCancelSessionMutation,
  useCreateFollowUpSessionMutation,
  useCreateQuestionMutation,
  useCreateRepositoryMutation,
  useCreateSessionMutation,
  useCreateTaskMutation,
  useCreateWorktreeMutation,
  useArchiveProjectMutation,
  usePatchTaskMutation,
  usePatchWorktreeMutation,
} from "@/features/control-plane/hooks";
import { createControlPlaneInvalidation } from "@/features/control-plane/invalidation";

type Params = {
  queryClient: QueryClient;
  selectedProjectId: string | null;
  inspectedTaskId: string | null;
  setSelectedProjectId: (projectId: string | null) => void;
  setActiveSection: (section: NavSection) => void;
  setProjectDialogOpen: (open: boolean) => void;
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
  setActiveSection,
  setProjectDialogOpen,
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
  const invalidation = createControlPlaneInvalidation({
    queryClient,
    projectId: selectedProjectId,
    taskId: inspectedTaskId,
  });

  const bootstrapProjectMutation = useBootstrapProjectMutation({
    onSuccess: (result) => {
      invalidation.invalidateProjectMutation({
        projectId: result.project.id,
        includeDashboard: true,
        includeProjects: true,
      });
      startTransition(() => {
        setActiveSection("projects");
        setSelectedProjectId(result.project.id);
        setProjectDialogOpen(false);
      });
    },
  });
  const bootstrapPreviewMutation = useBootstrapProjectPreviewMutation();

  const archiveProjectMutation = useArchiveProjectMutation({
    onSuccess: (project) => {
      const isCurrentProject = project.id === selectedProjectId;
      invalidation.invalidateProjectMutation({
        projectId: project.id,
        includeDashboard: true,
        includeProjects: true,
      });
      if (isCurrentProject) {
        setInspectedTaskId(null);
        setSelectedSessionId(null);
        setSelectedProjectId(null);
      }
      startTransition(() => {
        setActiveSection("projects");
      });
    },
  });

  const createTaskMutation = useCreateTaskMutation({
    onSuccess: () => {
      invalidation.invalidateProjectMutation({ includeDashboard: true });
      setDraftTaskTitle("");
    },
  });

  const createSubtaskMutation = useCreateTaskMutation({
    onSuccess: () => {
      invalidation.invalidateProjectMutation();
      setDraftSubtaskTitle("");
    },
  });

  const patchTaskMutation = usePatchTaskMutation({
    onSuccess: () => {
      invalidation.invalidateProjectMutation();
    },
  });

  const createRepositoryMutation = useCreateRepositoryMutation({
    onSuccess: (repository) => {
      invalidation.invalidateProjectMutation({ includeDashboard: true });
      setSelectedRepositoryId(repository.id);
      setDraftRepoPath("");
      setDraftRepoName("");
    },
  });

  const createWorktreeMutation = useCreateWorktreeMutation({
    onSuccess: () => {
      invalidation.invalidateProjectMutation();
      setDraftWorktreeLabel("");
      setSelectedTaskId("");
    },
  });

  const patchWorktreeMutation = usePatchWorktreeMutation({
    onSuccess: () => {
      invalidation.invalidateProjectMutation();
    },
  });

  const createSessionMutation = useCreateSessionMutation({
    onSuccess: (session) => {
      invalidation.invalidateSessionMutation({ includeSessionStreams: false });
      selectSession(session.id);
    },
  });

  const createFollowUpSessionMutation = useCreateFollowUpSessionMutation({
    onSuccess: (session) => {
      invalidation.invalidateSessionMutation();
      selectSession(session.id);
    },
  });

  const createQuestionMutation = useCreateQuestionMutation({
    onSuccess: (question) => {
      invalidation.invalidateProjectMutation({ includeDashboard: true });
      selectQuestion(question.id);
      setDraftQuestionPrompt("");
      setDraftQuestionReason("");
    },
  });

  const answerQuestionMutation = useAnswerQuestionMutation({
    onSuccess: (detail) => {
      invalidation.invalidateProjectMutation({
        includeDashboard: true,
        questionId: detail.id,
      });
      setDraftReplyBody("");
    },
  });

  const addTaskCommentMutation = useAddTaskCommentMutation({
    onSuccess: () => {
      invalidation.invalidateTaskDetailMutation();
      setDraftCommentBody("");
    },
  });

  const addTaskCheckMutation = useAddTaskCheckMutation({
    onSuccess: () => {
      invalidation.invalidateTaskDetailMutation();
      setDraftCheckSummary("");
    },
  });

  const addTaskArtifactMutation = useAddTaskArtifactMutation({
    onSuccess: () => {
      invalidation.invalidateTaskDetailMutation();
      setDraftArtifactName("");
      setDraftArtifactUri("");
    },
  });

  const addTaskDependencyMutation = useAddTaskDependencyMutation({
    onSuccess: () => {
      invalidation.invalidateTaskDetailMutation();
      setSelectedDependencyTaskId("");
    },
  });

  const cancelSessionMutation = useCancelSessionMutation({
    onSuccess: () => {
      invalidation.invalidateSessionMutation({ includeProjectRoot: true });
      setInspectedTaskId(null);
      setSelectedSessionId(null);
    },
  });

  return {
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
    archiveProjectMutation,
    cancelSessionMutation,
  };
}
