import { Activity, BookOpen, ClipboardList, FolderKanban, Search, Settings, type LucideIcon } from "lucide-react";

export type NavSection = "home" | "projects" | "search" | "activity" | "settings" | "howto";

export type DetailEntityType = "task";

export type DetailSelection = {
  type: DetailEntityType;
  id: string;
};

export const validSections = new Set<NavSection>([
  "home",
  "projects",
  "search",
  "activity",
  "settings",
  "howto",
]);

export function isDetailEntityType(value: string | null): value is DetailEntityType {
  return value === "task";
}

export const navItems: Array<{ key: NavSection; label: string; icon: LucideIcon }> = [
  { key: "home", label: "Home", icon: ClipboardList },
  { key: "projects", label: "Projects", icon: FolderKanban },
  { key: "search", label: "Search", icon: Search },
  { key: "activity", label: "Activity", icon: Activity },
  { key: "settings", label: "Settings", icon: Settings },
  { key: "howto", label: "How-To", icon: BookOpen },
];

export const sectionTitleByKey: Record<NavSection, string> = {
  home: "Home",
  projects: "Projects",
  search: "Search",
  activity: "Activity",
  settings: "Settings",
  howto: "How-To",
};
