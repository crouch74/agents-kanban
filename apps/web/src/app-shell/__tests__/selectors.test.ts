import { expect, test } from "vitest";
import type { TaskSummary } from "@acp/sdk";
import type { EventRecord } from "@/lib/api";
import {
  buildActivitySessionOptions,
  buildActivityTaskOptions,
  buildGroupedTasks,
  buildSubtasksByParent,
  filterProjects,
} from "@/app-shell/selectors";
import { formatEvent, formatSearchSnippet, summarizeEvent } from "@/app-shell/eventFormatting";

function makeTask(overrides: Partial<TaskSummary> = {}): TaskSummary {
  return {
    id: "task-1",
    project_id: "project-1",
    title: "Task",
    workflow_state: "backlog",
    board_column_id: "col-backlog",
    parent_task_id: null,
    blocked_reason: null,
    waiting_for_human: false,
    priority: "medium",
    tags: [],
    ...overrides,
  };
}

function makeEvent(overrides: Partial<EventRecord> = {}): EventRecord {
  return {
    id: "event-1",
    actor_type: "system",
    actor_name: "agent",
    entity_type: "task",
    entity_id: "task-1",
    event_type: "task.updated",
    created_at: "2026-01-01T00:00:00Z",
    payload_json: {},
    ...overrides,
  };
}

test("filterProjects matches name, slug, and description", () => {
  const projects = [
    { id: "p1", name: "Agent Control Plane", slug: "acp", description: "Monorepo" },
    { id: "p2", name: "CLI", slug: "terminal-tools", description: "shell" },
  ];

  expect(filterProjects(projects, "acp")).toHaveLength(1);
  expect(filterProjects(projects, "terminal")).toHaveLength(1);
  expect(filterProjects(projects, "shell")).toHaveLength(1);
});

test("buildGroupedTasks excludes subtasks", () => {
  const grouped = buildGroupedTasks(
    [{ id: "col-backlog" }, { id: "col-ready" }],
    [
      makeTask({ id: "top", parent_task_id: null }),
      makeTask({ id: "sub", parent_task_id: "top" }),
    ],
  );

  expect(grouped.get("col-backlog")?.map((task) => task.id)).toEqual(["top"]);
});

test("buildSubtasksByParent indexes subtasks by parent id", () => {
  const map = buildSubtasksByParent([
    makeTask({ id: "parent", parent_task_id: null }),
    makeTask({ id: "child-a", parent_task_id: "parent" }),
    makeTask({ id: "child-b", parent_task_id: "parent" }),
  ]);

  expect(map.get("parent")?.map((task) => task.id)).toEqual(["child-a", "child-b"]);
});

test("activity options include fallbacks from events", () => {
  const events = [
    makeEvent({ entity_id: "task-9", payload_json: { task_id: "task-9" } }),
    makeEvent({ entity_type: "session", entity_id: "session-9", payload_json: { session_id: "session-9" } }),
  ];

  const taskOptions = buildActivityTaskOptions([], events);
  const sessionOptions = buildActivitySessionOptions([], events);

  expect(taskOptions[0]?.label).toBe("Task task-9");
  expect(sessionOptions[0]?.label).toBe("Session session-");
});

test("event formatting and summaries handle payload data", () => {
  expect(formatEvent("task.updated")).toBe("Task Updated");

  const summary = summarizeEvent(
    makeEvent({ payload_json: { summary: "patched workflow" } }),
  );
  expect(summary).toBe("patched workflow");

  const snippet = formatSearchSnippet({
    entity_type: "event",
    entity_id: "event-1",
    project_id: null,
    title: "task.updated",
    snippet: "ignored",
    secondary: "executor",
    created_at: "2026-01-01T00:00:00Z",
  });
  expect(snippet).toContain("Audit event matched the query");
});
