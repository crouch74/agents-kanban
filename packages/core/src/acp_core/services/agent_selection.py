from __future__ import annotations

from acp_core.agents import AgentRegistry
from acp_core.settings import Settings

_FLOW_DEFAULT_SETTING_BY_TASK_KIND: dict[str, str] = {
    "kickoff": "kickoff_agent",
    "execute": "execution_agent",
    "review": "review_agent",
    "verify": "verify_agent",
    "research": "research_agent",
    "docs": "docs_agent",
}


def resolve_agent_name(
    task_kind: str,
    requested_agent_name: str | None,
    settings: Settings,
    *,
    registry: AgentRegistry | None = None,
) -> str:
    resolved_registry = registry or AgentRegistry.default()
    flow_setting_name = _FLOW_DEFAULT_SETTING_BY_TASK_KIND.get(task_kind)
    flow_specific_default = (
        getattr(settings, flow_setting_name, None) if flow_setting_name else None
    )
    effective_default = flow_specific_default or settings.default_agent
    selected_name = requested_agent_name or effective_default
    canonical_name = resolved_registry.canonical_key(selected_name)
    try:
        resolved_registry.resolve(canonical_name)
    except ValueError as exc:
        raise ValueError(f"Unknown agent: {selected_name}") from exc
    return canonical_name
