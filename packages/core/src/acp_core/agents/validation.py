from __future__ import annotations

from acp_core.agents.adapters import AgentRegistry, resolve_coding_agent_adapter
from acp_core.agents.types import (
    AgentCapabilities,
    AgentLaunchPlan,
    AgentRequest,
    SpecializedMode,
)


def validate_request_against_capabilities(
    request: AgentRequest, capabilities: AgentCapabilities
) -> None:
    if request.model and not capabilities.supports_model:
        raise ValueError(
            f"Agent '{request.agent_name}' does not support model selection"
        )

    if request.permissions and request.permissions not in capabilities.permission_modes:
        supported = ", ".join(sorted(capabilities.permission_modes)) or "none"
        raise ValueError(
            f"Agent '{request.agent_name}' does not support permission_mode='{request.permissions}'. "
            f"Supported values: {supported}"
        )

    if request.output and request.output not in capabilities.output_modes:
        supported = ", ".join(sorted(capabilities.output_modes)) or "none"
        raise ValueError(
            f"Agent '{request.agent_name}' does not support output_mode='{request.output}'. Supported values: {supported}"
        )

    if request.resume_token and not capabilities.native_resume:
        raise ValueError(f"Agent '{request.agent_name}' does not support resume_token")

    if request.allowed_tools and not capabilities.supports_allowed_tools:
        raise ValueError(f"Agent '{request.agent_name}' does not support allowed_tools")

    if request.disallowed_tools and not capabilities.supports_disallowed_tools:
        raise ValueError(
            f"Agent '{request.agent_name}' does not support disallowed_tools"
        )

    if request.max_turns is not None and not capabilities.supports_max_turns:
        raise ValueError(f"Agent '{request.agent_name}' does not support max_turns")

    if (
        request.task_kind in {SpecializedMode.REVIEW.value, SpecializedMode.VERIFY.value}
        and request.task_kind not in capabilities.specialized_modes
    ):
        supported = ", ".join(sorted(capabilities.specialized_modes)) or "none"
        raise ValueError(
            f"Agent '{request.agent_name}' does not support task_kind='{request.task_kind}'. "
            f"Specialized modes: {supported}"
        )


def validate_launch_plan_shape(*, agent_name: str, plan: AgentLaunchPlan) -> None:
    if (
        not isinstance(plan.argv, list)
        or not plan.argv
        or not all(isinstance(value, str) and value for value in plan.argv)
    ):
        raise ValueError(
            f"Agent '{agent_name}' returned invalid launch plan: argv must be a non-empty list[str]"
        )
    if not isinstance(plan.env, dict) or not all(
        isinstance(key, str) and key and isinstance(value, str)
        for key, value in plan.env.items()
    ):
        raise ValueError(
            f"Agent '{agent_name}' returned invalid launch plan: env must be dict[str, str]"
        )
    if not isinstance(plan.display_command, str) or not plan.display_command.strip():
        raise ValueError(
            f"Agent '{agent_name}' returned invalid launch plan: display_command must be non-empty"
        )


def resolve_adapter_and_validate_request(
    agent_name: str | None,
    request: AgentRequest,
    *,
    registry: AgentRegistry | None = None,
    default_agent: str | None = None,
):
    try:
        adapter = resolve_coding_agent_adapter(
            agent_name,
            registry=registry,
            default_agent=default_agent,
        )
    except ValueError as exc:
        message = str(exc)
        if message.startswith("Unsupported bootstrap agent"):
            raise ValueError(
                message.replace("Unsupported bootstrap agent", "Unknown agent", 1)
            ) from exc
        raise

    validate_request_against_capabilities(request, adapter.capabilities())
    return adapter
