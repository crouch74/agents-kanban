import { Separator } from "@radix-ui/react-separator";
import { navItems, type NavSection } from "@/app-shell/types";
import { ShellNavItem } from "@/components/ui";

export function SidebarNavigation({
  activeSection,
  setActiveSection,
}: {
  activeSection: NavSection;
  setActiveSection: (section: NavSection) => void;
}) {
  const workspaceItems = navItems.slice(0, 3);
  const systemItems = navItems.slice(3);
  const effectiveActiveSection =
    activeSection === "sessions" || activeSection === "worktrees"
      ? "projects"
      : activeSection;

  return (
    <div className="flex h-full flex-col">
      <div className="space-y-1">
        {workspaceItems.map((item, index) => (
          <ShellNavItem
            key={`${item.key}-${index}`}
            active={effectiveActiveSection === item.key}
            icon={item.icon}
            label={item.label}
            onClick={() => setActiveSection(item.key)}
          />
        ))}
      </div>
      <Separator className="my-3 h-px bg-[color:var(--border)]" />
      <div className="space-y-1">
        {systemItems.map((item, index) => (
          <ShellNavItem
            key={`${item.label}-${index}`}
            active={effectiveActiveSection === item.key}
            icon={item.icon}
            label={item.label}
            onClick={() => setActiveSection(item.key)}
          />
        ))}
      </div>
      <div className="mt-auto px-3 text-[11px] text-[color:var(--text-faint)]">v0.1</div>
    </div>
  );
}
