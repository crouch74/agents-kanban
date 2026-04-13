from __future__ import annotations

from enum import StrEnum


class WorkflowState(StrEnum):
    BACKLOG = "backlog"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskKind(StrEnum):
    KICKOFF = "kickoff"
    EXECUTE = "execute"
    REVIEW = "review"
    VERIFY = "verify"
    RESEARCH = "research"
    DOCS = "docs"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Urgency(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class AgentProfile(StrEnum):
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    VERIFIER = "verifier"
    RESEARCH = "research"
    DOCS = "docs"


class FollowUpType(StrEnum):
    RETRY = "retry"
    REVIEW = "review"
    VERIFY = "verify"
    HANDOFF = "handoff"


class WaitMode(StrEnum):
    CHECK = "check"
    HUMAN = "human"


class Permission(StrEnum):
    DANGER_FULL_ACCESS = "danger-full-access"


class OutputMode(StrEnum):
    JSON = "json"
    STREAM_JSON = "stream-json"


class SpecializedMode(StrEnum):
    REVIEW = "review"
    VERIFY = "verify"


class SessionStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_HUMAN = "waiting_human"
    BLOCKED = "blocked"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SessionRuntimeStatus(StrEnum):
    REQUESTED = "requested"
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    ERROR = "error"


class AuthorType(StrEnum):
    HUMAN = "human"
    AGENT = "agent"
    SYSTEM = "system"


class CheckStatus(StrEnum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class DependencyRelationshipType(StrEnum):
    BLOCKS = "blocks"
    RELATES_TO = "relates_to"


class WorktreeStatus(StrEnum):
    ACTIVE = "active"
    LOCKED = "locked"
    ARCHIVED = "archived"
    PRUNED = "pruned"


class WorktreeRecommendation(StrEnum):
    ARCHIVE = "archive"
    PRUNE = "prune"
    INSPECT = "inspect"


class WorktreeAction(StrEnum):
    CREATE = "create"
    CREATE_OR_UPDATE = "create_or_update"
    APPEND_LINE = "append_line"
    SCAFFOLD = "scaffold"


class AgentRuntimeErrorCode(StrEnum):
    WAITING_FOR_HUMAN = "waiting_for_human"
    WAITING_FOR_RUNTIME = "waiting_for_runtime"
    RUNTIME_ACTIVE = "runtime_active"


class WaitingQuestionStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


def coerce_workflow_state(value: WorkflowState | str | None) -> WorkflowState | None:
    if value is None:
        return None
    if isinstance(value, WorkflowState):
        return value
    try:
        return WorkflowState(value)
    except ValueError as exc:
        raise ValueError(f"Invalid workflow state: {value}") from exc


def coerce_task_kind(value: TaskKind | str | None) -> TaskKind | None:
    if value is None:
        return None
    if isinstance(value, TaskKind):
        return value
    if value == "execution":
        return TaskKind.EXECUTE
    try:
        return TaskKind(value)
    except ValueError as exc:
        raise ValueError(f"Invalid task kind: {value}") from exc


def coerce_task_priority(value: TaskPriority | str | None) -> TaskPriority | None:
    if value is None:
        return None
    if isinstance(value, TaskPriority):
        return value
    try:
        return TaskPriority(value)
    except ValueError as exc:
        raise ValueError(f"Invalid task priority: {value}") from exc


def coerce_urgency(value: Urgency | str | None) -> Urgency | None:
    if value is None:
        return None
    if isinstance(value, Urgency):
        return value
    try:
        return Urgency(value)
    except ValueError as exc:
        raise ValueError(f"Invalid urgency: {value}") from exc


def coerce_agent_profile(value: AgentProfile | str | None) -> AgentProfile | None:
    if value is None:
        return None
    if isinstance(value, AgentProfile):
        return value
    try:
        return AgentProfile(value)
    except ValueError as exc:
        raise ValueError(f"Invalid agent profile: {value}") from exc


def coerce_follow_up_type(value: FollowUpType | str | None) -> FollowUpType | None:
    if value is None:
        return None
    if isinstance(value, FollowUpType):
        return value
    try:
        return FollowUpType(value)
    except ValueError as exc:
        raise ValueError(f"Invalid follow-up type: {value}") from exc


def coerce_permission(value: Permission | str | None) -> Permission | None:
    if value is None:
        return None
    if isinstance(value, Permission):
        return value
    try:
        return Permission(value)
    except ValueError as exc:
        raise ValueError(f"Invalid permission: {value}") from exc


def coerce_output_mode(value: OutputMode | str | None) -> OutputMode | None:
    if value is None:
        return None
    if isinstance(value, OutputMode):
        return value
    try:
        return OutputMode(value)
    except ValueError as exc:
        raise ValueError(f"Invalid output mode: {value}") from exc


def coerce_specialized_mode(value: SpecializedMode | str | None) -> SpecializedMode | None:
    if value is None:
        return None
    if isinstance(value, SpecializedMode):
        return value
    try:
        return SpecializedMode(value)
    except ValueError as exc:
        raise ValueError(f"Invalid specialized mode: {value}") from exc


def coerce_session_status(value: SessionStatus | str | None) -> SessionStatus | None:
    if value is None:
        return None
    if isinstance(value, SessionStatus):
        return value
    try:
        return SessionStatus(value)
    except ValueError as exc:
        raise ValueError(f"Invalid session status: {value}") from exc


def coerce_session_runtime_status(value: SessionRuntimeStatus | str | None) -> SessionRuntimeStatus | None:
    if value is None:
        return None
    if isinstance(value, SessionRuntimeStatus):
        return value
    try:
        return SessionRuntimeStatus(value)
    except ValueError as exc:
        raise ValueError(f"Invalid session runtime status: {value}") from exc


def coerce_author_type(value: AuthorType | str | None) -> AuthorType | None:
    if value is None:
        return None
    if isinstance(value, AuthorType):
        return value
    try:
        return AuthorType(value)
    except ValueError as exc:
        raise ValueError(f"Invalid author type: {value}") from exc


def coerce_check_status(value: CheckStatus | str | None) -> CheckStatus | None:
    if value is None:
        return None
    if isinstance(value, CheckStatus):
        return value
    try:
        return CheckStatus(value)
    except ValueError as exc:
        raise ValueError(f"Invalid check status: {value}") from exc


def coerce_dependency_relationship(value: DependencyRelationshipType | str | None) -> DependencyRelationshipType | None:
    if value is None:
        return None
    if isinstance(value, DependencyRelationshipType):
        return value
    try:
        return DependencyRelationshipType(value)
    except ValueError as exc:
        raise ValueError(f"Invalid dependency relationship: {value}") from exc


def coerce_worktree_status(
    value: WorktreeStatus | str | None,
) -> WorktreeStatus | None:
    if value is None:
        return None
    if isinstance(value, WorktreeStatus):
        return value
    try:
        return WorktreeStatus(value)
    except ValueError as exc:
        raise ValueError(f"Invalid worktree status: {value}") from exc


def coerce_waiting_question_status(
    value: WaitingQuestionStatus | str | None,
) -> WaitingQuestionStatus | None:
    if value is None:
        return None
    if isinstance(value, WaitingQuestionStatus):
        return value
    try:
        return WaitingQuestionStatus(value)
    except ValueError as exc:
        raise ValueError(f"Invalid waiting question status: {value}") from exc
