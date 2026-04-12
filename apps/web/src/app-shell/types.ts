import { FolderGit2, Home, Inbox, Settings, type LucideIcon } from "lucide-react";

export type NavSection =
  | "home"
  | "projects"
  | "waiting"
  | "sessions"
  | "worktrees"
  | "search"
  | "activity"
  | "diagnostics";

export type DetailEntityType = "task" | "session" | "worktree" | "question";

export type DetailSelection = {
  type: DetailEntityType;
  id: string;
};

export const validSections = new Set<NavSection>([
  "home",
  "projects",
  "waiting",
  "sessions",
  "worktrees",
  "search",
  "activity",
  "diagnostics",
]);

export function isDetailEntityType(value: string | null): value is DetailEntityType {
  return value === "task" || value === "session" || value === "worktree" || value === "question";
}

export const navItems: Array<{ key: NavSection; label: string; icon: LucideIcon }> = [
  { key: "home", label: "Home", icon: Home },
  { key: "projects", label: "Projects", icon: FolderGit2 },
  { key: "waiting", label: "Inbox", icon: Inbox },
  { key: "diagnostics", label: "Settings", icon: Settings },
];

export const sectionTitleByKey: Record<NavSection, string> = {
  home: "Home",
  projects: "Projects",
  waiting: "Inbox",
  sessions: "Sessions",
  worktrees: "Worktrees",
  search: "Search",
  activity: "Activity",
  diagnostics: "Settings",
};
