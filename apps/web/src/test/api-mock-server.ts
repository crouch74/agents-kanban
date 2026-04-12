import { beforeAll, afterAll, afterEach, vi } from 'vitest';

type MockResolver = (request: Request) => Promise<Response> | Response;

type RouteHandler = {
  method: string;
  matcher: (url: URL) => boolean;
  resolver: MockResolver;
};

const routes: RouteHandler[] = [];

function addRoute(method: string, path: string, resolver: MockResolver) {
  routes.push({
    method,
    matcher: (url) => url.pathname === path,
    resolver,
  });
}

addRoute('GET', '/api/v1/dashboard', () =>
  Response.json({
    projects: [],
    recent_events: [],
    waiting_questions: [],
    blocked_tasks: [],
    active_sessions: [],
    waiting_count: 0,
    blocked_count: 0,
    running_sessions: 0,
  }),
);

addRoute('GET', '/api/v1/diagnostics', () =>
  Response.json({
    app_name: 'Agent Control Plane',
    environment: 'test',
    database_path: '.acp/acp.sqlite3',
    runtime_home: '.acp',
    tmux_available: true,
    tmux_server_running: false,
    runtime_managed_session_count: 0,
    orphan_runtime_session_count: 0,
    orphan_runtime_sessions: [],
    reconciled_session_count: 0,
    stale_worktree_count: 0,
    stale_worktrees: [],
    git_available: true,
    current_project_count: 0,
    current_repository_count: 0,
    current_task_count: 0,
    current_worktree_count: 0,
    current_session_count: 0,
    current_open_question_count: 0,
    current_event_count: 0,
  }),
);

addRoute('GET', '/api/v1/projects', () => Response.json([]));
addRoute('GET', '/api/v1/questions', () => Response.json([]));

addRoute('GET', '/api/v1/search', (request) => {
  const url = new URL(request.url);
  const q = url.searchParams.get('q');

  if (q !== 'calc') {
    return Response.json({ query: q ?? '', hits: [] });
  }

  return Response.json({
    query: 'calc',
    hits: [
      {
        entity_type: 'event',
        entity_id: 'event-1',
        project_id: 'project-1',
        title: 'task.created',
        snippet: '{"title":"calc task"}',
        secondary: 'operator',
        created_at: '2026-04-11T10:00:00Z',
      },
    ],
  });
});

addRoute('POST', '/api/v1/projects/bootstrap/preview', () =>
  Response.json({
    repo_path: '/tmp/demo-repo',
    stack_preset: 'nextjs',
    stack_notes: 'demo notes',
    use_worktree: false,
    repo_initialized_on_confirm: true,
    scaffold_applied_on_confirm: true,
    has_existing_commits: false,
    confirmation_required: false,
    execution_path: '/tmp/demo-repo',
    execution_branch: 'main',
    planned_changes: [],
  }),
);

addRoute('POST', '/api/v1/projects/bootstrap', () =>
  Response.json({
    project: {
      id: 'project-1',
      name: 'Bootstrap Demo',
      slug: 'bootstrap-demo',
      description: 'demo',
    },
    repository: {
      id: 'repo-1',
      project_id: 'project-1',
      name: 'demo-repo',
      local_path: '/tmp/demo-repo',
      default_branch: 'main',
      metadata_json: {},
    },
    kickoff_task: {
      id: 'task-1',
      project_id: 'project-1',
      title: 'Kick off planning and board setup',
      workflow_state: 'in_progress',
      board_column_id: 'column-1',
      parent_task_id: null,
      blocked_reason: null,
      waiting_for_human: false,
      priority: 'medium',
      tags: [],
    },
    kickoff_session: {
      id: 'session-1',
      project_id: 'project-1',
      task_id: 'task-1',
      repository_id: 'repo-1',
      worktree_id: null,
      profile: 'executor',
      status: 'running',
      session_name: 'acp-project-1',
      runtime_metadata: {},
    },
    kickoff_worktree: null,
    execution_path: '/tmp/demo-repo',
    execution_branch: 'main',
    stack_preset: 'nextjs',
    stack_notes: 'demo notes',
    use_worktree: false,
    repo_initialized: true,
    scaffold_applied: true,
  }),
);

addRoute('GET', '/api/v1/projects/project-1', () =>
  Response.json({
    project: {
      id: 'project-1',
      name: 'Bootstrap Demo',
      slug: 'bootstrap-demo',
      description: 'demo',
    },
    board: { id: 'board-1', project_id: 'project-1', name: 'Main Board', columns: [], tasks: [] },
    repositories: [],
    worktrees: [],
    sessions: [],
    waiting_questions: [],
  }),
);

addRoute('GET', '/api/v1/projects/project-1/events', () =>
  Response.json([
    {
      id: 'event-1',
      actor_type: 'human',
      actor_name: 'operator',
      entity_type: 'task',
      entity_id: 'task-1',
      event_type: 'task.created',
      created_at: '2026-04-11T10:00:00Z',
      payload_json: { title: 'Task created from bootstrap', project_id: 'project-1' },
    },
  ]),
);

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
