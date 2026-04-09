import { create } from "zustand";

type UIState = {
  selectedProjectId: string | null;
  inspectorOpen: boolean;
  setSelectedProjectId: (projectId: string | null) => void;
  setInspectorOpen: (open: boolean) => void;
};

export const useUIStore = create<UIState>((set) => ({
  selectedProjectId: null,
  inspectorOpen: true,
  setSelectedProjectId: (selectedProjectId) => set({ selectedProjectId }),
  setInspectorOpen: (inspectorOpen) => set({ inspectorOpen }),
}));

