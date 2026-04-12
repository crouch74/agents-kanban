from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from shlex import quote
from typing import Any, Protocol


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
class AgentCapabilities:
    """Capabilities exposed by a concrete coding-agent adapter."""

    supports_model: bool
    supports_permissions: bool
    supports_output: bool
    supports_resume_hint: bool = False


class CodingAgentAdapterProtocol(Protocol):
    name: str

    def capabilities(self) -> AgentCapabilities: ...

    def build_launch_plan(self, request: AgentRequest) -> AgentLaunchPlan: ...


def render_launch_plan_command(plan: AgentLaunchPlan) -> str:
    """Render a shell command string from launch-plan primitives."""

    env_prefix = " ".join(f"{key}={_shell_join([value])}" for key, value in plan.env.items())
    command = _shell_join(plan.argv)
    stdin_file = plan.metadata.get("stdin_file")
    if isinstance(stdin_file, str) and stdin_file:
        command = f"{command} < {_shell_join([stdin_file])}"
    if env_prefix:
        return f"export {env_prefix}; {command}"
    return command


def _shell_join(parts: list[str]) -> str:
    return " ".join(quote(part) for part in parts)
