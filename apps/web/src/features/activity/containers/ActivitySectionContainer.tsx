import { ActivityScreen } from "@/screens/ActivityScreen";
import type { EventRecord } from "@/lib/api";

export function ActivitySectionContainer({
  events,
  loading,
  error,
  projectOptions,
  taskOptions,
  sessionOptions,
}: {
  events: EventRecord[];
  loading: boolean;
  error: string | null;
  projectOptions: Array<{ value: string; label: string }>;
  taskOptions: Array<{ value: string; label: string }>;
  sessionOptions: Array<{ value: string; label: string }>;
}) {
  return (
    <ActivityScreen
      active
      events={events}
      loading={loading}
      error={error}
      projectOptions={projectOptions}
      taskOptions={taskOptions}
      sessionOptions={sessionOptions}
    />
  );
}
