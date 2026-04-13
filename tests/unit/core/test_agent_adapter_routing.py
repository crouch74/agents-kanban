from __future__ import annotations

from pathlib import Path

import pytest

from acp_core.agents import AgentCapabilities, AgentRequest, resolve_coding_agent_adapter
from acp_core.agents.validation import (
    resolve_adapter_and_validate_request,
    validate_request_against_capabilities,
)


def _request(agent_name: str, **overrides: object) -> AgentRequest:
    return AgentRequest(
        agent_name=agent_name,
        task_kind=str(overrides.pop("task_kind", "execute")),
        prompt_file=Path("prompt.md"),
        execution_root=Path("."),
        model=overrides.pop("model", None),
        permissions=overrides.pop("permissions", None),
        output=overrides.pop("output", None),
        max_turns=overrides.pop("max_turns", None),
        resume_token=overrides.pop("resume_token", None),
        allowed_tools=list(overrides.pop("allowed_tools", [])),
        disallowed_tools=list(overrides.pop("disallowed_tools", [])),
    )


@pytest.mark.parametrize(
    ("agent_name", "expected_adapter_name"),
    [
        ("codex", "codex"),
        ("claude_code", "claude-code"),
        ("aider", "aider"),
    ],
)
def test_registry_resolution_returns_expected_adapter(
    agent_name: str, expected_adapter_name: str
) -> None:
    adapter = resolve_coding_agent_adapter(agent_name)

    assert adapter.name == expected_adapter_name


def test_registry_resolution_raises_for_unknown_agent() -> None:
    with pytest.raises(ValueError) as exc:
        resolve_adapter_and_validate_request("unknown", _request("unknown"))

    assert (
        str(exc.value)
        == "Unknown agent 'unknown'. Supported agents: aider, claude_code, codex"
    )


def test_launch_plan_generation_codex_asserts_argv_env_metadata(tmp_path: Path) -> None:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("hi", encoding="utf-8")

    adapter = resolve_coding_agent_adapter("codex")
    plan = adapter.build_launch_plan(
        _request(
            "codex",
            task_kind="kickoff",
            model="gpt-5",
            permissions="danger-full-access",
            output="json",
        )
    )

    assert plan.argv[:4] == ["codex", "--dangerously-bypass-approvals-and-sandbox", "--model", "gpt-5"]
    assert plan.argv[-2:] == ["exec", "-"]
    assert "ACP_RUNTIME_HOME" in plan.env
    assert plan.metadata["agent"] == "codex"
    assert plan.metadata["task_kind"] == "kickoff"


def test_launch_plan_generation_claude_code_asserts_argv_env_metadata(tmp_path: Path) -> None:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("hi", encoding="utf-8")

    adapter = resolve_coding_agent_adapter("claude_code")
    plan = adapter.build_launch_plan(
        AgentRequest(
            agent_name="claude_code",
            task_kind="execute",
            prompt_file=prompt_file,
            execution_root=tmp_path,
            model="sonnet",
        )
    )

    assert plan.argv == ["claude", "--print", "--model", "sonnet"]
    assert "ACP_RUNTIME_HOME" in plan.env
    assert plan.metadata == {
        "agent": "claude-code",
        "task_kind": "execute",
        "stdin_file": str(prompt_file),
    }


def test_launch_plan_generation_aider_asserts_argv_env_metadata(tmp_path: Path) -> None:
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("hi", encoding="utf-8")

    adapter = resolve_coding_agent_adapter("aider")
    plan = adapter.build_launch_plan(
        AgentRequest(
            agent_name="aider",
            task_kind="execute",
            prompt_file=prompt_file,
            execution_root=tmp_path,
            model="gpt-4.1",
        )
    )

    assert plan.argv == ["aider", "--message-file", str(prompt_file), "--model", "gpt-4.1"]
    assert "ACP_RUNTIME_HOME" in plan.env
    assert plan.metadata == {"agent": "aider", "task_kind": "execute"}


@pytest.mark.parametrize(
    "agent_request",
    [
        _request("claude-code", output="json"),
        _request("claude-code", allowed_tools=["bash"]),
        _request("claude-code", max_turns=3),
    ],
)
def test_capability_gating_rejects_unsupported_json_tools_and_max_turns(
    agent_request: AgentRequest,
) -> None:
    adapter = resolve_coding_agent_adapter("claude-code")

    with pytest.raises(ValueError):
        validate_request_against_capabilities(agent_request, adapter.capabilities())


def test_capability_gating_rejects_resume_when_adapter_lacks_native_resume() -> None:
    capabilities = AgentCapabilities(supports_model=True, native_resume=False)

    with pytest.raises(ValueError):
        validate_request_against_capabilities(
            _request("custom", resume_token="resume-1"),
            capabilities,
        )
