import { describe, expect, test } from "vitest";
import { useUIStore } from "./ui";

describe("ui store", () => {
  test("updates selected project and inspector state", () => {
    useUIStore.setState({ selectedProjectId: null, inspectorOpen: true });

    useUIStore.getState().setSelectedProjectId("project-42");
    expect(useUIStore.getState().selectedProjectId).toBe("project-42");

    useUIStore.getState().setInspectorOpen(false);
    expect(useUIStore.getState().inspectorOpen).toBe(false);
  });
});
