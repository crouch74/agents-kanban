import { navItems, type NavSection } from "@/app-shell/types";
import { ShellNavItem } from "@/components/ui";

export function SidebarNavigation({
  activeSection,
  setActiveSection,
}: {
  activeSection: NavSection;
  setActiveSection: (section: NavSection) => void;
}) {
  return (
    <div className="flex h-full flex-col">
      <div className="space-y-1">
        {navItems.map((item, index) => (
          <ShellNavItem
            key={`${item.key}-${index}`}
            active={activeSection === item.key}
            icon={item.icon}
            label={item.label}
            onClick={() => setActiveSection(item.key)}
          />
        ))}
      </div>
      <div className="mt-auto px-3 text-[11px] text-[color:var(--text-faint)]">v0.2</div>
    </div>
  );
}
