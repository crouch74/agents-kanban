from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from acp_core.enums import (
    AgentProfile,
    AuthorType,
    CheckStatus,
    DependencyRelationshipType,
    FollowUpType,
    Permission,
    SessionStatus,
    TaskKind,
    TaskPriority,
    Urgency,
    WaitingQuestionStatus,
    WorkflowState,
    WorktreeAction,
    WorktreeRecommendation,
    WorktreeStatus,
)
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StackPreset(StrEnum):
    NODE_LIBRARY = "node-library"
    REACT_VITE = "react-vite"
    NEXTJS = "nextjs"
    PYTHON_PACKAGE = "python-package"
    FASTAPI_SERVICE = "fastapi-service"


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None


class ProjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    description: str | None
    archived: bool
    created_at: datetime


class ProjectBootstrapCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    repo_path: str = Field(min_length=1)
    initialize_repo: bool = False
    stack_preset: StackPreset
    stack_notes: str | None = None
    initial_prompt: str = Field(min_length=3)
    use_worktree: bool = False
    confirm_existing_repo: bool = False
    agent_name: str | None = None
    agent_model: str | None = None
    agent_permissions: str | None = None
    agent_output: str | None = None


class RepositoryCreate(BaseModel):
    project_id: str
    local_path: str
    name: str | None = Field(default=None, max_length=255)


class RepositoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    name: str
    local_path: str
    default_branch: str | None
    metadata_json: dict[str, Any]
    created_at: datetime


class RuntimeLaunchSpecCreate(BaseModel):
    argv: list[str]
    env: dict[str, str] = Field(default_factory=dict)
    display_command: str
    working_directory: str = Field(min_length=1)
    legacy_shell_command: str | None = None


class SessionLaunchInputCreate(BaseModel):
    task_kind: TaskKind = TaskKind.EXECUTE
    agent_name: str | None = None
    prompt: str | None = None
    working_directory: str | None = None
    model: str | None = None
    permission_mode: Permission | None = None
    output_mode: str | None = None
    max_turns: int | None = Field(default=None, ge=1)
    resume_token: str | None = None
    allowed_tools: list[str] = Field(default_factory=list)
    disallowed_tools: list[str] = Field(default_factory=list)
    extra_env: dict[str, str] = Field(default_factory=dict)
    repository_id: str | None = None
    worktree_id: str | None = None
    session_family_id: str | None = None
    follow_up_of_session_id: str | None = None


class AgentSessionCreate(BaseModel):
    task_id: str
    profile: AgentProfile = AgentProfile.EXECUTOR
    agent_name: str | None = None
    repository_id: str | None = None
    worktree_id: str | None = None
    launch_input: SessionLaunchInputCreate | None = None
    launch_spec: RuntimeLaunchSpecCreate | None = None
    # Deprecated compatibility bridge.
    command: str | None = None


class AgentSessionFollowUpCreate(BaseModel):
    profile: AgentProfile = AgentProfile.VERIFIER
    follow_up_type: FollowUpType | None = None
    agent_name: str | None = None
    reuse_worktree: bool = True
    reuse_repository: bool = True
    launch_input: SessionLaunchInputCreate | None = None
    launch_spec: RuntimeLaunchSpecCreate | None = None
    # Deprecated compatibility bridge.
    command: str | None = None


class AgentSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    task_id: str
    repository_id: str | None
    worktree_id: str | None
    profile: AgentProfile
    status: SessionStatus
    session_name: str
    runtime_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class WaitingQuestionCreate(BaseModel):
    task_id: str
    session_id: str | None = None
    prompt: str = Field(min_length=3)
    blocked_reason: str | None = None
    urgency: Urgency | None = None
    options_json: list[dict[str, Any]] = Field(default_factory=list)


class HumanReplyCreate(BaseModel):
    responder_name: str = Field(min_length=2, max_length=255)
    body: str = Field(min_length=1)
    payload_json: dict[str, Any] = Field(default_factory=dict)


class HumanReplyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_id: str
    responder_name: str
    body: str
    payload_json: dict[str, Any]
    created_at: datetime


class WaitingQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    task_id: str
    session_id: str | None
    status: WaitingQuestionStatus
    prompt: str
    blocked_reason: str | None
    urgency: Urgency | None
    options_json: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class WaitingQuestionDetail(WaitingQuestionRead):
    replies: list[HumanReplyRead]


class AgentRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    attempt_number: int
    status: str
    summary: str | None
    runtime_metadata: dict[str, Any]
    created_at: datetime


class SessionMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    message_type: str
    source: str
    body: str
    payload_json: dict[str, Any]
    created_at: datetime


class SessionTailRead(BaseModel):
    session: AgentSessionRead
    lines: list[str]
    recent_messages: list[SessionMessageRead]


class SessionTimelineRead(BaseModel):
    session: AgentSessionRead
    runs: list[AgentRunRead]
    messages: list[SessionMessageRead]
    waiting_questions: list[WaitingQuestionRead]
    events: list["EventRecord"]
    related_sessions: list[AgentSessionRead]


class BoardColumnRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    key: WorkflowState
    name: str
    position: int
    wip_limit: int | None
    entry_policy: str | None
    exit_policy: str | None
    done_policy: str | None


class TaskCreate(BaseModel):
    project_id: str
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    parent_task_id: str | None = None
    board_column_key: WorkflowState = WorkflowState.BACKLOG
    tags: list[str] = Field(default_factory=list)


class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    workflow_state: WorkflowState | None = None
    board_column_id: str | None = None
    blocked_reason: str | None = None
    waiting_for_human: bool | None = None


class TaskCommentCreate(BaseModel):
    author_type: AuthorType = AuthorType.HUMAN
    author_name: str = Field(min_length=2, max_length=255)
    body: str = Field(min_length=1)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class TaskCommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    author_type: AuthorType
    author_name: str
    body: str
    metadata_json: dict[str, Any]
    created_at: datetime


class TaskCheckCreate(BaseModel):
    check_type: str = Field(min_length=2, max_length=64)
    status: CheckStatus = CheckStatus.PENDING
    summary: str = Field(min_length=1)
    payload_json: dict[str, Any] = Field(default_factory=dict)


class TaskCheckRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    check_type: str
    status: CheckStatus
    summary: str
    payload_json: dict[str, Any]
    created_at: datetime


class TaskArtifactCreate(BaseModel):
    artifact_type: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=255)
    uri: str = Field(min_length=1)
    payload_json: dict[str, Any] = Field(default_factory=dict)


class TaskArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    artifact_type: str
    name: str
    uri: str
    payload_json: dict[str, Any]
    created_at: datetime


class TaskDependencyCreate(BaseModel):
    depends_on_task_id: str
    relationship_type: DependencyRelationshipType = DependencyRelationshipType.BLOCKS


class TaskDependencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    depends_on_task_id: str
    relationship_type: DependencyRelationshipType
    created_at: datetime


class TaskCompletionReadinessRead(BaseModel):
    task_id: str
    can_mark_done: bool
    passing_check_count: int
    artifact_count: int
    blocking_dependency_count: int
    open_waiting_question_count: int
    missing_requirements: list[str]


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    board_column_id: str
    parent_task_id: str | None
    title: str
    description: str | None
    workflow_state: WorkflowState
    priority: TaskPriority
    tags: list[str]
    blocked_reason: str | None
    waiting_for_human: bool
    created_at: datetime
    updated_at: datetime


class TaskDetail(TaskRead):
    dependencies: list[TaskDependencyRead]
    comments: list[TaskCommentRead]
    checks: list[TaskCheckRead]
    artifacts: list[TaskArtifactRead]
    waiting_questions: list[WaitingQuestionRead]


class WorktreeCreate(BaseModel):
    repository_id: str
    task_id: str | None = None
    label: str | None = Field(default=None, max_length=255)


class WorktreePatch(BaseModel):
    status: WorktreeStatus | None = None
    lock_reason: str | None = None


class WorktreeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    repository_id: str
    task_id: str | None
    session_id: str | None
    branch_name: str
    path: str
    status: WorktreeStatus
    lock_reason: str | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class WorktreeHygieneIssueRead(BaseModel):
    worktree_id: str
    project_id: str | None
    task_id: str | None
    session_id: str | None
    branch_name: str
    path: str
    status: WorktreeStatus
    recommendation: WorktreeRecommendation
    reasons: list[str]


class BoardView(BaseModel):
    id: str
    project_id: str
    name: str
    columns: list[BoardColumnRead]
    tasks: list[TaskRead]


class ProjectOverview(BaseModel):
    project: ProjectSummary
    board: BoardView
    repositories: list[RepositoryRead]
    worktrees: list[WorktreeRead]
    sessions: list[AgentSessionRead]
    waiting_questions: list[WaitingQuestionRead]


class ProjectBootstrapPlannedChange(BaseModel):
    path: str
    action: WorktreeAction
    description: str


class ProjectBootstrapPreviewRead(BaseModel):
    repo_path: str
    stack_preset: StackPreset
    stack_notes: str | None
    use_worktree: bool
    repo_initialized_on_confirm: bool
    scaffold_applied_on_confirm: bool
    has_existing_commits: bool
    confirmation_required: bool
    execution_path: str
    execution_branch: str
    planned_changes: list[ProjectBootstrapPlannedChange]


class ProjectBootstrapRead(BaseModel):
    project: ProjectSummary
    repository: RepositoryRead
    kickoff_task: TaskRead
    kickoff_session: AgentSessionRead
    kickoff_worktree: WorktreeRead | None
    execution_path: str
    execution_branch: str
    stack_preset: StackPreset
    stack_notes: str | None
    use_worktree: bool
    repo_initialized: bool
    scaffold_applied: bool


class EventRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_type: str
    actor_name: str
    entity_type: str
    entity_id: str
    event_type: str
    payload_json: dict[str, Any]
    created_at: datetime


class SearchHit(BaseModel):
    entity_type: str
    entity_id: str
    project_id: str | None
    title: str
    snippet: str
    secondary: str | None
    created_at: datetime


class SearchResults(BaseModel):
    query: str
    hits: list[SearchHit]


class DiagnosticsRead(BaseModel):
    app_name: str
    environment: str
    database_path: str
    runtime_home: str
    tmux_available: bool
    tmux_server_running: bool
    runtime_managed_session_count: int
    orphan_runtime_session_count: int
    orphan_runtime_sessions: list[str]
    reconciled_session_count: int
    stale_worktree_count: int
    stale_worktrees: list[WorktreeHygieneIssueRead]
    git_available: bool
    current_project_count: int
    current_repository_count: int
    current_task_count: int
    current_worktree_count: int
    current_session_count: int
    current_open_question_count: int
    current_event_count: int


class RuntimeOrphanCleanupRead(BaseModel):
    removed_runtime_session_count: int
    removed_runtime_sessions: list[str]


class DashboardRead(BaseModel):
    projects: list[ProjectSummary]
    recent_events: list[EventRecord]
    waiting_questions: list[WaitingQuestionRead]
    blocked_tasks: list[TaskRead]
    active_sessions: list[AgentSessionRead]
    waiting_count: int
    blocked_count: int
    running_sessions: int


class ApiErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
    retryable: bool | None = None


class ApiErrorEnvelope(BaseModel):
    error: ApiErrorDetail
