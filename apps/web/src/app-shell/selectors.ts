import type { TaskSummary } from "@acp/sdk";
import type { EventRecord } from "@/lib/api";

export type ProjectSearchRecord = {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
};

export function filterProjects(
  projects: ProjectSearchRecord[],
  searchTerm: string,
): ProjectSearchRecord[] {
  const needle = searchTerm.trim().toLowerCase();
  if (!needle) {
    return projects;
  }

  return projects.filter((project) => {
    return (
      project.name.toLowerCase().includes(needle) ||
      project.slug.toLowerCase().includes(needle) ||
      (project.description ?? "").toLowerCase().includes(needle)
    );
  });
}

export function buildGroupedTasks(
  columns: Array<{ id: string }>,
  tasks: TaskSummary[],
): Map<string, TaskSummary[]> {
  const map = new Map<string, TaskSummary[]>();
  columns.forEach((column) => map.set(column.id, []));

  tasks.forEach((task) => {
    if (task.parent_task_id) {
      return;
    }
    const entry = map.get(task.board_column_id);
    if (entry) {
      entry.push(task);
    }
  });

  return map;
}

export function buildSubtasksByParent(tasks: TaskSummary[]): Map<string, TaskSummary[]> {
  const map = new Map<string, TaskSummary[]>();
  for (const task of tasks) {
    if (!task.parent_task_id) {
      continue;
    }
    const entry = map.get(task.parent_task_id) ?? [];
    entry.push(task);
    map.set(task.parent_task_id, entry);
  }
  return map;
}

export function buildActivityTaskOptions(tasks: TaskSummary[], events: EventRecord[]) {
  const options = new Map<string, string>();
  for (const task of tasks) {
    options.set(task.id, task.title);
  }
  for (const event of events) {
    const taskId =
      typeof event.payload_json.task_id === "string"
        ? event.payload_json.task_id
        : event.entity_type === "task"
          ? event.entity_id
          : null;

    if (taskId && !options.has(taskId)) {
      const payloadTitle = event.payload_json.title;
      options.set(
        taskId,
        typeof payloadTitle === "string" && payloadTitle.trim().length > 0
          ? payloadTitle
          : `Task ${taskId.slice(0, 8)}`,
      );
    }
  }

  return Array.from(options.entries()).map(([value, label]) => ({ value, label }));
}

export function buildActivitySessionOptions(
  sessions: Array<{ id: string; session_name: string }>,
  events: EventRecord[],
) {
  const options = new Map<string, string>();
  for (const session of sessions) {
    options.set(session.id, session.session_name);
  }

  for (const event of events) {
    const sessionId =
      typeof event.payload_json.session_id === "string"
        ? event.payload_json.session_id
        : event.entity_type === "session"
          ? event.entity_id
          : null;
    if (sessionId && !options.has(sessionId)) {
      const payloadSessionName = event.payload_json.session_name;
      options.set(
        sessionId,
        typeof payloadSessionName === "string" && payloadSessionName.trim().length > 0
          ? payloadSessionName
          : `Session ${sessionId.slice(0, 8)}`,
      );
    }
  }

  return Array.from(options.entries()).map(([value, label]) => ({ value, label }));
}
