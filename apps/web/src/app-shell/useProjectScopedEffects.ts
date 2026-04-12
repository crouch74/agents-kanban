import { useEffect } from "react";
import type { ProjectSummary, WaitingQuestionSummary } from "@acp/sdk";
import type { ProjectOverview } from "@/lib/api";
import type { DetailSelection } from "@/app-shell/types";

type Params = {
  projects: ProjectSummary[] | undefined;
  selectedProjectId: string | null;
  setSelectedProjectId: (projectId: string | null) => void;
  repositories: ProjectOverview["repositories"] | undefined;
  selectedRepositoryId: string | null;
  setSelectedRepositoryId: (repositoryId: string | null) => void;
  questions: WaitingQuestionSummary[] | undefined;
  selectedQuestionId: string | null;
  setSelectedQuestionId: (questionId: string | null) => void;
  setSelectedTaskId: (taskId: string) => void;
  setSelectedSessionTaskId: (taskId: string) => void;
  setSelectedSessionWorktreeId: (worktreeId: string) => void;
  setSelectedSessionId: (sessionId: string | null) => void;
  setInspectedTaskId: (taskId: string | null) => void;
  setDrawerSelection: (selection: DetailSelection | null) => void;
};

export function useProjectScopedEffects({
  projects,
  selectedProjectId,
  setSelectedProjectId,
  repositories,
  selectedRepositoryId,
  setSelectedRepositoryId,
  questions,
  selectedQuestionId,
  setSelectedQuestionId,
  setSelectedTaskId,
  setSelectedSessionTaskId,
  setSelectedSessionWorktreeId,
  setSelectedSessionId,
  setInspectedTaskId,
  setDrawerSelection,
}: Params) {
  useEffect(() => {
    if (!selectedProjectId && projects?.[0]) {
      setSelectedProjectId(projects[0].id);
    }
  }, [projects, selectedProjectId, setSelectedProjectId]);

  useEffect(() => {
    setSelectedRepositoryId(null);
    setSelectedTaskId("");
    setSelectedSessionTaskId("");
    setSelectedSessionWorktreeId("");
    setSelectedSessionId(null);
    setSelectedQuestionId(null);
    setInspectedTaskId(null);
    setDrawerSelection(null);
  }, [
    selectedProjectId,
    setDrawerSelection,
    setInspectedTaskId,
    setSelectedQuestionId,
    setSelectedRepositoryId,
    setSelectedSessionId,
    setSelectedSessionTaskId,
    setSelectedSessionWorktreeId,
    setSelectedTaskId,
  ]);

  useEffect(() => {
    if (!selectedRepositoryId && repositories?.[0]) {
      setSelectedRepositoryId(repositories[0].id);
    }
  }, [repositories, selectedRepositoryId, setSelectedRepositoryId]);

  useEffect(() => {
    const isCurrentStillAvailable = (questions ?? []).some(
      (question) => question.id === selectedQuestionId,
    );
    if (!isCurrentStillAvailable && questions?.[0]) {
      setSelectedQuestionId(questions[0].id);
    }
  }, [questions, selectedQuestionId, setSelectedQuestionId]);
}
