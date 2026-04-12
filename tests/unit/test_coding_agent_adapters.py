from __future__ import annotations

from pathlib import Path

from acp_core.agents import AgentRequest, render_launch_plan_command, resolve_coding_agent_adapter
from acp_core.settings import settings


def test_codex_adapter_builds_launch_plan_with_prompt_redirection(tmp_path: Path) -> None:
    prompt_file = tmp_path / ".acp" / "bootstrap-prompt.md"
    prompt_file.parent.mkdir(parents=True)
    prompt_file.write_text("hello", encoding="utf-8")

    adapter = resolve_coding_agent_adapter("codex")
    plan = adapter.build_launch_plan(
        AgentRequest(
            agent_name="codex",
            task_kind="kickoff",
            prompt_file=prompt_file,
            execution_root=tmp_path,
            model="gpt-5",
            permissions="danger-full-access",
            output="json",
        )
    )

    command = render_launch_plan_command(plan)
    assert "codex --dangerously-bypass-approvals-and-sandbox --model gpt-5 --output-format json exec -" in command
    assert f"< {prompt_file}" in command
    assert "ACP_RUNTIME_HOME=" in command


def test_codex_adapter_uses_deprecated_template_bridge_when_overridden(tmp_path: Path) -> None:
    prompt_file = tmp_path / ".acp" / "bootstrap-prompt.md"
    prompt_file.parent.mkdir(parents=True)
    prompt_file.write_text("hello", encoding="utf-8")

    original = settings.bootstrap_agent_command_template
    settings.bootstrap_agent_command_template = "echo legacy {prompt_file}"
    try:
        adapter = resolve_coding_agent_adapter("codex")
        plan = adapter.build_launch_plan(
            AgentRequest(
                agent_name="codex",
                task_kind="kickoff",
                prompt_file=prompt_file,
                execution_root=tmp_path,
            )
        )
    finally:
        settings.bootstrap_agent_command_template = original

    assert plan.argv[:2] == ["bash", "-lc"]
    assert plan.metadata["legacy_template_bridge"] is True
