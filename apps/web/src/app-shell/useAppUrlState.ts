import { useEffect, useRef } from "react";
import { type DetailSelection, type NavSection, validSections } from "@/app-shell/types";

type ParsedState = {
  activeSection: NavSection;
  selectedProjectId: string | null;
  inspectedTaskId: string | null;
  selectedSessionId: string | null;
  selectedQuestionId: string | null;
};

type PersistedState = ParsedState & {
  schema_version: number;
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

const APP_URL_STATE_STORAGE_KEY = "acp.app-url-state";
const APP_URL_STATE_SCHEMA_VERSION = 1;

const defaultState: ParsedState = {
  activeSection: "home",
  selectedProjectId: null,
  inspectedTaskId: null,
  selectedSessionId: null,
  selectedQuestionId: null,
};

function isPersistedState(value: unknown): value is PersistedState {
  if (value === null || typeof value !== "object") {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.schema_version === "number" &&
    typeof candidate.activeSection === "string" &&
    validSections.has(candidate.activeSection as NavSection) &&
    (candidate.selectedProjectId === null ||
      typeof candidate.selectedProjectId === "string") &&
    (candidate.inspectedTaskId === null || typeof candidate.inspectedTaskId === "string") &&
    (candidate.selectedSessionId === null || typeof candidate.selectedSessionId === "string") &&
    (candidate.selectedQuestionId === null || typeof candidate.selectedQuestionId === "string")
  );
}

function readPersistedState(): ParsedState | null {
  try {
    const raw = window.localStorage.getItem(APP_URL_STATE_STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed: unknown = JSON.parse(raw);
    if (!isPersistedState(parsed)) {
      return null;
    }
    return {
      activeSection: parsed.activeSection as NavSection,
      selectedProjectId: parsed.selectedProjectId,
      inspectedTaskId: parsed.inspectedTaskId,
      selectedSessionId: parsed.selectedSessionId,
      selectedQuestionId: parsed.selectedQuestionId,
    };
  } catch {
    return null;
  }
}

function writePersistedState(state: ParsedState) {
  try {
    const payload: PersistedState = {
      ...state,
      schema_version: APP_URL_STATE_SCHEMA_VERSION,
    };
    window.localStorage.setItem(APP_URL_STATE_STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // Ignore quota or storage restrictions in environments that do not allow persistence.
  }
}

function shouldUsePersistedFallback(pathname: string, state: ParsedState): boolean {
  const normalizedPath = pathname.split("?")[0].replace(/\/+$/, "");
  const isRoot = normalizedPath === "";
  const isHomeEquivalent =
    state.activeSection === "home" &&
    state.selectedProjectId === null &&
    state.inspectedTaskId === null &&
    state.selectedSessionId === null &&
    state.selectedQuestionId === null;
  return isRoot && isHomeEquivalent;
}

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
  const hasHydratedFromUrl = useRef(false);

  useEffect(() => {
    const state = parsePath(window.location.pathname, window.location.search);
    const resolvedState = shouldUsePersistedFallback(window.location.pathname, state)
      ? readPersistedState() ?? state
      : state;

    setActiveSection(resolvedState.activeSection);
    setSelectedProjectId(resolvedState.selectedProjectId);
    setInspectedTaskId(resolvedState.inspectedTaskId);
    setSelectedSessionId(resolvedState.selectedSessionId);
    setSelectedQuestionId(resolvedState.selectedQuestionId);
    setDrawerSelection(null);
    hasHydratedFromUrl.current = true;
  }, [
    setActiveSection,
    setDrawerSelection,
    setInspectedTaskId,
    setSelectedProjectId,
    setSelectedQuestionId,
    setSelectedSessionId,
  ]);

  useEffect(() => {
    if (!hasHydratedFromUrl.current) {
      return;
    }

    const href = buildPath(
      activeSection,
      selectedProjectId,
      inspectedTaskId,
      selectedSessionId,
      selectedQuestionId,
    );

    const current = `${window.location.pathname}${window.location.search}`;
    if (current !== href) {
      window.history.replaceState(null, "", href);
    }
    writePersistedState({
      activeSection,
      selectedProjectId,
      inspectedTaskId,
      selectedSessionId,
      selectedQuestionId,
    });
  }, [
    activeSection,
    inspectedTaskId,
    selectedProjectId,
    selectedQuestionId,
    selectedSessionId,
  ]);
}
