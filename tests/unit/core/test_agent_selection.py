from __future__ import annotations

import pytest

from acp_core.agents import AgentRegistry
from acp_core.services.agent_selection import resolve_agent_name
from acp_core.settings import settings


def test_resolve_agent_name_uses_explicit_request() -> None:
    original_default = settings.default_agent
    try:
        settings.default_agent = "codex"
        resolved = resolve_agent_name(
            task_kind="execution",
            requested_agent_name="aider",
            settings=settings,
            agent_registry=AgentRegistry.default(),
        )
        assert resolved == "aider"
    finally:
        settings.default_agent = original_default


def test_resolve_agent_name_uses_flow_default_when_request_missing() -> None:
    original_execution_agent = settings.execution_agent
    original_default_agent = settings.default_agent
    try:
        settings.execution_agent = "claude-code"
        settings.default_agent = "codex"
        resolved = resolve_agent_name(
            task_kind="execution",
            requested_agent_name=None,
            settings=settings,
            agent_registry=AgentRegistry.default(),
        )
        assert resolved == "claude_code"
    finally:
        settings.execution_agent = original_execution_agent
        settings.default_agent = original_default_agent


def test_resolve_agent_name_falls_back_to_default_when_no_flow_default() -> None:
    original_execution_agent = settings.execution_agent
    original_default_agent = settings.default_agent
    try:
        settings.execution_agent = None
        settings.default_agent = "codex"
        resolved = resolve_agent_name(
            task_kind="execution",
            requested_agent_name=None,
            settings=settings,
            agent_registry=AgentRegistry.default(),
        )
        assert resolved == "codex"
    finally:
        settings.execution_agent = original_execution_agent
        settings.default_agent = original_default_agent


@pytest.mark.parametrize(
    "requested_agent",
    ["unknown-agent", "ghost", "codexx"],
)
def test_resolve_agent_name_rejects_unknown_agent(requested_agent: str) -> None:
    with pytest.raises(ValueError, match=f"^Unknown agent: {requested_agent}$"):
        resolve_agent_name(
            task_kind="execution",
            requested_agent_name=requested_agent,
            settings=settings,
            agent_registry=AgentRegistry.default(),
        )
