from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from acp_core.agents import AgentLaunchPlan, AgentRequest
from acp_core.agents.validation import (
    resolve_adapter_and_validate_request,
    validate_launch_plan_shape,
    validate_request_against_capabilities,
)


def cast_any_int() -> Any:
    return 1


def _request(**kwargs: object) -> AgentRequest:
    return AgentRequest(
        agent_name=str(kwargs.pop("agent_name", "claude-code")),
        task_kind=str(kwargs.pop("task_kind", "execute")),
        prompt_file=Path("prompt.md"),
        execution_root=Path("."),
        model=kwargs.pop("model", None),
        permissions=kwargs.pop("permissions", None),
        output=kwargs.pop("output", None),
        max_turns=kwargs.pop("max_turns", None),
        resume_token=kwargs.pop("resume_token", None),
        allowed_tools=list(kwargs.pop("allowed_tools", [])),
        disallowed_tools=list(kwargs.pop("disallowed_tools", [])),
    )


def test_validate_request_rejects_unknown_agent_with_clear_message() -> None:
    with pytest.raises(ValueError) as exc:
        resolve_adapter_and_validate_request("ghost", _request(agent_name="ghost"))

    assert (
        str(exc.value)
        == "Unknown agent 'ghost'. Supported agents: aider, claude_code, codex"
    )


def test_validate_request_rejects_unsupported_permission_mode() -> None:
    adapter = resolve_adapter_and_validate_request("claude-code", _request())
    with pytest.raises(ValueError) as exc:
        validate_request_against_capabilities(
            _request(agent_name="claude-code", permissions="danger-full-access"),
            adapter.capabilities(),
        )

    assert (
        str(exc.value)
        == "Agent 'claude-code' does not support permission_mode='danger-full-access'. Supported values: none"
    )


def test_validate_request_rejects_unsupported_output_mode() -> None:
    adapter = resolve_adapter_and_validate_request("claude-code", _request())
    with pytest.raises(ValueError) as exc:
        validate_request_against_capabilities(
            _request(agent_name="claude-code", output="json"), adapter.capabilities()
        )

    assert (
        str(exc.value)
        == "Agent 'claude-code' does not support output_mode='json'. Supported values: none"
    )


def test_validate_request_rejects_unsupported_allowed_tools() -> None:
    adapter = resolve_adapter_and_validate_request("claude-code", _request())
    with pytest.raises(ValueError) as exc:
        validate_request_against_capabilities(
            _request(agent_name="claude-code", allowed_tools=["bash"]),
            adapter.capabilities(),
        )

    assert str(exc.value) == "Agent 'claude-code' does not support allowed_tools"


def test_validate_request_rejects_unsupported_disallowed_tools() -> None:
    adapter = resolve_adapter_and_validate_request("claude-code", _request())
    with pytest.raises(ValueError) as exc:
        validate_request_against_capabilities(
            _request(agent_name="claude-code", disallowed_tools=["python"]),
            adapter.capabilities(),
        )

    assert str(exc.value) == "Agent 'claude-code' does not support disallowed_tools"


def test_validate_request_rejects_unsupported_max_turns() -> None:
    adapter = resolve_adapter_and_validate_request("claude-code", _request())
    with pytest.raises(ValueError) as exc:
        validate_request_against_capabilities(
            _request(agent_name="claude-code", max_turns=2), adapter.capabilities()
        )

    assert str(exc.value) == "Agent 'claude-code' does not support max_turns"


def test_validate_request_rejects_unsupported_specialized_mode() -> None:
    adapter = resolve_adapter_and_validate_request("claude-code", _request())
    with pytest.raises(ValueError) as exc:
        validate_request_against_capabilities(
            _request(agent_name="claude-code", task_kind="review"),
            adapter.capabilities(),
        )

    assert (
        str(exc.value)
        == "Agent 'claude-code' does not support task_kind='review'. Specialized modes: none"
    )


def test_validate_launch_plan_shape_rejects_invalid_argv() -> None:
    with pytest.raises(ValueError) as exc:
        validate_launch_plan_shape(
            agent_name="codex",
            plan=AgentLaunchPlan(argv=[], env={}, display_command="codex exec -"),
        )

    assert (
        str(exc.value)
        == "Agent 'codex' returned invalid launch plan: argv must be a non-empty list[str]"
    )


def test_validate_launch_plan_shape_rejects_invalid_env() -> None:
    with pytest.raises(ValueError) as exc:
        validate_launch_plan_shape(
            agent_name="codex",
            plan=AgentLaunchPlan(
                argv=["codex"],
                env={"ACP": "ok", **{"BAD": cast_any_int()}},
                display_command="codex exec -",
            ),
        )

    assert (
        str(exc.value)
        == "Agent 'codex' returned invalid launch plan: env must be dict[str, str]"
    )


def test_validate_launch_plan_shape_rejects_empty_display_command() -> None:
    with pytest.raises(ValueError) as exc:
        validate_launch_plan_shape(
            agent_name="codex",
            plan=AgentLaunchPlan(argv=["codex"], env={}, display_command=""),
        )

    assert (
        str(exc.value)
        == "Agent 'codex' returned invalid launch plan: display_command must be non-empty"
    )
