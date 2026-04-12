import { useQuery } from "@tanstack/react-query";
import { getDashboard, getDiagnostics, getEvents, searchContext } from "@/lib/api/system";
import { controlPlaneQueryKeys } from "@/features/control-plane/queryKeys";

export const useDashboardQuery = () =>
  useQuery({ queryKey: controlPlaneQueryKeys.dashboard, queryFn: getDashboard });

export const useDiagnosticsQuery = () =>
  useQuery({ queryKey: controlPlaneQueryKeys.diagnostics, queryFn: getDiagnostics });

export const useEventsQuery = (projectId: string | null) =>
  useQuery({
    queryKey: controlPlaneQueryKeys.events(projectId),
    queryFn: () => getEvents({ projectId: projectId ?? undefined, limit: 18 }),
  });

export const useSearchQuery = (deferredSearch: string, projectId?: string | null) =>
  useQuery({
    queryKey: controlPlaneQueryKeys.search(deferredSearch, projectId),
    queryFn: () => searchContext(deferredSearch, projectId ?? undefined),
    enabled: deferredSearch.trim().length >= 2,
  });
