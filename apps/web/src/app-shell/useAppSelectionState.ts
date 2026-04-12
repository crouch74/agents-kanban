import { useState } from "react";
import type { DetailSelection, NavSection } from "@/app-shell/types";

export function useAppSelectionState() {
  const [selectedRepositoryId, setSelectedRepositoryId] = useState<string | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string>("");
  const [selectedSessionTaskId, setSelectedSessionTaskId] = useState<string>("");
  const [selectedSessionWorktreeId, setSelectedSessionWorktreeId] = useState<string>("");
  const [sessionProfile, setSessionProfile] = useState("executor");
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [selectedQuestionId, setSelectedQuestionId] = useState<string | null>(null);
  const [inspectedTaskId, setInspectedTaskId] = useState<string | null>(null);
  const [selectedDependencyTaskId, setSelectedDependencyTaskId] = useState("");
  const [activeSection, setActiveSection] = useState<NavSection>("home");
  const [drawerSelection, setDrawerSelection] = useState<DetailSelection | null>(null);
  const [projectDialogOpen, setProjectDialogOpen] = useState(false);
  const [mobileTaskPanelOpen, setMobileTaskPanelOpen] = useState(false);
  const [openTaskSections, setOpenTaskSections] = useState<Record<string, boolean>>({});

  return {
    selectedRepositoryId,
    setSelectedRepositoryId,
    selectedTaskId,
    setSelectedTaskId,
    selectedSessionTaskId,
    setSelectedSessionTaskId,
    selectedSessionWorktreeId,
    setSelectedSessionWorktreeId,
    sessionProfile,
    setSessionProfile,
    selectedSessionId,
    setSelectedSessionId,
    selectedQuestionId,
    setSelectedQuestionId,
    inspectedTaskId,
    setInspectedTaskId,
    selectedDependencyTaskId,
    setSelectedDependencyTaskId,
    activeSection,
    setActiveSection,
    drawerSelection,
    setDrawerSelection,
    projectDialogOpen,
    setProjectDialogOpen,
    mobileTaskPanelOpen,
    setMobileTaskPanelOpen,
    openTaskSections,
    setOpenTaskSections,
  };
}
