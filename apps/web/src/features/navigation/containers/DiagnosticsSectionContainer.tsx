import type { ReactNode } from "react";
import { Activity, Bot, FolderGit2, MessageSquareText, ShieldCheck, Terminal } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { DiagnosticsScreen } from "@/screens/DiagnosticsScreen";
import { Button } from "@/components/primitives";
import { useCleanRuntimeOrphansMutation } from "@/features/control-plane/hooks";
import { Pill, SectionFrame, SectionTitle } from "@/components/ui";
import { controlPlaneQueryKeys } from "@/features/control-plane/queryKeys";
import { toDisplay } from "@/utils/display";

function Signal({
  label,
  ready,
  icon: Icon,
  action,
}: {
  label: string;
  ready: boolean;
  icon: typeof Activity;
  action?: ReactNode;
}) {
  return (
    <div className="flex min-w-0 items-center justify-between gap-3 rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3">
      <div className="flex min-w-0 items-center gap-3">
        <Icon className="h-4 w-4 text-[color:var(--text-muted)]" />
        <span className="truncate text-sm text-[color:var(--text)]">{toDisplay(label)}</span>
      </div>
      {action ? (
        action
      ) : (
        <Pill className={ready ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}>{ready ? "Ready" : "Pending"}</Pill>
      )}
    </div>
  );
}

function DiagRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-2 rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
      <div className="text-sm text-[color:var(--text-muted)]">{label}</div>
      <div className="min-w-0 break-all text-left text-sm text-[color:var(--text)] sm:max-w-[70%] sm:text-right">{value}</div>
    </div>
  );
}

export function DiagnosticsSectionContainer({ diagnostics }: { diagnostics: any }) {
  const queryClient = useQueryClient();
  const cleanupRuntimeOrphansMutation = useCleanRuntimeOrphansMutation({
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: controlPlaneQueryKeys.diagnostics,
      });
    },
  });
  const hasOrphans = Boolean(diagnostics?.orphan_runtime_session_count);

  return (
    <>
      <DiagnosticsScreen>
        <SectionFrame className="px-5 py-5">
          <SectionTitle>Runtime readiness</SectionTitle>
          <div className="mt-5 grid gap-3">
            <Signal label="tmux" ready={Boolean(diagnostics?.tmux_available)} icon={Bot} />
            <Signal label="tmux server" ready={Boolean(diagnostics?.tmux_server_running)} icon={Terminal} />
            <Signal label="git" ready={Boolean(diagnostics?.git_available)} icon={FolderGit2} />
            <Signal
              label="runtime orphans"
              ready={!Boolean(diagnostics?.orphan_runtime_session_count)}
              icon={Activity}
              action={
                hasOrphans ? (
                  <Button
                    type="button"
                    variant="primary"
                    onClick={() => {
                      cleanupRuntimeOrphansMutation.mutate();
                    }}
                    disabled={cleanupRuntimeOrphansMutation.isPending}
                  >
                    {cleanupRuntimeOrphansMutation.isPending ? "Cleaning orphans…" : "Clean runtime orphans"}
                  </Button>
                ) : undefined
              }
            />
            <Signal label="audit log" ready icon={ShieldCheck} />
            <Signal label="waiting inbox" ready icon={MessageSquareText} />
          </div>
        </SectionFrame>
      </DiagnosticsScreen>
      <DiagnosticsScreen>
        <SectionFrame className="px-5 py-5">
          <SectionTitle>Diagnostics</SectionTitle>
          <div className="mt-4 grid gap-3">
            <DiagRow label="DB path" value={diagnostics?.database_path ?? "unknown"} />
            <DiagRow label="Runtime home" value={diagnostics?.runtime_home ?? "unknown"} />
          </div>
        </SectionFrame>
      </DiagnosticsScreen>
    </>
  );
}
