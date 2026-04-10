import { useState, type FormEvent } from "react";
import type { ProjectBootstrapResult, StackPreset } from "@acp/sdk";
import { ArrowRight, CheckCircle2, GitBranch, TerminalSquare } from "lucide-react";
import { Pill, SectionTitle } from "@/components/ui";

const STACK_OPTIONS: Array<{ value: StackPreset; label: string }> = [
  { value: "node-library", label: "Node library" },
  { value: "react-vite", label: "React + Vite" },
  { value: "nextjs", label: "Next.js" },
  { value: "python-package", label: "Python package" },
  { value: "fastapi-service", label: "FastAPI service" },
];

type BootstrapPayload = {
  name: string;
  description?: string;
  repo_path: string;
  initialize_repo?: boolean;
  stack_preset: StackPreset;
  stack_notes?: string;
  initial_prompt: string;
  use_worktree?: boolean;
};

export function ProjectBootstrapWizard({
  isPending,
  errorMessage,
  result,
  onSubmit,
}: {
  isPending: boolean;
  errorMessage?: string;
  result?: ProjectBootstrapResult;
  onSubmit: (payload: BootstrapPayload) => void;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [repoPath, setRepoPath] = useState("");
  const [initializeRepo, setInitializeRepo] = useState(false);
  const [stackPreset, setStackPreset] = useState<StackPreset>("nextjs");
  const [stackNotes, setStackNotes] = useState("");
  const [initialPrompt, setInitialPrompt] = useState("");
  const [useWorktree, setUseWorktree] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit({
      name,
      description: description || undefined,
      repo_path: repoPath,
      initialize_repo: initializeRepo,
      stack_preset: stackPreset,
      stack_notes: stackNotes || undefined,
      initial_prompt: initialPrompt,
      use_worktree: useWorktree,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="mt-8 rounded-3xl border border-white/7 bg-white/2 p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <SectionTitle>New Project Bootstrap</SectionTitle>
          <div className="mt-2 text-sm text-slate-500">
            Create the project, prepare the repo, and launch the kickoff Codex session.
          </div>
        </div>
        <Pill className="border-white/8 text-slate-300">{useWorktree ? "worktree" : "repo branch"}</Pill>
      </div>

      <input
        value={name}
        onChange={(event) => setName(event.target.value)}
        placeholder="Acme migration program"
        className="mt-4 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
      />
      <input
        value={description}
        onChange={(event) => setDescription(event.target.value)}
        placeholder="Optional project description"
        className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
      />
      <input
        value={repoPath}
        onChange={(event) => setRepoPath(event.target.value)}
        placeholder="/absolute/path/to/repo"
        className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
      />
      <select
        value={stackPreset}
        onChange={(event) => setStackPreset(event.target.value as StackPreset)}
        className="mt-3 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
      >
        {STACK_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <textarea
        value={stackNotes}
        onChange={(event) => setStackNotes(event.target.value)}
        placeholder="Optional stack notes or constraints"
        className="mt-3 min-h-20 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
      />
      <textarea
        value={initialPrompt}
        onChange={(event) => setInitialPrompt(event.target.value)}
        placeholder="Describe the work to kick off. ACP will ask the agent to clarify requirements and create tasks/subtasks."
        className="mt-3 min-h-32 w-full rounded-2xl border border-white/8 bg-black/15 px-3 py-3 text-sm outline-none"
      />

      <label className="mt-3 flex items-center gap-3 rounded-2xl border border-white/8 bg-black/10 px-3 py-3 text-sm text-slate-300">
        <input
          type="checkbox"
          checked={initializeRepo}
          onChange={(event) => setInitializeRepo(event.target.checked)}
          className="h-4 w-4 rounded border-white/8 bg-transparent"
        />
        Initialize repo with `git init` when the folder is empty
      </label>
      <label className="mt-3 flex items-center gap-3 rounded-2xl border border-white/8 bg-black/10 px-3 py-3 text-sm text-slate-300">
        <input
          type="checkbox"
          checked={useWorktree}
          onChange={(event) => setUseWorktree(event.target.checked)}
          className="h-4 w-4 rounded border-white/8 bg-transparent"
        />
        Use worktree for kickoff instead of the repo’s current branch
      </label>

      {errorMessage ? (
        <div className="mt-3 rounded-2xl border border-rose-300/20 bg-rose-300/10 px-3 py-3 text-sm text-rose-100">
          {errorMessage}
        </div>
      ) : null}

      <button
        type="submit"
        disabled={!name.trim() || !repoPath.trim() || !initialPrompt.trim() || isPending}
        className="mt-4 inline-flex items-center gap-2 rounded-full bg-[color:var(--color-accent-primary)] px-4 py-2 text-sm font-semibold text-slate-900 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Launch bootstrap
        <ArrowRight className="h-4 w-4" />
      </button>

      {result ? (
        <div className="mt-5 rounded-2xl border border-emerald-300/15 bg-emerald-300/10 px-4 py-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-emerald-100">
            <CheckCircle2 className="h-4 w-4" />
            {result.project.name} is ready
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Pill className="border-emerald-300/20 text-emerald-100">{result.stack_preset}</Pill>
            <Pill className="border-emerald-300/20 text-emerald-100">
              {result.use_worktree ? "worktree kickoff" : "repo kickoff"}
            </Pill>
            {result.repo_initialized ? <Pill className="border-emerald-300/20 text-emerald-100">git initialized</Pill> : null}
            {result.scaffold_applied ? <Pill className="border-emerald-300/20 text-emerald-100">scaffolded</Pill> : null}
          </div>
          <div className="mt-3 space-y-2 text-sm text-emerald-50">
            <div className="flex items-center gap-2">
              <GitBranch className="h-4 w-4" />
              {result.execution_branch}
            </div>
            <div className="break-all text-emerald-100/90">{result.execution_path}</div>
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
