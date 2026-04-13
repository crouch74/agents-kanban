import { useEffect } from "react";
import { type DetailSelection, type NavSection, isDetailEntityType, validSections } from "@/app-shell/types";

type Params = {
  activeSection: NavSection;
  selectedProjectId: string | null;
  inspectedTaskId: string | null;
  selectedSessionId: string | null;
  selectedQuestionId: string | null;
  drawerSelection: DetailSelection | null;
  setActiveSection: (section: NavSection) => void;
  setSelectedProjectId: (projectId: string | null) => void;
  setInspectedTaskId: (taskId: string | null) => void;
  setSelectedSessionId: (sessionId: string | null) => void;
  setSelectedQuestionId: (questionId: string | null) => void;
  setDrawerSelection: (selection: DetailSelection | null) => void;
};

export function useAppUrlState({
  activeSection,
  selectedProjectId,
  inspectedTaskId,
  selectedSessionId,
  selectedQuestionId,
  drawerSelection,
  setActiveSection,
  setSelectedProjectId,
  setInspectedTaskId,
  setSelectedSessionId,
  setSelectedQuestionId,
  setDrawerSelection,
}: Params) {
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const section = params.get("section");
    const projectId = params.get("project");
    const taskId = params.get("task");
    const sessionId = params.get("session");
    const questionId = params.get("question");
    const drawerType = params.get("drawer");
    const drawerId = params.get("drawer_id");

    if (section && validSections.has(section as NavSection)) {
      setActiveSection(section as NavSection);
    } else {
      setActiveSection("home");
    }
    setSelectedProjectId(projectId);
    setInspectedTaskId(taskId);
    setSelectedSessionId(sessionId);
    setSelectedQuestionId(questionId);
    setDrawerSelection(
      drawerId && isDetailEntityType(drawerType) ? { type: drawerType, id: drawerId } : null,
    );
  }, [
    setActiveSection,
    setDrawerSelection,
    setInspectedTaskId,
    setSelectedProjectId,
    setSelectedQuestionId,
    setSelectedSessionId,
  ]);

  useEffect(() => {
    const params = new URLSearchParams();
    params.set("section", activeSection);
    if (selectedProjectId) {
      params.set("project", selectedProjectId);
    }
    if (inspectedTaskId) {
      params.set("task", inspectedTaskId);
    }
    if (selectedSessionId) {
      params.set("session", selectedSessionId);
    }
    if (selectedQuestionId) {
      params.set("question", selectedQuestionId);
    }
    if (drawerSelection) {
      params.set("drawer", drawerSelection.type);
      params.set("drawer_id", drawerSelection.id);
    }
    const query = params.toString();
    const href = query ? `${window.location.pathname}?${query}` : `${window.location.pathname}`;
    window.history.replaceState(null, "", href);
  }, [
    activeSection,
    drawerSelection,
    inspectedTaskId,
    selectedProjectId,
    selectedQuestionId,
    selectedSessionId,
    setActiveSection,
    setDrawerSelection,
    setInspectedTaskId,
    setSelectedProjectId,
    setSelectedQuestionId,
    setSelectedSessionId,
  ]);
}
