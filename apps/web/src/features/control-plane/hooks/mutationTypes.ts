import { type UseMutationOptions } from "@tanstack/react-query";

export type MutationHookOptions<TData, TVars> = Omit<
  UseMutationOptions<TData, Error, TVars>,
  "mutationFn"
>;
