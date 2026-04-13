import { useEffect } from "react";
import { type DetailSelection, type NavSection, validSections } from "@/app-shell/types";

type ParsedState = {
  activeSection: NavSection;
  selectedProjectId: string | null;
  inspectedTaskId: string | null;
  selectedSessionId: string | null;
  selectedQuestionId: string | null;
};

type Params = {
  activeSection: NavSection;
  selectedProjectId: string | null;
  inspectedTaskId: string | null;
  selectedSessionId: string | null;
  selectedQuestionId: string | null;
  setActiveSection: (section: NavSection) => void;
  setSelectedProjectId: (projectId: string | null) => void;
  setInspectedTaskId: (taskId: string | null) => void;
  setSelectedSessionId: (sessionId: string | null) => void;
  setSelectedQuestionId: (questionId: string | null) => void;
  setDrawerSelection: (selection: DetailSelection | null) => void;
};

const defaultState: ParsedState = {
  activeSection: "home",
  selectedProjectId: null,
  inspectedTaskId: null,
  selectedSessionId: null,
  selectedQuestionId: null,
};

function parseLegacyQuery(params: URLSearchParams): ParsedState {
  const section = params.get("section");
  const activeSection =
    section && validSections.has(section as NavSection)
      ? (section as NavSection)
      : "home";

  return {
    ...defaultState,
    activeSection,
    selectedProjectId: params.get("project"),
    inspectedTaskId: params.get("task"),
    selectedSessionId: params.get("session"),
    selectedQuestionId: params.get("question"),
  };
}

function safeDecode(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

function parsePath(pathname: string, search: string): ParsedState {
  const segments = pathname.split("?")[0].split("/").filter(Boolean).map(safeDecode);
  const params = new URLSearchParams(search);

  if (!segments.length) {
    if (params.toString()) {
      return parseLegacyQuery(params);
    }
    return defaultState;
  }

  const [section, projectId, nestedSection, nestedId, trailing] = segments;

  if (section === "projects") {
    if (!projectId) {
      return {
        ...defaultState,
        activeSection: "projects",
      };
    }

    if (nestedSection === "tasks" && nestedId) {
      const taskId = nestedId;
      if (trailing) {
        return {
          ...defaultState,
          activeSection: "sessions",
          selectedProjectId: projectId,
          inspectedTaskId: taskId,
          selectedSessionId: trailing,
        };
      }
      return {
        ...defaultState,
        activeSection: "projects",
        selectedProjectId: projectId,
        inspectedTaskId: taskId,
      };
    }

    if (nestedSection === "sessions") {
      return {
        ...defaultState,
        activeSection: "sessions",
        selectedProjectId: projectId,
        selectedSessionId: nestedId ?? null,
      };
    }

    if (nestedSection === "worktrees") {
      return {
        ...defaultState,
        activeSection: "worktrees",
        selectedProjectId: projectId,
      };
    }

    if (nestedSection === "activity") {
      return {
        ...defaultState,
        activeSection: "activity",
        selectedProjectId: projectId,
      };
    }

    if (nestedSection === "search") {
      return {
        ...defaultState,
        activeSection: "search",
        selectedProjectId: projectId,
      };
    }

    if (params.toString()) {
      const legacy = parseLegacyQuery(params);
      if (
        legacy.selectedProjectId !== null ||
        legacy.inspectedTaskId !== null ||
        legacy.selectedSessionId !== null ||
        legacy.selectedQuestionId !== null
      ) {
        return {
          ...legacy,
          selectedProjectId: projectId,
        };
      }
    }

    return {
      ...defaultState,
      activeSection: "projects",
      selectedProjectId: projectId,
    };
  }

  if (section === "inbox") {
    return {
      ...defaultState,
      activeSection: "waiting",
      selectedQuestionId: nestedSection ?? null,
    };
  }

  if (section === "search") {
    return {
      ...defaultState,
      activeSection: "search",
    };
  }

  if (section === "activity") {
    return {
      ...defaultState,
      activeSection: "activity",
      selectedProjectId: nestedSection ?? null,
    };
  }

  if (section === "settings") {
    return {
      ...defaultState,
      activeSection: "diagnostics",
    };
  }

  if (params.toString()) {
    return parseLegacyQuery(params);
  }

  return defaultState;
}

function buildPath(
  activeSection: NavSection,
  selectedProjectId: string | null,
  inspectedTaskId: string | null,
  selectedSessionId: string | null,
  selectedQuestionId: string | null,
): string {
  const projectSegment = selectedProjectId
    ? `/${encodeURIComponent(selectedProjectId)}`
    : "";
  const taskSegment = inspectedTaskId
    ? `/${encodeURIComponent(inspectedTaskId)}`
    : "";
  const sessionSegment = selectedSessionId
    ? `/${encodeURIComponent(selectedSessionId)}`
    : "";

  if (activeSection === "home") {
    return "/";
  }

  if (activeSection === "projects") {
    if (selectedProjectId && inspectedTaskId && selectedSessionId) {
      return `/projects${projectSegment}/tasks${taskSegment}${sessionSegment}`;
    }

    if (selectedProjectId && inspectedTaskId) {
      return `/projects${projectSegment}/tasks${taskSegment}`;
    }

    return selectedProjectId ? `/projects${projectSegment}` : "/projects";
  }

  if (activeSection === "waiting") {
    return selectedQuestionId
      ? `/inbox/${encodeURIComponent(selectedQuestionId)}`
      : "/inbox";
  }

  if (activeSection === "sessions") {
    if (!selectedProjectId) {
      return "/projects";
    }

    if (selectedSessionId && inspectedTaskId) {
      return `/projects${projectSegment}/tasks${taskSegment}${sessionSegment}`;
    }

    if (selectedSessionId) {
      return `/projects${projectSegment}/sessions${sessionSegment}`;
    }

    return `/projects${projectSegment}/sessions`;
  }

  if (activeSection === "worktrees") {
    return selectedProjectId ? `/projects${projectSegment}/worktrees` : "/projects";
  }

  if (activeSection === "search") {
    return "/search";
  }

  if (activeSection === "activity") {
    return selectedProjectId ? `/activity${projectSegment}` : "/activity";
  }

  return "/settings";
}

export function useAppUrlState({
  activeSection,
  selectedProjectId,
  inspectedTaskId,
  selectedSessionId,
  selectedQuestionId,
  setActiveSection,
  setSelectedProjectId,
  setInspectedTaskId,
  setSelectedSessionId,
  setSelectedQuestionId,
  setDrawerSelection,
}: Params) {
  useEffect(() => {
    const state = parsePath(window.location.pathname, window.location.search);

    setActiveSection(state.activeSection);
    setSelectedProjectId(state.selectedProjectId);
    setInspectedTaskId(state.inspectedTaskId);
    setSelectedSessionId(state.selectedSessionId);
    setSelectedQuestionId(state.selectedQuestionId);
    setDrawerSelection(null);
  }, [
    setActiveSection,
    setDrawerSelection,
    setInspectedTaskId,
    setSelectedProjectId,
    setSelectedQuestionId,
    setSelectedSessionId,
  ]);

  useEffect(() => {
    const href = buildPath(
      activeSection,
      selectedProjectId,
      inspectedTaskId,
      selectedSessionId,
      selectedQuestionId,
    );
    window.history.replaceState(null, "", href);
  }, [
    activeSection,
    inspectedTaskId,
    selectedProjectId,
    selectedQuestionId,
    selectedSessionId,
  ]);
}
