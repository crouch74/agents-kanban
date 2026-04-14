import { useState, type FormEvent } from "react";
import { Button, Input, Textarea } from "@/components/primitives";

export function ProjectBootstrapWizard({
  isPending,
  errorMessage,
  onCreate,
}: {
  isPending: boolean;
  errorMessage?: string;
  onCreate: (payload: { name: string; description?: string }) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onCreate({ name: name.trim(), description: description.trim() || undefined });
    setName("");
    setDescription("");
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <div className="text-sm font-medium text-[color:var(--text)]">New project</div>
        <div className="mt-1 text-sm text-[color:var(--text-muted)]">
          Create a project and start managing tasks on its board.
        </div>
      </div>

      <Input
        value={name}
        onChange={(event) => setName(event.target.value)}
        placeholder="Acme migration program"
      />
      <Textarea
        value={description}
        onChange={(event) => setDescription(event.target.value)}
        placeholder="Optional project description"
        className="min-h-24"
      />

      {errorMessage ? (
        <div className="rounded-[4px] border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
          {errorMessage}
        </div>
      ) : null}

      <div className="flex items-center justify-end gap-2">
        <Button
          type="submit"
          variant="primary"
          disabled={!name.trim() || isPending}
        >
          Create project
        </Button>
      </div>
    </form>
  );
}
