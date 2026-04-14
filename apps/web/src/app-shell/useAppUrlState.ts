import { useEffect, useRef } from "react";
import { type DetailSelection, type NavSection, validSections } from "@/app-shell/types";

type ParsedState = {
  activeSection: NavSection;
  selectedProjectId: string | null;
  inspectedTaskId: string | null;
};

type Params = {
  activeSection: NavSection;
  selectedProjectId: string | null;
  inspectedTaskId: string | null;
  setActiveSection: (section: NavSection) => void;
  setSelectedProjectId: (projectId: string | null) => void;
  setInspectedTaskId: (taskId: string | null) => void;
  setSelectedSessionId?: (sessionId: string | null) => void;
  setSelectedQuestionId?: (questionId: string | null) => void;
  setDrawerSelection?: (selection: DetailSelection | null) => void;
};

const APP_URL_STATE_STORAGE_KEY = "acp.app-url-state";

const defaultState: ParsedState = {
  activeSection: "projects",
  selectedProjectId: null,
  inspectedTaskId: null,
};

function parsePath(pathname: string): ParsedState {
  const segments = pathname.split("?")[0].split("/").filter(Boolean);
  if (!segments.length) {
    return defaultState;
  }

  const [section, projectId, nestedSection, nestedId] = segments;
  if (section === "projects") {
    if (nestedSection === "tasks" && nestedId) {
      return {
        activeSection: "projects",
        selectedProjectId: projectId ?? null,
        inspectedTaskId: nestedId,
      };
    }
    return {
      activeSection: "projects",
      selectedProjectId: projectId ?? null,
      inspectedTaskId: null,
    };
  }

  if (section === "search") {
    return { ...defaultState, activeSection: "search" };
  }
  if (section === "activity") {
    return { ...defaultState, activeSection: "activity" };
  }
  if (section === "home") {
    return { ...defaultState, activeSection: "home" };
  }
  if (section === "settings") {
    return { ...defaultState, activeSection: "settings" };
  }
  if (section === "howto") {
    return { ...defaultState, activeSection: "howto" };
  }
  return defaultState;
}

function buildPath(activeSection: NavSection, selectedProjectId: string | null, inspectedTaskId: string | null): string {
  if (activeSection === "home") return "/home";
  if (activeSection === "search") return "/search";
  if (activeSection === "activity") return "/activity";
  if (activeSection === "settings") return "/settings";
  if (activeSection === "howto") return "/howto";
  if (selectedProjectId && inspectedTaskId) {
    return `/projects/${encodeURIComponent(selectedProjectId)}/tasks/${encodeURIComponent(inspectedTaskId)}`;
  }
  if (selectedProjectId) {
    return `/projects/${encodeURIComponent(selectedProjectId)}`;
  }
  return "/projects";
}

export function useAppUrlState({
  activeSection,
  selectedProjectId,
  inspectedTaskId,
  setActiveSection,
  setSelectedProjectId,
  setInspectedTaskId,
  setDrawerSelection,
}: Params) {
  const hydratedRef = useRef(false);

  useEffect(() => {
    if (hydratedRef.current || typeof window === "undefined") {
      return;
    }
    hydratedRef.current = true;

    const parsed = parsePath(window.location.pathname);
    if (!validSections.has(parsed.activeSection)) {
      setActiveSection("projects");
    } else {
      setActiveSection(parsed.activeSection);
    }
    setSelectedProjectId(parsed.selectedProjectId);
    setInspectedTaskId(parsed.inspectedTaskId);
    setDrawerSelection?.(parsed.inspectedTaskId ? { type: "task", id: parsed.inspectedTaskId } : null);

    const raw = window.localStorage.getItem(APP_URL_STATE_STORAGE_KEY);
    if (raw) {
      try {
        const persisted = JSON.parse(raw) as ParsedState;
        if (!parsed.selectedProjectId && persisted.selectedProjectId) {
          setSelectedProjectId(persisted.selectedProjectId);
        }
      } catch {
        // ignore malformed storage payloads
      }
    }
  }, [setActiveSection, setDrawerSelection, setInspectedTaskId, setSelectedProjectId]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    if (!hydratedRef.current) {
      return;
    }
    const nextPath = buildPath(activeSection, selectedProjectId, inspectedTaskId);
    if (window.location.pathname !== nextPath) {
      window.history.replaceState(null, "", nextPath);
    }
    window.localStorage.setItem(
      APP_URL_STATE_STORAGE_KEY,
      JSON.stringify({ activeSection, selectedProjectId, inspectedTaskId }),
    );
  }, [activeSection, inspectedTaskId, selectedProjectId]);
}
