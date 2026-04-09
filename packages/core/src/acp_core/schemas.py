from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


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
    key: str
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
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    parent_task_id: str | None = None
    board_column_key: str = "backlog"
    tags: list[str] = Field(default_factory=list)


class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    workflow_state: str | None = None
    board_column_id: str | None = None
    blocked_reason: str | None = None
    waiting_for_human: bool | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    board_column_id: str
    parent_task_id: str | None
    title: str
    description: str | None
    workflow_state: str
    priority: str
    tags: list[str]
    blocked_reason: str | None
    waiting_for_human: bool
    created_at: datetime
    updated_at: datetime


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
    payload_json: dict[str, Any]
    created_at: datetime


class DiagnosticsRead(BaseModel):
    app_name: str
    environment: str
    database_path: str
    runtime_home: str
    tmux_available: bool
    git_available: bool
    current_project_count: int
    current_task_count: int


class DashboardRead(BaseModel):
    projects: list[ProjectSummary]
    recent_events: list[EventRecord]
    waiting_count: int
    blocked_count: int
    running_sessions: int

