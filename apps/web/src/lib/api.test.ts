import { beforeEach, describe, expect, test, vi } from "vitest";
import {
  fetchJson,
  getEvents,
  patchJson,
  postJson,
  searchContext,
} from "./api";

describe("api helpers", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });

  test("fetchJson parses successful responses", async () => {
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ ok: true }), { status: 200 }));

    await expect(fetchJson<{ ok: boolean }>("/dashboard")).resolves.toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledWith("http://127.0.0.1:8000/api/v1/dashboard");
  });

  test("fetchJson surfaces API detail errors", async () => {
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ detail: "boom" }), { status: 400 }));

    await expect(fetchJson("/projects")).rejects.toThrow("boom");
  });

  test("postJson and patchJson send JSON payloads", async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "p1" }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: "p2" }), { status: 200 }));

    await postJson("/projects", { name: "Demo" });
    await patchJson("/tasks/t1", { workflow_state: "ready" });

    expect(fetchMock.mock.calls[0][1]).toMatchObject({
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "Demo" }),
    });
    expect(fetchMock.mock.calls[1][1]).toMatchObject({
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ workflow_state: "ready" }),
    });
  });

  test("getEvents builds query parameters from optional filters", async () => {
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 200 }));

    await getEvents({ projectId: "proj-1", taskId: "task-1", sessionId: "session-1", limit: 5 });

    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl).toContain("/events?");
    expect(calledUrl).toContain("project_id=proj-1");
    expect(calledUrl).toContain("task_id=task-1");
    expect(calledUrl).toContain("session_id=session-1");
    expect(calledUrl).toContain("limit=5");
  });

  test("searchContext includes query and optional project", async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify({ query: "test", hits: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ query: "test", hits: [] }), { status: 200 }));

    await searchContext("test");
    await searchContext("test", "proj-1");

    expect(fetchMock.mock.calls[0][0]).toBe("http://127.0.0.1:8000/api/v1/search?q=test");
    expect(fetchMock.mock.calls[1][0]).toBe("http://127.0.0.1:8000/api/v1/search?q=test&project_id=proj-1");
  });
});
