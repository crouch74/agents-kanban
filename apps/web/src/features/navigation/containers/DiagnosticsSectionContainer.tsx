import { Activity, Bot, FolderGit2, MessageSquareText, ShieldCheck, Terminal } from "lucide-react";
import { DiagnosticsScreen } from "@/screens/DiagnosticsScreen";
import { Pill, SectionFrame, SectionTitle } from "@/components/ui";
import { toDisplay } from "@/utils/display";

function Signal({ label, ready, icon: Icon }: { label: string; ready: boolean; icon: typeof Activity }) {
  return (
    <div className="flex items-center justify-between rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3">
      <div className="flex items-center gap-3">
        <Icon className="h-4 w-4 text-[color:var(--text-muted)]" />
        <span className="text-sm text-[color:var(--text)]">{toDisplay(label)}</span>
      </div>
      <Pill className={ready ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}>{ready ? "Ready" : "Pending"}</Pill>
    </div>
  );
}

function DiagRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-[6px] border border-[color:var(--border)] bg-[color:var(--surface)] px-4 py-3">
      <div className="text-sm text-[color:var(--text-muted)]">{label}</div>
      <div className="max-w-[60%] break-all text-right text-sm text-[color:var(--text)]">{value}</div>
    </div>
  );
}

export function DiagnosticsSectionContainer({ diagnostics }: { diagnostics: any }) {
  return (
    <>
      <DiagnosticsScreen>
        <SectionFrame className="px-5 py-5">
          <SectionTitle>Runtime readiness</SectionTitle>
          <div className="mt-5 grid gap-3">
            <Signal label="tmux" ready={Boolean(diagnostics?.tmux_available)} icon={Bot} />
            <Signal label="tmux server" ready={Boolean(diagnostics?.tmux_server_running)} icon={Terminal} />
            <Signal label="git" ready={Boolean(diagnostics?.git_available)} icon={FolderGit2} />
            <Signal label="runtime orphans" ready={!Boolean(diagnostics?.orphan_runtime_session_count)} icon={Activity} />
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
