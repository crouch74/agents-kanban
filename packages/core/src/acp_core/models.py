from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    settings_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    diagnostics_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    board: Mapped["Board | None"] = relationship(back_populates="project", uselist=False)
    tasks: Mapped[list["Task"]] = relationship(back_populates="project")
    repositories: Mapped[list["Repository"]] = relationship(back_populates="project")


class Repository(TimestampMixin, Base):
    __tablename__ = "repositories"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    local_path: Mapped[str] = mapped_column(Text, nullable=False)
    default_branch: Mapped[str | None] = mapped_column(String(255))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    project: Mapped[Project] = relationship(back_populates="repositories")


class Board(TimestampMixin, Base):
    __tablename__ = "boards"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="Main Board")

    project: Mapped[Project] = relationship(back_populates="board")
    columns: Mapped[list["BoardColumn"]] = relationship(
        back_populates="board",
        order_by="BoardColumn.position",
        cascade="all, delete-orphan",
    )


class BoardColumn(TimestampMixin, Base):
    __tablename__ = "board_columns"

    board_id: Mapped[str] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    wip_limit: Mapped[int | None] = mapped_column(Integer)
    entry_policy: Mapped[str | None] = mapped_column(Text)
    exit_policy: Mapped[str | None] = mapped_column(Text)
    done_policy: Mapped[str | None] = mapped_column(Text)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    board: Mapped[Board] = relationship(back_populates="columns")
    tasks: Mapped[list["Task"]] = relationship(back_populates="board_column")


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    board_column_id: Mapped[str] = mapped_column(ForeignKey("board_columns.id", ondelete="RESTRICT"))
    parent_task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    workflow_state: Mapped[str] = mapped_column(String(64), nullable=False)
    priority: Mapped[str] = mapped_column(String(32), default="medium", nullable=False)
    estimate: Mapped[int | None] = mapped_column(Integer)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    blocked_reason: Mapped[str | None] = mapped_column(Text)
    waiting_for_human: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acceptance_criteria: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    project: Mapped[Project] = relationship(back_populates="tasks")
    board_column: Mapped[BoardColumn] = relationship(back_populates="tasks")
    parent_task: Mapped["Task | None"] = relationship(remote_side="Task.id")


class TaskDependency(TimestampMixin, Base):
    __tablename__ = "task_dependencies"

    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    depends_on_task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    relationship_type: Mapped[str] = mapped_column(String(64), default="blocks", nullable=False)


class TaskComment(TimestampMixin, Base):
    __tablename__ = "task_comments"

    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    author_type: Mapped[str] = mapped_column(String(32), nullable=False)
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class TaskCheck(TimestampMixin, Base):
    __tablename__ = "task_checks"

    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    check_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class TaskArtifact(TimestampMixin, Base):
    __tablename__ = "task_artifacts"

    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    uri: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class AgentSession(TimestampMixin, Base):
    __tablename__ = "agent_sessions"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    repository_id: Mapped[str | None] = mapped_column(ForeignKey("repositories.id"))
    worktree_id: Mapped[str | None] = mapped_column(ForeignKey("worktrees.id"))
    profile: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="queued")
    runtime_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class AgentRun(TimestampMixin, Base):
    __tablename__ = "agent_runs"

    session_id: Mapped[str] = mapped_column(ForeignKey("agent_sessions.id", ondelete="CASCADE"))
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)


class SessionMessage(TimestampMixin, Base):
    __tablename__ = "session_messages"

    session_id: Mapped[str] = mapped_column(ForeignKey("agent_sessions.id", ondelete="CASCADE"))
    message_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class WaitingQuestion(TimestampMixin, Base):
    __tablename__ = "waiting_questions"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    session_id: Mapped[str | None] = mapped_column(ForeignKey("agent_sessions.id"))
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="open")
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    blocked_reason: Mapped[str | None] = mapped_column(Text)
    urgency: Mapped[str | None] = mapped_column(String(32))
    options_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)


class HumanReply(TimestampMixin, Base):
    __tablename__ = "human_replies"

    question_id: Mapped[str] = mapped_column(ForeignKey("waiting_questions.id", ondelete="CASCADE"))
    responder_name: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class Worktree(TimestampMixin, Base):
    __tablename__ = "worktrees"

    repository_id: Mapped[str] = mapped_column(ForeignKey("repositories.id", ondelete="CASCADE"))
    task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id", ondelete="SET NULL"))
    session_id: Mapped[str | None] = mapped_column(ForeignKey("agent_sessions.id", ondelete="SET NULL"))
    branch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="requested")
    lock_reason: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)


class Event(TimestampMixin, Base):
    __tablename__ = "events"

    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(255))
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

