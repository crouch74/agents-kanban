import type { ReactNode } from "react";
import { SectionFrame, SectionTitle } from "@/components/ui";

export function SessionsSectionContainer({ active, children }: { active: boolean; children: ReactNode }) {
  if (!active) return null;
  return (
    <SectionFrame className="px-5 py-5">
      <SectionTitle>Session Runtime</SectionTitle>
      {children}
    </SectionFrame>
  );
}
