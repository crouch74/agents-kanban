import { useMutation, useQuery } from "@tanstack/react-query";
import {
  cancelSession,
  createFollowUpSession,
  createSession,
  getSessionTail,
  getSessionTimeline,
} from "@/lib/api/sessions";
import { controlPlaneQueryKeys } from "@/features/control-plane/queryKeys";
import { type MutationHookOptions } from "@/features/control-plane/hooks/mutationTypes";

export const useSessionTailQuery = (sessionId: string | null) =>
  useQuery({
    queryKey: controlPlaneQueryKeys.sessionTail(sessionId),
    queryFn: () => getSessionTail(sessionId!),
    enabled: Boolean(sessionId),
    refetchInterval: sessionId ? 2500 : false,
  });

export const useSessionTimelineQuery = (sessionId: string | null) =>
  useQuery({
    queryKey: controlPlaneQueryKeys.sessionTimeline(sessionId),
    queryFn: () => getSessionTimeline(sessionId!),
    enabled: Boolean(sessionId),
    refetchInterval: sessionId ? 3000 : false,
  });

export const useCreateSessionMutation = (
  options?: MutationHookOptions<
    Awaited<ReturnType<typeof createSession>>,
    Parameters<typeof createSession>[0]
  >,
) => useMutation({ mutationFn: createSession, ...options });

export const useCreateFollowUpSessionMutation = (
  options?: MutationHookOptions<
    Awaited<ReturnType<typeof createFollowUpSession>>,
    { sessionId: string; profile: string; followUpType?: "retry" | "review" | "verify" | "handoff" }
  >,
) =>
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

export const useCancelSessionMutation = (
  options?: MutationHookOptions<
    Awaited<ReturnType<typeof cancelSession>>,
    Parameters<typeof cancelSession>[0]
  >,
) => useMutation({ mutationFn: cancelSession, ...options });
