import { useMutation, useQuery } from "@tanstack/react-query";
import {
  bootstrapProject,
  getProject,
  getProjects,
  previewBootstrapProject,
} from "@/lib/api/projects";
import { createRepository } from "@/lib/api/repositories";
import { createWorktree, patchWorktree } from "@/lib/api/worktrees";
import { controlPlaneQueryKeys } from "@/features/control-plane/queryKeys";
import { type MutationHookOptions } from "@/features/control-plane/hooks/mutationTypes";

export const useProjectsQuery = () =>
  useQuery({ queryKey: controlPlaneQueryKeys.projects, queryFn: getProjects });

export const useProjectDetailQuery = (projectId: string | null) =>
  useQuery({
    queryKey: controlPlaneQueryKeys.project(projectId),
    queryFn: () => getProject(projectId!),
    enabled: Boolean(projectId),
  });

export const useBootstrapProjectMutation = (
  options?: MutationHookOptions<
    Awaited<ReturnType<typeof bootstrapProject>>,
    Parameters<typeof bootstrapProject>[0]
  >,
) => useMutation({ mutationFn: bootstrapProject, ...options });

export const useBootstrapProjectPreviewMutation = (
  options?: MutationHookOptions<
    Awaited<ReturnType<typeof previewBootstrapProject>>,
    Parameters<typeof previewBootstrapProject>[0]
  >,
) => useMutation({ mutationFn: previewBootstrapProject, ...options });

export const useCreateRepositoryMutation = (
  options?: MutationHookOptions<
    Awaited<ReturnType<typeof createRepository>>,
    Parameters<typeof createRepository>[0]
  >,
) => useMutation({ mutationFn: createRepository, ...options });

export const useCreateWorktreeMutation = (
  options?: MutationHookOptions<
    Awaited<ReturnType<typeof createWorktree>>,
    Parameters<typeof createWorktree>[0]
  >,
) => useMutation({ mutationFn: createWorktree, ...options });

export const usePatchWorktreeMutation = (
  options?: MutationHookOptions<
    Awaited<ReturnType<typeof patchWorktree>>,
    { worktreeId: string; status: string }
  >,
) =>
  useMutation({
    mutationFn: ({ worktreeId, status }) => patchWorktree(worktreeId, { status }),
    ...options,
  });
