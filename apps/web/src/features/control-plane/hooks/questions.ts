import { useMutation, useQuery } from "@tanstack/react-query";
import { answerQuestion, createQuestion, getQuestion, getQuestions } from "@/lib/api/questions";
import { controlPlaneQueryKeys } from "@/features/control-plane/queryKeys";
import { type MutationHookOptions } from "@/features/control-plane/hooks/mutationTypes";

export const useQuestionsQuery = (projectId: string | null, status: string | null = null) =>
  useQuery({
    queryKey: controlPlaneQueryKeys.questions(projectId, status),
    queryFn: () =>
      getQuestions({ projectId: projectId ?? undefined, status: status ?? undefined }),
    enabled: Boolean(projectId),
  });

export const useQuestionDetailQuery = (questionId: string | null) =>
  useQuery({
    queryKey: controlPlaneQueryKeys.question(questionId),
    queryFn: () => getQuestion(questionId!),
    enabled: Boolean(questionId),
  });

export const useCreateQuestionMutation = (
  options?: MutationHookOptions<
    Awaited<ReturnType<typeof createQuestion>>,
    Parameters<typeof createQuestion>[0]
  >,
) => useMutation({ mutationFn: createQuestion, ...options });

export const useAnswerQuestionMutation = (
  options?: MutationHookOptions<
    Awaited<ReturnType<typeof answerQuestion>>,
    { questionId: string; body: string }
  >,
) =>
  useMutation({
    mutationFn: ({ questionId, body }) =>
      answerQuestion(questionId, { responder_name: "operator", body }),
    ...options,
  });
