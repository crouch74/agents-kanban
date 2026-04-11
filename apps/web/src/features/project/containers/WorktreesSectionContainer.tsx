import type { ComponentProps } from "react";
import { WorktreeInventoryScreen } from "@/screens/WorktreeInventoryScreen";

export function WorktreesSectionContainer(props: ComponentProps<typeof WorktreeInventoryScreen>) {
  return <WorktreeInventoryScreen {...props} />;
}
