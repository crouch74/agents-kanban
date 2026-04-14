import { afterAll, afterEach, beforeAll, vi } from 'vitest';

type MockResolver = (request: Request) => Promise<Response> | Response;

type RouteHandler = {
  method: string;
  matcher: (url: URL) => boolean;
  resolver: MockResolver;
};

const routes: RouteHandler[] = [];

function addRoute(method: string, matcher: (url: URL) => boolean, resolver: MockResolver) {
  routes.push({ method, matcher, resolver });
}

const project = {
  id: 'project-1',
  name: 'Test Project',
  slug: 'test-project',
  description: 'Mock project',
  archived: false,
  created_at: '2026-04-11T10:00:00Z',
};

const board = {
  id: 'board-1',
  project_id: 'project-1',
  name: 'Main Board',
  columns: [
    { id: 'col-backlog', key: 'backlog', name: 'Backlog', position: 0, wip_limit: null },
    { id: 'col-in-progress', key: 'in_progress', name: 'In Progress', position: 1, wip_limit: null },
    { id: 'col-done', key: 'done', name: 'Done', position: 2, wip_limit: null },
  ],
  tasks: [
    {
      id: 'task-1',
      project_id: 'project-1',
      board_column_id: 'col-backlog',
      title: 'Mock task',
      description: 'Task for UI tests',
      workflow_state: 'backlog',
      priority: 'medium',
      tags: [],
      assignee: null,
      source: 'test',
      created_at: '2026-04-11T10:00:00Z',
      updated_at: '2026-04-11T10:00:00Z',
    },
  ],
};

addRoute('GET', (url) => url.pathname === '/api/v1/dashboard', () =>
  Response.json({
    projects: [project],
    recent_events: [],
    task_counts: { backlog: 1, in_progress: 0, done: 0 },
  }),
);

addRoute('GET', (url) => url.pathname === '/api/v1/settings/diagnostics', () =>
  Response.json({
    app_name: 'Shared Task Board',
    environment: 'test',
    services: {
      api: { status: 'ok', detail: 'FastAPI service online' },
      database: { status: 'ok', detail: 'SQLite connection healthy' },
      mcp: { status: 'external', detail: 'Served as an external task-board endpoint' },
    },
    paths: {
      runtime_home: '/tmp/.acp',
      database_path: '/tmp/.acp/acp.sqlite3',
      artifacts_path: '/tmp/.acp/artifacts',
      logs_path: '/tmp/.acp/logs',
    },
    row_counts: { projects: 1, tasks: 1, task_comments: 1, events: 1 },
  }),
);

addRoute('POST', (url) => url.pathname === '/api/v1/settings/purge-db', () =>
  Response.json({
    status: 'ok',
    purged_tables: 5,
    rows_deleted: 12,
    database_path: '/tmp/.acp/acp.sqlite3',
  }),
);

addRoute('GET', (url) => url.pathname === '/api/v1/projects', () => Response.json([project]));
addRoute('POST', (url) => url.pathname === '/api/v1/projects', async (request) => {
  const payload = (await request.json()) as { name: string; description?: string };
  return Response.json({
    ...project,
    id: 'project-created',
    name: payload.name,
    slug: payload.name.toLowerCase().replace(/\s+/g, '-'),
    description: payload.description ?? null,
  }, { status: 201 });
});

addRoute('GET', (url) => url.pathname === '/api/v1/projects/project-1', () =>
  Response.json({ project, board }),
);

addRoute('GET', (url) => url.pathname === '/api/v1/events', () =>
  Response.json([
    {
      id: 'event-1',
      actor_type: 'human',
      actor_name: 'operator',
      entity_type: 'task',
      entity_id: 'task-1',
      event_type: 'task.created',
      created_at: '2026-04-11T10:00:00Z',
      payload_json: { title: 'Mock task', project_id: 'project-1' },
    },
  ]),
);

addRoute('GET', (url) => url.pathname === '/api/v1/search', (request) => {
  const url = new URL(request.url);
  const q = url.searchParams.get('q') ?? '';
  if (!q) {
    return Response.json({ query: q, hits: [] });
  }
  return Response.json({
    query: q,
    hits: [
      {
        entity_type: 'task',
        entity_id: 'task-1',
        project_id: 'project-1',
        title: 'Mock task',
        snippet: 'Task for UI tests',
        secondary: 'backlog',
        created_at: '2026-04-11T10:00:00Z',
      },
    ],
  });
});

addRoute('GET', (url) => url.pathname === '/api/v1/tasks/task-1/detail', () =>
  Response.json({
    ...board.tasks[0],
    comments: [
      {
        id: 'comment-1',
        task_id: 'task-1',
        author_type: 'agent',
        author_name: 'codex',
        source: 'mcp',
        body: 'Initial progress note',
        metadata_json: {},
        created_at: '2026-04-11T10:01:00Z',
      },
    ],
  }),
);

addRoute('POST', (url) => url.pathname === '/api/v1/tasks', () =>
  Response.json(
    {
      ...board.tasks[0],
      id: 'task-created',
      title: 'New task',
    },
    { status: 201 },
  ),
);

addRoute('PATCH', (url) => url.pathname.startsWith('/api/v1/tasks/'), () =>
  Response.json({ ...board.tasks[0], workflow_state: 'in_progress' }),
);

addRoute('POST', (url) => url.pathname.endsWith('/comments'), async (request) => {
  const payload = (await request.json()) as { body: string; author_name: string; source?: string };
  return Response.json(
    {
      id: 'comment-created',
      task_id: 'task-1',
      author_type: 'human',
      author_name: payload.author_name,
      source: payload.source ?? 'web',
      body: payload.body,
      metadata_json: {},
      created_at: '2026-04-11T10:03:00Z',
    },
    { status: 201 },
  );
});

const mockFetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
  const request = new Request(input, init);
  const url = new URL(request.url);
  const method = request.method.toUpperCase();

  const route = routes.find((candidate) => candidate.method === method && candidate.matcher(url));
  if (route) {
    return route.resolver(request);
  }

  throw new Error(`Unhandled API request in tests: ${method} ${url.pathname}${url.search}`);
});

export function installApiMockServer() {
  beforeAll(() => {
    vi.stubGlobal('fetch', mockFetch);
  });

  afterEach(() => {
    mockFetch.mockClear();
  });

  afterAll(() => {
    vi.unstubAllGlobals();
  });
}
