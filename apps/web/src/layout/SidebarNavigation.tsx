import type { RefObject } from "react";
import { ProjectBootstrapWizard } from "@/components/project-bootstrap-wizard";
import { Pill, SectionTitle } from "@/components/ui";
import { navItems, type NavSection } from "@/app-shell/types";

export function SidebarNavigation({
  activeSection,
  setActiveSection,
  filteredProjects,
  selectedProjectId,
  setSelectedProjectId,
  setProjectsSection,
  bootstrapWizardRef,
  bootstrapProjectMutation,
}: {
  activeSection: NavSection;
  setActiveSection: (section: NavSection) => void;
  filteredProjects: Array<{ id: string; name: string }>;
  selectedProjectId: string | null;
  setSelectedProjectId: (projectId: string) => void;
  setProjectsSection: () => void;
  bootstrapWizardRef: RefObject<HTMLDivElement | null>;
  bootstrapProjectMutation: any;
}) {
  return (
    <>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Agent Control Plane</p>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight">Local operator workspace</h1>
        </div>
        <Pill className="border-emerald-400/20 bg-emerald-400/10 text-emerald-200">v0.1</Pill>
      </div>

      <div className="mt-8">
        <SectionTitle>Navigation</SectionTitle>
        <div className="mt-3 flex flex-col gap-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.key}
                onClick={() => setActiveSection(item.key)}
                className={[
                  "flex items-center gap-3 rounded-2xl border px-4 py-3 text-left text-sm transition",
                  activeSection === item.key
                    ? "border-[color:var(--color-accent-primary)] bg-[color:var(--color-accent-soft)] text-slate-100"
                    : "border-white/7 bg-white/2 text-slate-400 hover:bg-white/5",
                ].join(" ")}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-8">
        <SectionTitle>Projects</SectionTitle>
        <div className="mt-3 flex flex-col gap-2">
          {filteredProjects.slice(0, 6).map((project) => (
            <button
              key={project.id}
              onClick={() => {
                setSelectedProjectId(project.id);
                setProjectsSection();
              }}
              className={[
                "rounded-2xl border px-3 py-3 text-left text-sm",
                selectedProjectId === project.id
                  ? "border-[color:var(--color-accent-primary)] bg-[color:var(--color-accent-soft)]"
                  : "border-white/7 bg-white/2",
              ].join(" ")}
            >
              <div className="font-semibold text-slate-100">{project.name}</div>
            </button>
          ))}
        </div>
      </div>

      <div ref={bootstrapWizardRef}>
        <ProjectBootstrapWizard
          isPending={bootstrapProjectMutation.isPending}
          errorMessage={bootstrapProjectMutation.error instanceof Error ? bootstrapProjectMutation.error.message : undefined}
          result={bootstrapProjectMutation.data as never}
          onSubmit={(payload) => bootstrapProjectMutation.mutate(payload)}
        />
      </div>
    </>
  );
}
