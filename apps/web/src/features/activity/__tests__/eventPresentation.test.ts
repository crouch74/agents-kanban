import { expect, test } from "vitest";
import type { EventRecord, SearchHit } from "@/lib/api";
import {
  formatEvent,
  formatSearchSnippet,
  summarizeEvent,
} from "@/features/activity/eventPresentation";

test("formats event types for display", () => {
  expect(formatEvent("task.created")).toBe("Task Created");
});

test("summarizes from first non-empty payload field", () => {
  const event: EventRecord = {
    id: "event-1",
    actor_type: "human",
    actor_name: "operator",
    entity_type: "task",
    entity_id: "task-1",
    event_type: "task.created",
    created_at: "2026-04-11T10:00:00Z",
    payload_json: {
      title: "",
      summary: "Provisioned worktree",
    },
  };

  expect(summarizeEvent(event)).toBe("Provisioned worktree");
});

test("summarizes added board columns when present", () => {
  const event: EventRecord = {
    id: "event-2",
    actor_type: "system",
    actor_name: "",
    entity_type: "board",
    entity_id: "board-1",
    event_type: "board.updated",
    created_at: "2026-04-11T10:00:00Z",
    payload_json: {
      added_column_keys: ["backlog", "review"],
    },
  };

  expect(summarizeEvent(event)).toBe("Added columns: backlog, review");
});

test("formats search snippets for events", () => {
  const hit: SearchHit = {
    entity_type: "event",
    entity_id: "event-1",
    title: "task.created",
    snippet: "ignored",
    created_at: "2026-04-11T10:00:00Z",
    secondary: "operator",
    project_id: "project-1",
  };

  expect(formatSearchSnippet(hit)).toBe(
    "Audit event matched the query. Task Created · operator",
  );
});
