from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from shlex import quote
from typing import Any, Protocol

from acp_core.enums import OutputMode, Permission, SpecializedMode

PermissionMode = Permission
OutputMode = OutputMode


@dataclass(frozen=True)
class AgentRequest:
    """Normalized ACP-facing request to launch a coding agent."""

    agent_name: str
    task_kind: str
    prompt_file: Path
    execution_root: Path
    model: str | None = None
    permissions: str | None = None
    output: str | None = None
    max_turns: int | None = None
    resume_token: str | None = None
    allowed_tools: list[str] = field(default_factory=list)
    disallowed_tools: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentLaunchPlan:
    """Concrete process launch details ready for runtime orchestration."""

    argv: list[str]
    env: dict[str, str]
    display_command: str
    metadata: dict[str, Any] = field(default_factory=dict)
    resume_hint: str | None = None


@dataclass(frozen=True)
class SessionLaunchInputs:
    """Normalized launch configuration shared by session spawn and follow-up flows."""

    task_kind: str
    agent_name: str | None
    prompt: str | None
    working_directory: Path
    model: str | None = None
    permission_mode: str | None = None
    output_mode: str | None = None
    max_turns: int | None = None
    resume_token: str | None = None
    allowed_tools: list[str] = field(default_factory=list)
    disallowed_tools: list[str] = field(default_factory=list)
    extra_env: dict[str, str] = field(default_factory=dict)
    repository_id: str | None = None
    worktree_id: str | None = None
    session_family_id: str | None = None
    follow_up_of_session_id: str | None = None


@dataclass(frozen=True)
class AgentCapabilities:
    """Capabilities exposed by a concrete coding-agent adapter."""

    supports_model: bool
    native_resume: bool
    permission_modes: frozenset[PermissionMode] = field(default_factory=frozenset)
    output_modes: frozenset[OutputMode] = field(default_factory=frozenset)
    supports_streaming_json: bool = False
    supports_allowed_tools: bool = False
    supports_disallowed_tools: bool = False
    supports_max_turns: bool = False
    specialized_modes: frozenset[SpecializedMode] = field(default_factory=frozenset)


class CodingAgentAdapterProtocol(Protocol):
    name: str

    def capabilities(self) -> AgentCapabilities: ...

    def build_launch_plan(self, request: AgentRequest) -> AgentLaunchPlan: ...


def render_launch_plan_command(plan: AgentLaunchPlan) -> str:
    """Render a shell command string from launch-plan primitives."""

    env_prefix = " ".join(
        f"{key}={_shell_join([value])}" for key, value in plan.env.items()
    )
    command = _shell_join(plan.argv)
    stdin_file = plan.metadata.get("stdin_file")
    if isinstance(stdin_file, str) and stdin_file:
        command = f"{command} < {_shell_join([stdin_file])}"
    if env_prefix:
        return f"export {env_prefix}; {command}"
    return command


def _shell_join(parts: list[str]) -> str:
    return " ".join(quote(part) for part in parts)
