from __future__ import annotations

import pytest

from acp_core.services.agent_selection import resolve_agent_name
from acp_core.settings import Settings


def _settings() -> Settings:
    return Settings()


def test_resolve_agent_name_prefers_explicit_user_value() -> None:
    configured = _settings()
    configured.default_agent = "codex"
    configured.review_agent = "aider"

    resolved = resolve_agent_name("review", "claude-code", configured)

    assert resolved == "claude_code"


def test_resolve_agent_name_uses_flow_default_when_user_value_missing() -> None:
    configured = _settings()
    configured.default_agent = "codex"
    configured.verify_agent = "claude-code"

    resolved = resolve_agent_name("verify", None, configured)

    assert resolved == "claude_code"


def test_resolve_agent_name_falls_back_to_global_default() -> None:
    configured = _settings()
    configured.default_agent = "aider"
    configured.execution_agent = None

    resolved = resolve_agent_name("execute", None, configured)

    assert resolved == "aider"


def test_resolve_agent_name_raises_for_unknown_agent() -> None:
    configured = _settings()

    with pytest.raises(ValueError, match="Unknown agent: ghost-agent"):
        resolve_agent_name("execute", "ghost-agent", configured)
