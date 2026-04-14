from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from acp_core.enums import AuthorType, TaskPriority, WorkflowState


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


class BoardColumnRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    key: WorkflowState
    name: str
    position: int
    wip_limit: int | None


class TaskCreate(BaseModel):
    project_id: str
    title: str = Field(min_length=2, max_length=255)
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    board_column_key: WorkflowState = WorkflowState.BACKLOG
    tags: list[str] = Field(default_factory=list)
    assignee: str | None = None
    source: str | None = None


class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    workflow_state: WorkflowState | None = None
    board_column_id: str | None = None
    priority: TaskPriority | None = None
    tags: list[str] | None = None
    assignee: str | None = None


class TaskCommentCreate(BaseModel):
    author_type: AuthorType = AuthorType.HUMAN
    author_name: str = Field(min_length=2, max_length=255)
    source: str | None = None
    body: str = Field(min_length=1)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class TaskCommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    author_type: AuthorType
    author_name: str
    source: str | None = None
    body: str
    metadata_json: dict[str, Any]
    created_at: datetime


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    board_column_id: str
    title: str
    description: str | None
    workflow_state: WorkflowState
    priority: TaskPriority
    tags: list[str]
    assignee: str | None = None
    source: str | None = None
    created_at: datetime
    updated_at: datetime


class TaskDetail(TaskRead):
    comments: list[TaskCommentRead]


class BoardView(BaseModel):
    id: str
    project_id: str
    name: str
    columns: list[BoardColumnRead]
    tasks: list[TaskRead]


class ProjectOverview(BaseModel):
    project: ProjectSummary
    board: BoardView


class EventRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_type: str
    actor_name: str
    entity_type: str
    entity_id: str
    event_type: str
    correlation_id: str | None
    payload_json: dict[str, Any]
    created_at: datetime


class DashboardRead(BaseModel):
    projects: list[ProjectSummary]
    recent_events: list[EventRecord]
    task_counts: dict[str, int]


class SearchHit(BaseModel):
    entity_type: str
    entity_id: str
    project_id: str | None = None
    title: str
    snippet: str
    secondary: str | None = None
    created_at: datetime


class SearchResults(BaseModel):
    query: str
    hits: list[SearchHit]


class ServiceStatusRead(BaseModel):
    status: str
    detail: str | None = None


class SystemDiagnosticsRead(BaseModel):
    app_name: str
    environment: str
    services: dict[str, ServiceStatusRead]
    paths: dict[str, str]
    row_counts: dict[str, int]


class PurgeDatabaseRead(BaseModel):
    status: str
    purged_tables: int
    rows_deleted: int
    database_path: str


class ApiErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    retryable: bool = False


class ApiErrorEnvelope(BaseModel):
    error: ApiErrorDetail
