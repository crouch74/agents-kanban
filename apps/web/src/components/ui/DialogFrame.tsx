import type { ReactNode } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";

export function DialogFrame({
  open,
  onOpenChange,
  title,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  children: ReactNode;
}) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-[70] bg-black/20" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-[80] flex max-h-[calc(100vh-32px)] w-[min(640px,calc(100vw-32px))] -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-[8px] border border-[color:var(--border)] bg-[color:var(--surface)] p-4 shadow-[var(--shadow-panel)]">
          <div className="flex items-center justify-between gap-3">
            <Dialog.Title className="text-base font-semibold text-[color:var(--text)]">
              {title}
            </Dialog.Title>
            <Dialog.Close className="btn-ghost !h-7 !px-1" aria-label="Close dialog">
              <X className="h-4 w-4" />
            </Dialog.Close>
          </div>
          <Dialog.Description className="sr-only">
            Dialog content for {title}
          </Dialog.Description>
          <div className="mt-4 min-h-0 flex-1 overflow-y-auto pr-1">{children}</div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
