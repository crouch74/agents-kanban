import { useEffect, useMemo, useState, type FormEvent } from "react";
import type { ProjectBootstrapPreview, ProjectBootstrapResult, StackPreset } from "@acp/sdk";
import { ArrowRight, CheckCircle2, GitBranch, TerminalSquare } from "lucide-react";
import { Badge, Button, Input, Select, Textarea } from "@/components/primitives";

const STACK_OPTIONS: Array<{ value: StackPreset; label: string }> = [
  { value: "node-library", label: "Node library" },
  { value: "react-vite", label: "React + Vite" },
  { value: "nextjs", label: "Next.js" },
  { value: "python-package", label: "Python package" },
  { value: "fastapi-service", label: "FastAPI service" },
];

const AGENT_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "", label: "Default (from settings)" },
  { value: "codex", label: "Codex" },
  { value: "claude-code", label: "Claude Code" },
  { value: "aider", label: "Aider" },
];

type BootstrapPayload = {
  name: string;
  description?: string;
  repo_path: string;
  initialize_repo?: boolean;
  stack_preset: StackPreset;
  stack_notes?: string;
  initial_prompt: string;
  agent_name?: string;
  use_worktree?: boolean;
};

export function ProjectBootstrapWizard({
  isPreviewPending,
  isConfirmPending,
  errorMessage,
  result,
  onPreview,
  onConfirm,
}: {
  isPreviewPending: boolean;
  isConfirmPending: boolean;
  errorMessage?: string;
  result?: ProjectBootstrapResult;
  onPreview: (payload: BootstrapPayload) => Promise<ProjectBootstrapPreview>;
  onConfirm: (payload: BootstrapPayload & { confirm_existing_repo?: boolean }) => Promise<ProjectBootstrapResult>;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [repoPath, setRepoPath] = useState("");
  const [initializeRepo, setInitializeRepo] = useState(false);
  const [stackPreset, setStackPreset] = useState<StackPreset>("nextjs");
  const [stackNotes, setStackNotes] = useState("");
  const [initialPrompt, setInitialPrompt] = useState("");
  const [agentName, setAgentName] = useState("");
  const [useWorktree, setUseWorktree] = useState(false);
  const [preview, setPreview] = useState<ProjectBootstrapPreview | null>(null);
  const [previewSignature, setPreviewSignature] = useState<string | null>(null);

  const payload = useMemo(
    () => ({
      name,
      description: description || undefined,
      repo_path: repoPath,
      initialize_repo: initializeRepo,
      stack_preset: stackPreset,
      stack_notes: stackNotes || undefined,
      initial_prompt: initialPrompt,
      agent_name: agentName || undefined,
      use_worktree: useWorktree,
    }),
    [
      description,
      initialPrompt,
      initializeRepo,
      name,
      repoPath,
      stackNotes,
      stackPreset,
      useWorktree,
      agentName,
    ],
  );
  const payloadSignature = useMemo(() => JSON.stringify(payload), [payload]);
  const awaitingConfirmation = Boolean(preview?.confirmation_required && previewSignature === payloadSignature);

  useEffect(() => {
    if (result) {
      setPreview(null);
      setPreviewSignature(null);
    }
  }, [result]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (awaitingConfirmation) {
      await onConfirm({ ...payload, confirm_existing_repo: true });
      return;
    }
    const nextPreview = await onPreview(payload);
    setPreview(nextPreview);
    setPreviewSignature(payloadSignature);
    if (!nextPreview.confirmation_required) {
      await onConfirm(payload);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <div className="text-sm font-medium text-[color:var(--text)]">New project</div>
        <div className="mt-1 text-sm text-[color:var(--text-muted)]">
          Create the project, attach the repository, and launch the kickoff session.
        </div>
      </div>

      <Input
        value={name}
        onChange={(event) => setName(event.target.value)}
        placeholder="Acme migration program"
      />
      <Input
        value={description}
        onChange={(event) => setDescription(event.target.value)}
        placeholder="Optional project description"
      />
      <Input
        value={repoPath}
        onChange={(event) => setRepoPath(event.target.value)}
        placeholder="/absolute/path/to/repo"
      />
      <Select
        value={stackPreset}
        onChange={(event) => setStackPreset(event.target.value as StackPreset)}
      >
        {STACK_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </Select>
      <Textarea
        value={stackNotes}
        onChange={(event) => setStackNotes(event.target.value)}
        placeholder="Optional stack notes or constraints"
        className="min-h-20"
      />
      <Select
        value={agentName}
        onChange={(event) => setAgentName(event.target.value)}
      >
        {AGENT_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </Select>
      <Textarea
        value={initialPrompt}
        onChange={(event) => setInitialPrompt(event.target.value)}
        placeholder="Describe the work to kick off. ACP will ask the agent to clarify requirements and create tasks/subtasks."
        className="min-h-28"
      />

      <label className="flex items-center gap-2 rounded-[4px] border border-[color:var(--border)] bg-[color:var(--surface-2)] px-3 py-2 text-sm text-[color:var(--text-muted)]">
        <input
          type="checkbox"
          checked={initializeRepo}
          onChange={(event) => setInitializeRepo(event.target.checked)}
          className="h-4 w-4 rounded-[4px]"
        />
        Initialize repo with `git init` when the folder is empty
      </label>
      <label className="flex items-center gap-2 rounded-[4px] border border-[color:var(--border)] bg-[color:var(--surface-2)] px-3 py-2 text-sm text-[color:var(--text-muted)]">
        <input
          type="checkbox"
          checked={useWorktree}
          onChange={(event) => setUseWorktree(event.target.checked)}
          className="h-4 w-4 rounded-[4px]"
        />
        Use worktree for kickoff instead of the repo branch
      </label>

      {errorMessage ? (
        <div className="rounded-[4px] border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {errorMessage}
        </div>
      ) : null}

      {preview?.confirmation_required ? (
        <div className="rounded-[6px] border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-900">
          <div className="font-semibold">Review planned repo changes before kickoff</div>
          <div className="mt-2 text-[color:inherit]">
            ACP detected an existing repository and will only proceed after explicit confirmation.
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Badge variant="info">{preview.use_worktree ? "worktree kickoff" : "repo kickoff"}</Badge>
            {preview.repo_initialized_on_confirm ? <Badge variant="info">git init on confirm</Badge> : null}
            {preview.scaffold_applied_on_confirm ? <Badge variant="info">starter scaffold on confirm</Badge> : null}
          </div>
          <div
            data-testid="bootstrap-preview-scroll-region"
            className="mt-3 max-h-64 space-y-2 overflow-y-auto pr-1"
          >
            {preview.planned_changes.map((change) => (
              <div key={`${change.path}:${change.action}`} className="rounded-[4px] border border-amber-200 bg-white/70 px-3 py-2">
                <div className="font-medium">{change.path}</div>
                <div className="text-xs uppercase tracking-[0.12em] text-amber-700">{change.action.replaceAll("_", " ")}</div>
                <div className="mt-1 text-sm">{change.description}</div>
              </div>
            ))}
          </div>
          <div className="mt-3 flex items-center gap-2 text-xs text-amber-800">
            <GitBranch className="h-3.5 w-3.5" />
            {preview.execution_branch}
          </div>
          <div className="mt-1 break-all text-xs text-amber-800">{preview.execution_path}</div>
        </div>
      ) : null}

      <div className="flex items-center justify-end gap-2">
        <Button
          type="submit"
          variant="primary"
          disabled={!name.trim() || !repoPath.trim() || !initialPrompt.trim() || isPreviewPending || isConfirmPending}
        >
          {awaitingConfirmation ? "Confirm + launch bootstrap" : "Review bootstrap"}
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>

      {result ? (
        <div className="rounded-[6px] border border-emerald-200 bg-emerald-50 px-4 py-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-emerald-700">
            <CheckCircle2 className="h-4 w-4" />
            {result.project.name} is ready
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Badge variant="success">{result.stack_preset}</Badge>
            <Badge variant="success">{result.use_worktree ? "worktree kickoff" : "repo kickoff"}</Badge>
            {result.repo_initialized ? <Badge variant="success">git initialized</Badge> : null}
            {result.scaffold_applied ? <Badge variant="success">scaffolded</Badge> : null}
          </div>
          <div className="mt-3 space-y-2 text-sm text-emerald-800">
            <div className="flex items-center gap-2">
              <GitBranch className="h-4 w-4" />
              {result.execution_branch}
            </div>
            <div className="break-all">{result.execution_path}</div>
            <div className="flex items-center gap-2">
              <TerminalSquare className="h-4 w-4" />
              {result.kickoff_session.session_name}
            </div>
            <div>Kickoff task: {result.kickoff_task.title}</div>
            {result.kickoff_worktree ? <div>Kickoff worktree: {result.kickoff_worktree.branch_name}</div> : null}
          </div>
        </div>
      ) : null}
    </form>
  );
}
