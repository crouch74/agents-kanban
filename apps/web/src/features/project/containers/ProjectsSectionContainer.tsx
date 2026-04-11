import type { ReactNode } from "react";
import { ProjectBoardScreen } from "@/screens/ProjectBoardScreen";

export function ProjectsSectionContainer({ active, children }: { active: boolean; children: ReactNode }) {
  if (!active) return null;
  return <ProjectBoardScreen>{children}</ProjectBoardScreen>;
}
